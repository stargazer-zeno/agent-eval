# GameVisualFix 项目最终汇报

> 面向 HR 与技术评审的项目总结。正式模型指标冻结于 `gamevisualfix_v2_1_seed_proxy_3x2`；本报告不包含任何新的模型实验。

## 1. 项目结论

本项目完成了一条面向游戏开发视觉调试的 Coding Agent Evaluation 全链路：前期文献边界、原创 Godot 任务、公开/隐藏数据隔离、统一 Controller、runtime screenshot、隐藏自动评分、模型轨迹、失败分类和结果汇总。

最终 v2.1 矩阵包含三道任务和两个 Provider，共六次有效 canonical attempt：

| Provider | T001 | T002 | T003 | 成功率 | 平均总分 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seed Evolving (`doubao-seed-evolving`) | 100 | 100 | 100 | 3/3 | 100.000 |
| Local Codex (`gpt-5.6-sol`) | 100 | 0 | 100 | 2/3 | 66.667 |

Seed 三题均完成补丁、fresh observation、运行检查、提交和隐藏评测。Local Codex 的 T002 是有效模型失败：它没有写入补丁，观察两次后直接提交，隐藏 18-case 全部保留原始 bug，因此 F/V/R 均为 0。六次结果全部为 `valid_canonical`；历史基础设施无效记录没有混入指标。

这个结论只支持本轮小样本的描述性比较，不支持统计显著性、稳定性或广泛模型排名。

## 2. 背景与研究问题

普通 Coding Agent 评测通常关注文本 issue、代码测试或最终 patch。GameVisualFix 关注更窄但更完整的闭环：

`初始 runtime 画面 -> 仓库检索与定位 -> 代码修改 -> 新进程运行 -> fresh screenshot -> 验证或恢复 -> 隐藏评测`

主问题是：Agent 是否能把 runtime visual evidence 用于 repository-level repair，而不是只根据文字或静态代码猜测。次问题是：Visual Perception、Code Localization、Editing、Runtime Verification 和 Recovery 的差异，能否通过可审计 trajectory 与确定性 Oracle 解释。

本项目不声称首次进行多模态 Coding Agent、首次游戏修复或首次截图驱动编辑。文献调研覆盖 GameDevBench、GameCraft-Bench、GameEngineBench、SWE-bench Multimodal、VisualAgentBench、GUIRepair、SVRepair、MM-IssueLoc、CodeV、FailureMem 和 CUADebug，详细来源见 [`research/literature_review.md`](../research/literature_review.md) 与 [`research/gap_analysis.md`](../research/gap_analysis.md)。本项目的具体价值是把 runtime visual evidence、现有游戏仓库修复、fresh observation、隐藏多条件 Oracle 和 recovery 证据链放入同一个受控小型实验。

## 3. 数据集与任务设计

三道任务都不是从空目录生成游戏，而是在已有 Godot 项目中修复一个可运行的视觉/行为 bug。公开 workspace 只提供任务描述、代码、资源和初始证据；参考补丁、隐藏 case、Oracle 与 evaluator 在 Agent 进程结束后才使用。

| Task | 难度标签 | 任务示例 | 隐藏 Oracle | Case 数 |
| --- | --- | --- | --- | ---: |
| T001 Signal Courier | Easy | 修正两个 HUD tracker 的目标方向，同时保持移动目标和窗口尺寸变化下的行为。 | 5 个方向 × 2 个 viewport，方向/几何像素检查、动态更新、布局和资源完整性。 | 10 |
| T002 Orbit Relay | Medium | 修正 camera-space edge tracker，同时保持另一个 tracker 和普通 camera/player 行为。 | 3 个 camera rotation × 2 个 zoom × 3 个 viewport，目标方向、威胁可见性和干净 capture。 | 18 |
| T003 Echo Dash | Hard | 在方向变化和 interruption 下让 temporal trail 始终位于正确一侧。 | 6 个 fixed-tick replay × 2 个 physics rate，每个 replay 生成固定帧 contact sheet。 | 12 |

### 为什么任务规模较小仍有价值

任务规模小是刻意的 P0 设计，而不是把小补丁误称为完整游戏开发能力。小型项目可以减少资产、引擎和环境噪声，让评测清楚观察：模型是否看到了症状、是否找到决定性文件、是否写入合理补丁、是否请求新的运行证据，以及是否在验证失败后改变策略。

判别性来自隐藏条件而不是补丁行数：多方向、多分辨率、camera rotation、zoom、viewport、fixed-tick replay、动态目标、资源完整性和回归行为会阻止只修一个截图或硬编码一个方向。三题也覆盖了静态几何、camera-space 关系和时序 trail 三类不同机制。

因此它不是大型排行榜 benchmark，而是一个低混杂、可复核、可在一天内完成的 end-to-end repair case。它适合展示评测设计能力和 trajectory case study，不能替代大规模任务集。

## 4. 评价指标与 Oracle

每道任务统一使用 100 分：

| 维度 | 分值 | 含义 |
| --- | ---: | --- |
| Functional Correctness | 45 | 运行状态、方向关系、行为逻辑和主要功能 case。 |
| Visual Correctness | 35 | 固定 viewport、状态和时刻下的方向、几何、可见性或 contact-sheet 检查。 |
| Regression Safety | 20 | 目标 bug 之外的 tracker、camera、输入、动态行为、资源和工程完整性。 |

三部分必须同时满分才有 `task_success=true`；总分不能用其他维度抵消 mandatory failure。过程指标包括 action sequence、Controller action 数、fresh observation 数、wall time、turn usage、token telemetry、terminal status 和 failure class。

基础设施有效性优先于分数：provider/CLI/Controller/renderer/evaluator 的可复现故障标记为 `invalid_infrastructure`；timeout、错误 action、错误 patch、预算耗尽和低分都保留为有效模型结果，不重跑。

## 5. 评测流程

1. 在每次 attempt 前从 public seed 建立独立 workspace，移除 `.git`、`.env`、缓存和隐藏内容。
2. 首轮把任务 prompt、初始 runtime PNG 和严格 Controller action schema 交给模型。
3. Controller 只执行白名单动作：`list_files`、`read_file`、`write_file`、`run_smoke`、`observe`、`submit`。
4. `observe` 复制当前 workspace，启动固定 Godot 4.7.1 renderer，产生 fresh PNG，并通过同一显式 resume 回传模型。
5. `submit` 后冻结 workspace，隐藏 evaluator 在 Agent 进程结束后执行，输出 Functional/Visual/Regression 分数。
6. 正式顺序固定为 T001→T002→T003，每题 Seed→Local，每个 Provider/Task 只接受一次有效 canonical attempt。

Seed 通过仅监听 `127.0.0.1` 随机端口的 Responses SSE 归一化代理转发到固定 Agent Plan 上游。代理依据 OpenAI Responses streaming event 规范补齐缺失的 item/part envelope、`added/done` 生命周期和单调 `sequence_number`，不改写模型 delta、reasoning、usage、HTTP 状态或完成状态。未知或畸形流 fail closed。

正式运行前完成了 synthetic canary（三张合成图片、长 prompt、两次显式 resume）、Harness fixture self-test、三题 import/smoke/capture/private evaluator preflight 和代理标准库单测。

## 6. 正式结果

完整机器结果见 [`results/v2_1_seed_proxy_scores.json`](../results/v2_1_seed_proxy_scores.json)，对比表见 [`results/v2_1_seed_proxy_comparison.md`](../results/v2_1_seed_proxy_comparison.md)。

| Task | Provider | F | V | R | Total | Success | Actions | Fresh obs | Seconds |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| T001 | Seed | 45 | 35 | 20 | 100 | yes | 5 | 1 | 105.969 |
| T001 | Local Codex | 45 | 35 | 20 | 100 | yes | 8 | 1 | 76.016 |
| T002 | Seed | 45 | 35 | 20 | 100 | yes | 4 | 1 | 89.188 |
| T002 | Local Codex | 0 | 0 | 0 | 0 | no | 4 | 2 | 107.485 |
| T003 | Seed | 45 | 35 | 20 | 100 | yes | 3 | 1 | 111.875 |
| T003 | Local Codex | 45 | 35 | 20 | 100 | yes | 6 | 1 | 80.172 |

### Aggregate telemetry

| Provider | Total actions | Successful fresh obs | Total seconds | Input tokens | Cached input | Output tokens | Reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Seed | 12 | 3 | 307.032 | 223,953 | 169,832 | 9,490 | 6,222 |
| Local Codex | 18 | 4 | 263.673 | 412,757 | 244,480 | 5,973 | 2,393 |

Token 和 wall time 是运行 telemetry，不等于最终账单。Seed 总耗时更高，但 action 更少；Local 总耗时较低但 action 更多。样本太小，不能把这些差异解释为稳定效率优势。

## 7. 轨迹示例与案例分析

脱敏 action/observation hash-chain 位于 [`trajectories/v2_1_seed_proxy/`](../trajectories/v2_1_seed_proxy/)，receipt 不包含 provider reasoning、模型正文或文件正文。

### Seed T002：完成闭环

`write_file -> observe -> run_smoke -> submit`

Seed 首先定位并修改 camera-space tracker，随后请求新的 BASELINE observation，运行 public smoke 并提交。隐藏 18-case 全部通过。该 run 的 adapter receipt 记录了 6 条 upstream stream，其中 2 条出现代理不负责猜测的 `function_call` item；代理对这两条流 fail closed，Codex 在同一 canonical attempt 内通过既有 stream retry 恢复，最终形成完整的 4-turn Controller trajectory。这不是额外实验，也不是 invalidation。

### Local T002：有效模型失败

`read_file -> observe -> observe -> submit`

Local 读取代码后连续请求两次观察，但从未执行 `write_file`。18 个 rotation × zoom × viewport 隐藏 case 都能渲染，但目标 tracker 没有修复，Functional/Visual/Regression 分别为 0/45、0/35、0/20。这个结果说明“能够启动程序和获得截图”不等于“完成 repository repair”，也说明 evaluator 的 gated score 能区分可运行但未修复的提交。

更多逐题说明见 [`results/v2_1_seed_proxy_case_study.md`](../results/v2_1_seed_proxy_case_study.md)。

## 8. 成本与资源

### 已知运行成本指标

| 项目 | Seed | Local Codex | 备注 |
| --- | ---: | ---: | --- |
| Canonical attempts | 3 | 3 | 每题一次有效 attempt。 |
| Wall time | 307.032 s | 263.673 s | 三题总和。 |
| Controller actions | 12 | 18 | 包含 read/write/observe/smoke/submit。 |
| Input tokens | 223,953 | 412,757 | Provider/Codex telemetry。 |
| Cached input tokens | 169,832 | 244,480 | Provider/Codex telemetry。 |
| Output tokens | 9,490 | 5,973 | Provider/Codex telemetry。 |
| Reasoning output tokens | 6,222 | 2,393 | 只记录统计值，不发布 reasoning 正文。 |

### 待项目负责人补充

| 成本项 | 当前值 | 说明 |
| --- | --- | --- |
| Seed Agent Plan/API 金额 | 待补充 | 当前没有可靠账单或统一单价口径。 |
| Local Codex 订阅/调用金额 | 待补充 | 本地登录订阅不等价于单次 API 价格。 |
| 人工设计、调试和整理工时 | 待补充 | 代码和报告中没有完整工时记录。 |
| 设备、GPU、网络和电力成本 | 待补充 | 使用单台本地 Windows 机器，未做成本计量。 |
| 总项目成本 | 待补充 | 不用 token 数反推金额。 |

## 9. 有效性、安全与历史 lineage

- v2.1 六个 manifest 均为 schema v3、同一 suite、`submitted` 且 evaluator 正常退出。
- Seed 三题都有至少一次成功 fresh observation；六条脱敏 trajectory 共 30 个事件，hash-chain 与 receipt 一致。
- 旧 v2 Seed transport invalid、旧 Local adapter-path invalid 和早期失败 canary 保留在 v2.1 score JSON 的 `excluded_lineage` 中，不进入 v2.1 aggregate。
- `.env`、API key、Authorization、原始 Provider delta/reasoning 不进入最终树；Codex 生命周期日志只保留事件类型、usage 和正文哈希，canonical manifest 中的提交摘要也仅保留字节数与 SHA-256 指纹。
- 当前公开树移除旧 raw 运行正文，但已有 Git 历史不改写；历史提交仍按 Git 原有 lineage 保存。

## 10. 局限与后续建议

1. 每个模型只有三道任务、每个 pair 一次有效 attempt，无法做统计显著性、方差或稳定性结论。
2. 六个结果中五个达到 100 分，存在明显 ceiling effect；T002 Local 的单次失败不能证明稳定模型差异。
3. 任务是小型合成 Godot repair case，不代表真实大型游戏仓库、其他引擎或长期维护能力。
4. 运行使用单机、单账户、Godot 4.7.1 和 Codex 0.149.0；升级 Provider、CLI 或 renderer 后应创建新 suite，而不是混入本 suite。
5. 后续可增加 layout、动画/瞬态、资源管理、多文件重构和真正失败后 recovery 任务，并把每题扩展到多次独立 attempt。
6. 后续实验应统一不同模型的 prompt/image packaging、CLI 版本、model metadata、sandbox/VM 隔离和成本账单口径。

## 11. 项目索引

- v2.1 正式技术报告：[`report/v2_1_seed_proxy_report.md`](v2_1_seed_proxy_report.md)
- v2.1 机器矩阵：[`results/v2_1_seed_proxy_scores.json`](../results/v2_1_seed_proxy_scores.json)
- v2.1 对比与 Case Study：[`results/`](../results/)
- v2.1 脱敏 trajectories：[`trajectories/v2_1_seed_proxy/`](../trajectories/v2_1_seed_proxy/)
- 文献调研：[`research/literature_review.md`](../research/literature_review.md)
- Benchmark 规格：[`design/benchmark_spec.md`](../design/benchmark_spec.md)
- Harness 使用说明：[`harness/README.md`](../harness/README.md)
