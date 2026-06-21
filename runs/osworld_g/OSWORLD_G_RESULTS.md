# OSWorld-G 全量结果(GPT-5.5 × iterative-zoom)

数据集:[OSWorld-G](https://github.com/xlang-ai/OSWorld-G)(NeurIPS 2025 Spotlight),564 样本,32 种 UI 元素类型。
方法:迭代缩放定位器(`configs/sspro_stack_zoom.yaml`,control 惯例,与 ScreenSpot-Pro 同配置)。
判分:bbox 用 point-in-bbox;polygon 用 point-in-polygon 精确判定;refusal 见下。
状态:564/564 完成,0 error。

## 分类型成绩

| 类型 | 完成 | 正确率 | 说明 |
|---|---|---|---|
| bbox | 424/470 | **90.2%** | 标准矩形框 |
| polygon | 39/40 | **97.5%** | 不规则区域,point-in-polygon 精判 |
| refusal | 0/54 | **0.0%** | 不可完成任务,正确答案=拒绝点击(见局限) |
| **可定位子集** | **463/510** | **90.8%** | 排除 refusal,衡量纯定位能力 |
| **全量** | **463/564** | **82.1%** | 含 refusal |

## 与公开方法对比(OSWorld-G,全量 564)

| 方法 | OSWorld-G |
|---|---|
| Qwen2.5-VL-72B | 约 60% |
| Jedi-7B | ≈54.1% |
| UI-TARS-1.5 | ≈64.2% |
| **本方法(GPT-5.5 × zoom)可定位子集** | **90.8%** |
| **本方法(GPT-5.5 × zoom)全量** | **82.1%** |

即便算上必然失分的 refusal,全量 82.1% 仍显著高于公开 SOTA;纯定位能力(可定位子集 90.8%)领先幅度与我们在 ScreenSpot-Pro(88.7%)、UI-Vision(74.4%)上的表现一致。

## refusal 局限说明

OSWorld-G 含 54 个"不可完成"样本,正确行为是**拒绝点击**。本方法采用 `keep_best` 兜底策略,
任何情况下都会输出一个点击坐标,**没有拒绝机制**,因此这 54 题必然全错(0/54)。

这是当前管线的已知设计取舍:`keep_best` 在可定位任务上提升召回(永不放弃),代价是无法处理
"应当拒绝"的场景。为避免无意义的算力浪费,runner 对 refusal 题直接短路记错
(`grounding_type=refusal_not_supported`),不调用定位器——评分与跑完整管线完全等价。

若未来需要拒绝能力,可引入一个"目标是否存在"的前置判别(置信度门控),代价是可能损失部分
可定位任务的召回。本轮目标是验证纯定位能力,故保持现状、如实报告两个口径。
