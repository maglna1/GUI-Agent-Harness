# ScreenSpot-Pro Benchmark

ScreenSpot-Pro 是 GUI 元素定位基准测试，覆盖 1581 个专业软件样本（5 大子集、23 个应用）。

## 结果总览

| 模型 | 进度 | 正确 | 错误 | WF | 准确率 | Pipeline | 状态 |
|------|------|------|------|----|--------|----------|------|
| **GPT-5.5** | 1581/1581 | 1390 | 191 | 0 | **87.9%** | legacy (fill/legacy, 8 rounds) | ✅ 完成 |
| Claude 4.7 | 338/1581 | 267 | 71 | 1243 | 79.0%* | legacy | ⏹ 额度耗尽 |
| Claude 4.7 (stratified) | 78/1581 | 62 | 16 | 0 | 79.5% | - | ✅ 完成 |
| Claude 4.8 (stratified) | 78/1581 | - | - | - | - | - | ✅ 完成 |

*Claude 4.7 完整跑被额度耗尽中断，1243 个 WF 是额度错误导致。

## GPT-5.5 按子集

| 子集 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| Office | 230 | 221 | 96.1% |
| Development | 289 | 259 | 89.6% |
| Operating Systems | 196 | 177 | 90.3% |
| CAD | 306 | 259 | 84.6% |
| Creative | 306 | 259 | 84.6% |
| Scientific | 254 | 215 | 84.6% |
| **合计** | **1581** | **1390** | **87.9%** |

## GPT-5.5 按应用（Top/Bottom 5）

| 应用 | 子集 | 样本 | 准确率 |
|------|------|------|--------|
| EViews | Scientific | 50 | 98.0% |
| Word | Office | 84 | 97.6% |
| VMware | Development | 41 | 97.6% |
| Excel | Office | 64 | 96.9% |
| macOS | OS | 65 | 95.4% |
| ... | ... | ... | ... |
| Origin | Scientific | 62 | 58.1% |
| AutoCAD | CAD | 34 | 70.6% |
| FL Studio | Creative | 57 | 75.4% |
| Quartus | CAD | 45 | 75.6% |
| Thunderbird | — | — | 77.8% |

## Tracked Code

- `run_screenspot_pro.py` — 运行 ScreenSpot-style annotation 文件
- `sync_full_final.py` — 合并多轮结果到统一目录
- `report_full_final.py` — 输出紧凑进度/最终报告
- `prepare_screenspot_versions.py` / `start_screenspot_versions.py` / `report_screenspot_versions.py` — ScreenSpot v1/v2 工具链
- `prepare_gui_grounding_datasets.py` / `start_gui_grounding_datasets.py` / `report_gui_grounding_datasets.py` — UI-Vision / MMBench-GUI L2 工具链
- `configs/` — 管线配置文件 (`main_baseline.yaml` = legacy, `known_good.yaml` = new)

## Local Data

以下被 git 忽略：
- `benchmarks/screenspot_pro/data*/`
- `runs/`
- JSONL 输出和错误事件文件

## Resume Notes

所有 detached starter 使用 shard JSONL + `--skip-existing`，可从同一 run 目录 resume 不重复。
