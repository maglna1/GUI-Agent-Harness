# Benchmarks Overview — GUI Agent Harness

| Benchmark | Status | Best Model | Best Acc | Samples |
|-----------|--------|------------|----------|---------|
| [ScreenSpot Pro](screenspot_pro/) | ✅ Done | Claude 4.7 (stratified) / GPT-5.5 (full) | 79.5% / **87.9%** | 78/1581 (stratified) / 1581/1581 (full) |
| [ScreenSpot v2](screenspot_v2/) | ✅ Done | GPT-5.5 | **95.83%** | 1272/1272 |
| [ScreenSpot v1](screenspot_v1/) | ❌ Not run | — | — | 0/~1272 |
| [MMBench-GUI-L2](mmbench_gui_l2/) | ✅ Done | GPT-5.5 | **91.52%** | 3594/3594 |
| [OSWorld](osworld/) | Partial | Claude 4.6 | 93.5% (Chrome) | 172+/369 |

## 运行目录结构
```
benchmarks/
  screenspot_pro/     # ScreenSpot Pro (1581 专业软件样本)
    results/
      claude_opus_4_7/  # Claude 4.7 结果
      claude_opus_4_8/  # Claude 4.8 结果
      gpt_5_5/          # GPT-5.5 完整结果
    configs/
      main_baseline.yaml    # Legacy 管线配置
      known_good.yaml       # 新管线配置
    README.md
  screenspot_v2/
    results/
      gpt_5_5/
    README.md
  screenspot_v1/
    README.md
  mmbench_gui_l2/
    results/
      gpt_5_5/
    README.md
  osworld/
    docs/              # 任务文档
    scripts/           # Python/Shell 脚本
    config/            # 任务配置
    results/           # 模型结果
    README.md
  README.md (this file)
```

## 原始数据
所有原始 JSONL 结果、错误日志和运行脚本保存在 `runs/` 目录下：
- `runs/screenspot_pro/` — ScreenSpot 系列所有运行
- `runs/gui_grounding/` — MMBench-GUI-L2 等 grounding 基准运行
- `benchmarks/osworld/` — OSWorld 各 domain 结果（早期 Claude Code CLI + GPT-5.5 测试）
