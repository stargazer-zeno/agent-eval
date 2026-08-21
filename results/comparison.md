# GameVisualFix Task 001 多模型 Pilot 对比

## 结论先行

本轮已有两个可计分模型结果：`doubao-seed-evolving` 通过 Codex CLI compatibility run 得到 **100/100，任务成功**；Qwen `qwen3-vl-plus` 得到 **42/100，任务失败**。Seed Evolving 直接定位 Objective profile 并提交与 reference root cause 等价的一行修复；Qwen 误改共享方向算法，在隐藏多方向测试中失败。

但这不是严格的 apples-to-apples 排名：Seed Evolving canonical run 因多轮 Responses 延迟超时，成功的 run2 预载了同一 public workspace 的文本并附上两张 public PNG，以减少 Codex 每文件一次完整推理的往返；Qwen 使用逐步文件工具探索。因此 Seed run2 是有效任务结果，但在 `scores.json` 中标记为 `comparison_eligible=false`。

## 统一评价指标

| 指标 | 满分 | 成功条件 |
| --- | ---: | --- |
| Functional Correctness | 45 | 10 个方向/分辨率 case 全部通过 |
| Visual Correctness | 35 | 箭头语义像素、方向点积与视觉契约全部通过 |
| Regression Safety | 20 | Threat、动态目标、WASD、Objective completion、布局、节点和资产完整性通过 |
| Task Success | — | Build/integrity gate 通过且三类指标全部满分 |

## 主要运行结果

| Provider / Model | Validity | F / V / R | Total | Success | 可观察过程 |
| --- | --- | ---: | ---: | --- | --- |
| Seed Evolving via Codex run2 | valid; compatibility preload | 45 / 35 / 20 | **100** | true | 4 actions；1 张 fresh screenshot；submit |
| Qwen / `qwen3-vl-plus` | valid canonical API run | 18 / 14 / 10 | **42** | false | 17 actions；2 张成功 fresh screenshot；submit |
| Seed Evolving via Codex run1 | invalid provider timeout | — | — | — | 10 个可解析 actions；无 patch；无 observation |
| Seed 2.1 Pro 两次运行 | invalid provider timeout | — | — | — | 只读阶段超时 |
| GPT / Claude API | invalid auth | — | — | — | 首次请求 HTTP 403 |
| Codex login supplement | invalid sandbox/controller | — | — | — | 正确感知症状，但 workspace 操作被拒绝 |

无效运行中 evaluator 的 20/100 只是未修改 Bug workspace 的诊断基线，不进入模型能力比较。

## Seed Evolving 成功分析

成功 run2 的第一步就是覆盖 `resources/profile_alpha.tres`，将 `art_forward_offset` 从 `PI` 改为 `0.0`，没有修改共享算法、Threat profile 或图片资产。第二步请求 fresh observation，Controller clean import 后生成新 PNG；模型随后运行 public smoke 并提交。隐藏矩阵中五方向 × 两分辨率全部通过，动态目标、Threat、WASD、Objective completion、布局和资产完整性也全部通过。

该轨迹表明模型在获得初始 screenshot、两张公开箭头资产和 public text snapshot 后，能够把“Objective 反向、Threat 正常”的视觉差异定位为对象级 profile offset，而非共享方向算法。

## Qwen 失败分析

Qwen 从对称 profile 和共享算法出发，错误地把问题归因于共享坐标变换与两个 `PI` offset。它经历 parse failure、smoke recovery 和 fresh screenshot 驱动的再次修改，最终却反转共享 Y 并忽略全部 profile offset。基线画面看似改善，但隐藏矩阵揭示其过拟合：Functional 18/45、Visual 14/35、Regression 10/20。

## 效率与协议差异

| 有效 run | Wall time | Actions | Fresh PNG | 报告 token 累计 |
| --- | ---: | ---: | ---: | ---: |
| Seed Evolving run2 | 125.437 s | 4 | 1 | 206,913 |
| Qwen run1 | 269.031 s | 17 | 2 | 99,741 |

Seed 的 token 数更高，主要因为 Codex Responses thread 每轮携带较大的基础指令与缓存上下文；Qwen 的 controller API prompt 更轻。不能把 token 或 wall time 差异直接解释为模型效率差异。

## 结论边界

- HR 要求的“Seed + 外部模型”最低模型数量与真实分数已满足，但 Harness/input packaging 不完全一致，强弱结论只能写成 Task 001 case study。
- Seed canonical run1 timeout，run2 成功依赖 public preload；这属于工程兼容性结论，也是正式复现实验必须解决的混杂变量。
- 数据集只有一个合成任务，不支持统计显著性、通用模型排名或模型家族结论。
- GPT/Claude 的 403、其他 Seed endpoint timeout 与 Codex sandbox blocker 都是 availability/infrastructure 结果，不是模型能力分数。

机器可读数据见 `results/scores.json`，原始记录见 `experiments/task_001/`，hash-chain trajectory 见 `trajectories/task_001/`。
