# GameVisualFix Task 001 多模型 Pilot 对比

## 结论先行

本轮完成了 4 个 `.env` provider 与 1 个 Codex 登录态补充入口的端到端调度，但只有 Qwen 形成可计分的模型结果。Qwen 完成了多轮读写、公开检查、两张成功的 Patch 后 fresh screenshot 和最终提交，隐藏评分为 **42/100，任务失败**。Seed 连续两次在完成若干只读 action 后发生 provider timeout；GPT 与 Claude 在首次鉴权时返回 HTTP 403；Codex 登录态受 Windows workspace sandbox 阻断。后三类均不能当成模型能力分数。

## 统一评价指标

| 指标 | 满分 | 成功条件 |
| --- | ---: | --- |
| Functional Correctness | 45 | 10 个方向/分辨率 case 全部通过 |
| Visual Correctness | 35 | 箭头语义像素、方向点积与视觉契约全部通过 |
| Regression Safety | 20 | Threat、动态目标、WASD、Objective completion、布局、节点和资产完整性通过 |
| Task Success | — | Build/integrity gate 通过且三类指标全部满分 |

## 运行结果

| Provider / Model | Validity | F / V / R | Total | Success | 可观察过程 |
| --- | --- | ---: | ---: | --- | --- |
| Qwen / `qwen3-vl-plus` | valid model result | 18 / 14 / 10 | **42** | false | 17 actions；2 张成功 fresh screenshot；submit |
| Seed / `doubao-seed-2-1-pro-260628` run 1 | invalid provider timeout | — | — | — | 7 个有效只读 actions 后 timeout |
| Seed / 同模型 run 2 | invalid provider timeout | — | — | — | 放宽窗口后 5 个有效只读 actions，仍 timeout |
| GPT API / `gpt-5.6-sol` | invalid auth | — | — | — | 首次请求 HTTP 403，模型未接触任务 |
| Claude API / `claude-sonnet-4-6` | invalid auth | — | — | — | 首次请求 HTTP 403，模型未接触任务 |
| Codex login / `gpt-5.6-sol` | invalid Windows sandbox/controller | — | — | — | 正确感知初始症状，但所有读写被 sandbox 拒绝 |

无效运行中 evaluator 显示的 20/100 只是未修改 Bug workspace 的诊断基线，已在 `scores.json` 中保存为 `diagnostic_baseline_total`，不进入模型对比。

## Qwen 结果解释

Qwen 从对称 profile 和共享算法出发，错误地把问题归因于共享坐标变换与两个 `PI` offset。它先产生 parse error，经公开 smoke 反馈修复语法；第一次成功 fresh observation 后，它明确观察到 Objective 仍向左且 Threat 空间关系也不正确，于是继续修改。最终 patch 对共享算法做了 Y 反转并完全忽略 profile offset，基线画面看似改善，但隐藏多方向/双分辨率矩阵揭示其非根因：Functional 仅 18/45、Visual 14/35，并破坏 Threat/动态行为使 Regression 只有 10/20。

因此，该轨迹展示了视觉闭环的价值，也展示了单张 post-patch screenshot 的局限：fresh observation 促成了真实 recovery，但模型仍对局部画面过拟合，自动 Oracle 才能判定其未解决任务。

## 可比性边界

- 只有一个有效模型结果，不能给出 Seed vs external 的强弱结论，也不能形成正式排行榜。
- Provider timeout 与 403 是部署/凭据可用性结果，不是模型推理能力结果。
- API Harness 采用 controller-mediated 文件工具，Codex 补充入口采用 CLI workspace 工具，后者又未通过 sandbox gate，二者不可直接比较效率。
- 数据集仅 1 个合成任务；所有结论都是工程 pilot 与 case study。

机器可读数据见 `results/scores.json`，逐运行原始记录见 `experiments/task_001/`，hash-chain trajectory 见 `trajectories/task_001/`。
