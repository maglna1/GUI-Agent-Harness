# GPT-5.5 — ScreenSpot Pro Full

运行目录: `runs/screenspot_pro/iter_zoom_recrop_full_final_20260602/`
Provider: `openai-codex` / Model: `gpt-5.5`
Pipeline: iterative_zoom (8 rounds), legacy (fill/legacy)
状态: ✅ 已完成

## 最终结果

| 指标 | 数值 |
|------|------|
| 总样本 | 1581 |
| 正确 | 1390 |
| 错误 | 191 |
| Wrong Format | 0 |
| **准确率** | **87.9%** |

## 按子集

| 子集 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| Development | 289 | 259/289 | 89.6% |
| Creative | 306 | 259/306 | 84.6% |
| CAD | 306 | 259/306 | 84.6% |
| Scientific | 254 | 215/254 | 84.6% |
| Office | 230 | 221/230 | 96.1% |
| Operating Systems | 196 | 177/196 | 90.3% |

## 按应用

### Development

| 应用 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| Android Studio | 80 | 72/80 | 90.0% |
| PyCharm | 78 | 63/78 | 80.8% |
| VS Code | 55 | 52/55 | 94.5% |
| VMware | 41 | 40/41 | 97.6% |
| Unreal Engine | 35 | 32/35 | 91.4% |

### Creative

| 应用 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| Photoshop | 51 | 43/51 | 84.3% |
| Blender | 71 | 65/71 | 91.5% |
| Premiere | 52 | 46/52 | 88.5% |
| DaVinci Resolve | 44 | 36/44 | 81.8% |
| Illustrator | 31 | 26/31 | 83.9% |
| FL Studio | 57 | 43/57 | 75.4% |

### CAD

| 应用 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| AutoCAD | 34 | 24/34 | 70.6% |
| SolidWorks | 77 | 72/77 | 93.5% |
| Inventor | 70 | 59/70 | 84.3% |
| Quartus | 45 | 34/45 | 75.6% |
| Vivado | 80 | 70/80 | 87.5% |

### Scientific

| 应用 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| MATLAB | 93 | 84/93 | 90.3% |
| Origin | 62 | 36/62 | 58.1% |
| EViews | 50 | 49/50 | 98.0% |
| Stata | 49 | 46/49 | 93.9% |

### Office

| 应用 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| PowerPoint | 82 | 77/82 | 93.9% |
| Excel | 64 | 62/64 | 96.9% |
| Word | 84 | 82/84 | 97.6% |

### Operating Systems

| 应用 | 样本 | 正确 | 准确率 |
|------|------|------|--------|
| Linux | 50 | 46/50 | 92.0% |
| macOS | 65 | 62/65 | 95.4% |
| Windows | 81 | 69/81 | 85.2% |

## 数据来源
- 来源 runs: {'runs/screenspot_pro/iter_zoom_recrop_full_parallel_20260601_2056': 849, 'runs/screenspot_pro/iter_zoom_recrop_wf_recovery_20260601_2335': 18, 'runs/screenspot_pro/iter_zoom_recrop_full_autoretry_20260602_0331': 814}
- 忽略的行: 81 (infra errors treated as ignored, not wrong_format)
