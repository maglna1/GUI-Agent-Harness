# GUI-Agent-Harness 核心原理

> 本文档从架构层面概述 GUI-Agent-Harness 的核心工作原理。详细的踩坑经验与具体规则见 [`core.md`](core.md)。

## 一、项目定位

GUI-Agent-Harness 是一个 CLI 工具，把任意 LLM 变成桌面 GUI 自动化代理。给它一句自然语言任务，它就能自主地在桌面上完成**截图、点击、输入、验证**的循环，直到任务结束。

底层基于 [OpenProgram](https://github.com/Fzkuji/OpenProgram)——负责 provider 抽象、上下文管理、结构化 LLM 调用；Harness 在此基础上叠加**GUI 感知**（YOLO 检测、OCR、模板匹配）与**动作执行**（鼠标、键盘、剪贴板）。

---

## 二、Grounding Pipeline：迭代缩放定位（最核心创新）

给定自然语言描述（如"点击 GitHub 按钮"）与屏幕截图，输出精确点击坐标 `(x, y)`：

```
截图 + 目标描述
        │
        ▼
Phase 1：检测层         GPA-GUI-Detector（YOLO）+ OCR → 识别所有可见 UI 元素
        │
        ▼
Phase 2：候选匹配        模板匹配视觉记忆（已存储的 UI 组件）
        │
        ▼
Phase 3：LLM 粗定位     VLM 看整屏 + 组件列表 → 锁定目标区域
        │
        ▼
Phase 4：迭代缩放        裁剪 → 放大 → 重新定位 → 验证，重复最多 8 轮
        │
        ▼
    精确 (x, y)
```

### 关键设计决策

| 决策 | 解决的问题 |
|------|-----------|
| **多源感知**（YOLO + OCR + 模板记忆） | 让 VLM 在已标注的"组件世界"里推理，而不是直接看裸像素 |
| **渐进式细化** | 不一次性预测坐标，反复"裁剪 + 放大"，每轮给 VLM 更高分辨率的局部视图 |
| **验证器把关** | 每轮缩放后独立验证点是否落在目标上，假阳性在变成错误点击之前就被拒绝 |
| **可缓存的 prompt 布局** | 固定规则提到可缓存前缀，每轮只变化任务、组件列表、图像 → 最大化 8 轮 pipeline 的 prompt cache 命中率 |
| **可配置的缩放策略** | `preserve` 模式保留大图原始分辨率（小目标不下采样丢失信息）；`fill` 模式匹配旧行为用于对比 |

---

## 三、Agent Loop：4 阶段闭环

完整任务自动化（不仅限于 grounding）跑的是 4 阶段循环：

```
Observe（Python）──► Verify（LLM）──► Plan（LLM）──► Dispatch（Python）
       ▲                                                  │
       └──────────────── 下一轮 Observe ◄─────────────────┘
```

- **Observe（Python）** —— 截图 + YOLO 检测 + OCR + 模板匹配，识别当前可见 UI 状态
- **Verify（LLM）** —— 检查上一次动作是否成功
- **Plan（LLM）** —— 看截图、检测到的组件、验证结果，选择一个动作
- **Dispatch（Python）** —— 执行动作；若是点击则委托给上面的迭代缩放 pipeline

所有阶段都是 `@agentic_function` 调用，步骤之间通过结构化输出传递反馈。

---

## 四、视觉记忆（Visual Memory）

UI 组件首次出现时由 VLM 标注并存为模板；再次出现时用模板匹配代替重新检测：

- 提速约 **5 倍**
- 减少约 **60 倍 token**
- 状态用组件集合的 **Jaccard 相似度** 匹配
- 组件连续 **15 次未命中** 自动遗忘

> 更详细的记忆规则（保存时机、最小尺寸、去重、跨窗口匹配陷阱等）见 [`core.md`](core.md)。

---

## 五、架构特点

### 平台无关

- macOS / Windows / Linux 都能跑
- 支持本地桌面，也支持远程 VM（如 OSWorld 评测环境）

### Provider 无关

底层用 OpenProgram 抽象层，OpenAI / Anthropic / MiniMax 等任意 LLM 都可接入。

### Prompt 缓存优化

固定规则提到可缓存前缀，每轮 pipeline 只变化任务、组件列表、图像 → 最大化 prompt cache 命中率（避免 8 轮里 7 次重新解析长 system prompt）。

### 坐标系统

使用与缩放无关的 `ImageContext`，避免裁剪 bug（详见 [`core.md`](core.md)）。

---

## 六、性能指标

| 基准 | 样本数 | 准确率 |
|---|---|---|
| MMBench-GUI-L2（全量） | 3,594 | **91.52%** |
| MMBench-GUI-L2（basic） | 1,787 | 94.89% |
| MMBench-GUI-L2（advanced） | 1,807 | 88.17% |
| ScreenSpot Pro（全量） | 1,581 | **87.9%** |
| ScreenSpot v2 | 1,272 | **96.78%** |
| UI-Vision（全量） | 5,479 | **68.64%** |
| OSWorld Chrome | 46 | 93.5% |
| OSWorld Multi-Apps | 91 | 79.8% |

---

## 七、一句话总结

> 把屏幕截图先经 **YOLO / OCR / 模板匹配** 变成结构化的"组件列表"，再让 LLM 在这个已标注的世界里做规划；对需要点击的目标，采用**"裁剪 — 放大 — 验证"**的迭代缩放 pipeline 精确定位；最后所有阶段通过 `@agentic_function` 串成 **observe → verify → plan → dispatch** 的闭环。
