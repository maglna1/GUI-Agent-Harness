# MMBench-GUI-L2 — GUI 元素定位 (多平台)

MMBench-GUI-L2 是 MMBench 系列的 GUI 元素定位基准测试，覆盖 6 平台（Android/iOS/Linux/macOS/Web/Windows）。

- 模型: **GPT-5.5** (openai-codex)
- 总样本数: **3594 / 3594** (100% 完成) ✅
- Pipeline: iterative_zoom (8 rounds), legacy (fill/legacy via main_baseline.yaml)
- 总准确率: **91.52%** (3271 correct / 303 wrong / 20 WF)

---

## 运行结果

| 模型 | 进度 | 正确 | 错误 | WF | 准确率 | 状态 |
|------|------|------|------|----|--------|------|
| **GPT-5.5** | 3594/3594 | 3271 | 303 | 20 | **91.52%** | ✅ 完成 |

## 平台分布 (GPT-5.5)

| 平台 | 样本 | 正确 | 错误 | WF | 准确率 |
|------|------|------|------|----|--------|
| **Android** | 711 | 682 | 29 | 0 | 95.9% |
| **iOS** | 644 | 612 | 32 | 0 | 95.0% |
| **Web** | 618 | 569 | 46 | 3 | 92.5% |
| **macOS** | 691 | 610 | 73 | 8 | 89.3% |
| **Windows** | 543 | 474 | 60 | 9 | 88.8% |
| **Linux** | 387 | 324 | 63 | 0 | 83.7% |
| **合计** | **3594** | **3271** | **303** | **20** | **91.52%** |

> 20 个 WF 全部是 `NoVerifiedTarget` — 迭代缩放 8 轮 + 重试后模型仍无法定位的硬骨头（非网络问题）。

## 运行信息
- 运行目录: `runs/gui_grounding/gui_grounding_mmbench_gui_l2_full_20260602_2040/`
- 原始 shard: `runs/gui_grounding/gui_grounding_mmbench_gui_l2_full_20260602_2040/mmbench_gui_l2/shards/shard_*.jsonl`
- 结果文件: `benchmarks/mmbench_gui_l2/results/gpt_5_5/`

## 文件
- `results/gpt_5_5/full_report.md` — 汇总报告
- `results/gpt_5_5/full_summary.json` — 聚合统计
- `results/gpt_5_5/results.jsonl` — 3594 条逐样本记录
