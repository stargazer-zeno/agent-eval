# GameVisualFix Task 001 多模型 Pilot 对比

## 结论先行

本轮已有三个可计分模型结果：本地登录 Codex `gpt-5.6-sol` 与 `doubao-seed-evolving` 均得到 **100/100，任务成功**；Qwen `qwen3-vl-plus` 得到 **42/100，任务失败**。两个 Codex Controller run 都直接定位 Objective profile 并提交与 reference root cause 等价的一行修复；Qwen 误改共享方向算法，在隐藏多方向测试中失败。

本地 Codex 与 Seed Evolving 成功 run 使用相同的 public workspace 文本快照、初始 runtime screenshot、两张 public PNG 和 Controller action 协议，形成一个较可控的同包装子组；但两者的 CLI/provider metadata 和严格输出 Schema 版本仍有差异。Qwen 使用逐步文件工具探索，因此三模型仍不是严格的 apples-to-apples 排名。所有 public-preload run 在 `scores.json` 中保留 `comparison_eligible=false`，避免与预注册的原始逐步协议混淆。

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
| Local Codex / `gpt-5.6-sol` | valid; canonical local Controller | 45 / 35 / 20 | **100** | true | 4 actions；1 张 fresh screenshot；submit |
| Seed Evolving via Codex run2 | valid; compatibility preload | 45 / 35 / 20 | **100** | true | 4 actions；1 张 fresh screenshot；submit |
| Qwen / `qwen3-vl-plus` | valid canonical API run | 18 / 14 / 10 | **42** | false | 17 actions；2 张成功 fresh screenshot；submit |
| Seed Evolving via Codex run1 | invalid provider timeout | — | — | — | 10 个可解析 actions；无 patch；无 observation |
| Seed 2.1 Pro 两次运行 | invalid provider timeout | — | — | — | 只读阶段超时 |
| GPT / Claude API | invalid auth | — | — | — | 首次请求 HTTP 403 |
| Codex login supplement（历史 run） | invalid sandbox/controller | — | — | — | 正确感知症状，但旧 direct-write workspace 操作被拒绝 |

无效运行中 evaluator 的 20/100 只是未修改 Bug workspace 的诊断基线，不进入模型能力比较。

## Seed Evolving 成功分析

成功 run2 的第一步就是覆盖 `resources/profile_alpha.tres`，将 `art_forward_offset` 从 `PI` 改为 `0.0`，没有修改共享算法、Threat profile 或图片资产。第二步请求 fresh observation，Controller clean import 后生成新 PNG；模型随后运行 public smoke 并提交。隐藏矩阵中五方向 × 两分辨率全部通过，动态目标、Threat、WASD、Objective completion、布局和资产完整性也全部通过。

该轨迹表明模型在获得初始 screenshot、两张公开箭头资产和 public text snapshot 后，能够把“Objective 反向、Threat 正常”的视觉差异定位为对象级 profile offset，而非共享方向算法。

## 本地 Codex 成功分析

本地 Codex 使用当前 ChatGPT 登录、`gpt-5.6-sol`、`ultra` reasoning 与 read-only Codex sandbox。文件写入、Godot smoke 和 capture 全部由受限 Controller 执行，因此绕开了历史 direct-write run 的 Windows `workspace-write` 阻断。模型第一步生成同一最小 profile patch，第二步请求 fresh observation，第三步 smoke 通过，第四步 submit。隐藏 10 case、动态行为、Threat、WASD、completion、布局和资产哈希全部通过。

实际任务进程由 VS Code 扩展内 `codex-cli 0.149.0-alpha.4` 执行，其绝对路径和 SHA-256 已记录；审计后 Harness 已改为显式固定 npm native CLI，防止 PowerShell 与 Python PATH 解析漂移。由于首个有效 canonical local run 已成功，本轮没有为切换 CLI 再做 best-of-n 重跑。

## Qwen 失败分析

Qwen 从对称 profile 和共享算法出发，错误地把问题归因于共享坐标变换与两个 `PI` offset。它经历 parse failure、smoke recovery 和 fresh screenshot 驱动的再次修改，最终却反转共享 Y 并忽略全部 profile offset。基线画面看似改善，但隐藏矩阵揭示其过拟合：Functional 18/45、Visual 14/35、Regression 10/20。

## 效率与协议差异

| 有效 run | Wall time | Actions | Fresh PNG | 报告 token 累计 |
| --- | ---: | ---: | ---: | ---: |
| Local Codex | 63.078 s | 4 | 1 | 67,498 |
| Seed Evolving run2 | 125.437 s | 4 | 1 | 206,913 |
| Qwen run1 | 269.031 s | 17 | 2 | 99,741 |

Seed 的 token 数更高，主要因为 Codex Responses thread 每轮携带较大的基础指令与缓存上下文；Qwen 的 controller API prompt 更轻。不能把 token 或 wall time 差异直接解释为模型效率差异。

## 结论边界

- HR 要求的“Seed + 外部模型”最低模型数量与真实分数已满足；Local Codex 与 Seed 有同包装子组，但所有结论仍限定为 Task 001 case study。
- Seed canonical run1 timeout，run2 成功依赖 public preload；这属于工程兼容性结论，也是正式复现实验必须解决的混杂变量。
- 数据集只有一个合成任务，不支持统计显著性、通用模型排名或模型家族结论。
- GPT/Claude 的 403、其他 Seed endpoint timeout 与 Codex sandbox blocker 都是 availability/infrastructure 结果，不是模型能力分数。

本文件是 Task 001 Pilot 的历史摘要。原始运行正文已按最终发布规则移除，历史内容仍可从 Git 历史追溯；正式指标请参阅 [`v2_1_seed_proxy_scores.json`](v2_1_seed_proxy_scores.json) 和 [`final_project_report.md`](../report/final_project_report.md)，脱敏 hash-chain 轨迹见 [`trajectories/v2_1_seed_proxy/`](../trajectories/v2_1_seed_proxy/)。
