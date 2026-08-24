# GameVisualFix v3：Seed 能力边界三任务原型报告

> **Prototype Benchmark / Single-model Case Study**
> Suite: `gamevisualfix_v3_seed_boundary_3x1`
> Model: `doubao-seed-evolving` through Codex CLI 0.149.0
> Date: 2026-08-24

## 执行结论

本轮完成了三道独立、可运行、可自动评分的 Godot 4.7.1 原型，并用统一 Codex Controller Harness 对 Seed 各执行一次有效 canonical attempt。最终结果为：

| Task | 主要能力边界 | Hidden cases | F | V | R | Total | Task Success |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| T004 Glyph Atlas | 跨图细粒度对应、空间变换、工具执行 | 36 | 5 | 0 | 20 | 25 | false |
| T005 Checkpoint Mosaic | 持久状态、长程执行、延迟依赖 | 12 | 30 | 0 | 20 | 50 | false |
| T006 Mirrorstorm | 动态阶段、生命周期诊断、恢复 | 12 | 45 | 35 | 20 | 100 | true |

主指标 `Task Success Rate = 1/3 = 33.3%`；平均 `F=26.667`、`V=11.667`、`R=20.000`、总分 `58.333`。T004 与 T005 成功暴露能力边界，T006 出现 ceiling，未实现“三题全部失败”的理想目标，但按预注册规则没有结果后调参。

## 数据集与任务设计

### T004 — Glyph Atlas

8 个无文字世界地标与 8 个匿名 minimap glyph 形成非平凡置换，同时存在 camera rotation 与 portal reflection 的组合顺序错误。两张初始 PNG 和四个公开视角是确定 mapping/transform 的必要证据；公开文件名不编码对应关系。隐藏评价覆盖 6 rotations × 2 parity × 3 viewports。

### T005 — Checkpoint Mosaic

旧存档恢复链由 `LOBBY -> RESTORED_MIDPOINT -> POST_ELEVATOR -> FINAL_RESTORE` 四阶段构成。Controller 状态保存在 Agent workspace 外，只有当前 Gate 正确时 `ADVANCE` 才推进。Lobby seal 顺序在后续不重复，最终 HUD 仍依赖早期视觉证据。三个 Functional Gate 分别评价 route、migration、hint。

### T006 — Mirrorstorm

8-frame contact sheet 与仅含 tick/signal 的 trace 共同描述 deferred telegraph Bug。隐藏评价覆盖 CALM、MIRRORED_ENRAGED、INTERRUPTED_RESUME，30/60 tick 与左右方向，检查 movement commit、immutable sample、live-state read、epoch 和 pool reuse。

完整 Prompt、私有 Ground Truth、预期轨迹、失败模式和 50–500 条扩展模板见 `design/v3_hard_task_prototypes.md`；数据集机器索引见 `benchmark/dataset_v3.json`。

## Benchmark validity

三个任务均在模型接触前通过 Gate：

| Task | Bug State ×3 | Reference State ×3 | Equivalent patch | Shortcut rejection | Stable render |
| --- | --- | --- | --- | --- | --- |
| T004 | 25/100, fail | 100/100, pass | pass | mapping-only、transform-only、asset replacement 均 fail | pass |
| T005 | 20/100, fail | 100/100, pass | pass | route-only 35、route+migration-only 50，均 fail | pass |
| T006 | 20/100, fail | 100/100, pass | pass | initial-only 45、parity-only 20、hidden 0，均 fail | pass |

所有 evaluator 都以 Build/launch 为硬门槛，Task Success 要求 Functional、Visual、Regression mandatory groups 全通过。Reference 与非 byte-identical 等价实现均为 100，说明评价器不匹配固定 diff。公开包 leak audit 与 Caption necessity gate 均有机器可读记录。

需要诚实说明两点：T005 是确定性 migration table 原型，而非生产序列化后端；T006 是生命周期契约的合成 contact sheet，公开布尔常量和注释降低了逆向定位难度。这不影响评分可复现性，但限制了生态有效性与难度外推。

## Harness 与污染控制

- 首轮只注入 Prompt 与 manifest 声明的图片，源码必须通过 `list_files/read_file` 懒加载。
- 模型只能返回固定 JSON Action；文件读写、smoke、observe、state transition 与 submit 由 Controller 执行。
- task-local state、private evaluator、Oracle、reference patch、主仓库和凭据都不进入 Agent workspace。
- 每次成功观察记录 phase before/after、advanced、workspace/state/PNG hash、UTC timestamp 与 hash-chain receipt。
- 隐藏 evaluator 总是从独立 candidate copy 和 State 0 重放，不读取 Agent 实验状态。
- 归档排除 `.env`、Provider 原始流、reasoning、run-local Codex session 与 Agent workspace；保留脱敏 lifecycle、action/state receipt、patch、截图和评分。

固定预算为每题 30 Controller actions、8 fresh observations、40 分钟，总计 56 个有效 actions、11 张 fresh images、1987.502 秒。token 仅为 Provider 每 turn 回报值的描述性求和，不作为跨 Provider 预算或成本结论。

## Provider availability 与基础设施 lineage

三轮归档 canary 均完成三图、长 Prompt、strict JSON、thread start 与两次 resume，`active_item_errors=0`。正式运行中保留两次基础设施 invalid：

1. T004 首次 attempt 在 12 actions 后，第 13 次 resume 因上下文膨胀出现 transport failure。上一 turn 为 208,023 input + 31,688 output tokens。Harness 随后显式声明 Seed 256k context window，并在 180k 自动 compact；修复有单元测试且未改变任务或模型 reasoning policy。
2. T005 首次 attempt 在 0 actions 时出现瞬态 stream/transport failure。紧随其后的全新 canary 通过，因此使用唯一一次 fresh rerun。

两次 invalid 的 evaluator 分数不进入主矩阵。T004 rerun、T005 rerun 与 T006 首次 attempt 均为 `valid_canonical`。

## 真实能力结果与阶段诊断

### T004：Perception 到 Editing 的断点

Seed 读取相关源码并观察全部四个公开视角，但没有发出 `write_file`；四张图都属于 Patch 前观察。第 12 回合达到单 turn 240 秒上限，最终保持 Bug State，25/100。证据支持“多图证据没有及时转化为编辑”，但不能进一步断言 glyph perception 本身错误。

### T005：最有研究价值的失败

第一次 `ADVANCE` 在 Lobby 停留；随后出现不可读路径、一次 invalid schema 和重复列目录。Seed 经过两轮编辑后在 Step 28 进入 midpoint，证明发生了真实 Recovery。最终 route 和 hint 正确、migration 错误，得 50/100；状态链无法继续，30-turn 循环耗尽。该失败把长期依赖问题精确定位到中间 migration，而不是笼统记为“任务失败”。

### T006：一次性成功与原型 ceiling

Seed 读取全部组件，连续修改 attack/sample/renderer/pool，smoke 后进入 mirrored phase并重放，随后 submit。虽然没有公开进入 interrupted phase，隐藏 12-case evaluator 全通过。Recovery 因没有首次失败记为 `N/A`。这表明 Seed 能从明确的公开架构契约完成跨文件修复，也表明当前 T006 的正确方向过于容易从常量名与注释推断。

逐步证据与 hash-chain 见 `results/v3_seed_boundary_case_study.md` 和 `trajectories/v3_seed_boundary/`。

## 回答本轮研究问题

1. **三题攻击的边界**：T004 攻击跨图视觉对应到工具编辑的转换；T005 攻击失败恢复后的持久状态与延迟依赖；T006 攻击动态 phase 与 deferred lifecycle，但本实例未触及 Seed 边界。
2. **最值得扩展的 family**：T005。它同时提供视觉记忆、工具执行、状态推进、局部得分和明确 failure stage，且 route graph/save migration 可程序化生成。
3. **Seed 仍成功时如何增难**：不修改已冻结实例；下一轮增加分支状态图、多版本组合 migration、阶段间反事实 replay 与多个初始等价修复候选。尤其要把 T006 的具名布尔开关替换成真实 event ordering 和对象池代码，使后续 phase 图像成为消歧证据。
4. **论文潜力**：以 T005 的 **stateful visual software-engineering agents** 为主线，T004 作为 cross-view perception 子集，重构后的 T006 作为 recovery 子集。正式 novelty 声明仍需补充相邻工作检索，不能据三道合成题声称“首次”。

## 后续数据扩展建议

优先把 T005 扩展为 30–50 条 calibration set，再决定是否到 300 条：

- 程序化生成 seal codebook、route DAG、旧/新 schema 差、延迟引用距离和分支恢复点；
- 预注册 easy/medium/hard strata，以人类基线和至少两个强 Agent 校准，而不是按单模型结果调阈值；
- 每实例保留 Bug ×3、Reference ×3、shortcut、equivalent patch、caption/no-image 与 leak Gate；
- 将 Functional partial gates 保留为诊断指标，Task Success 继续要求全链通过；
- 为 T004 控制单回合推理时长影响，增加多模型复验，区分 perceptual failure 与 planning latency；
- 重写 T006 为真实事件队列/对象池实现，并让至少两个后续 phase 对初始合理候选产生不同可观察结果。

## 局限

- `n=3`、单模型、每题一次有效 attempt，不支持统计显著性、通用排名或模型优劣外推。
- 三题均为合成 Godot 原型，尚未覆盖真实大型游戏仓库、多人协作代码或平台差异。
- Caption necessity 是设计与候选空间 Gate，不是正式随机化 no-image 因果消融。
- Visual 评分仍以确定性 semantic/pixel contract 为主，不代表玩家主观体验。
- T004 的 timeout 和 T005 的工具循环表明预算也是任务交互的一部分；后续论文实验应同时报告 outcome 与预算敏感性。

## 可复现实物

- 设计：`design/v3_hard_task_prototypes.md`
- 数据索引：`benchmark/dataset_v3.json`
- 任务：`benchmark/task_004/`、`task_005/`、`task_006/`
- Harness：`harness/run_codex_eval.py`、`stateful_controller.py`
- 分数：`results/v3_seed_boundary_scores.json`
- Case Study：`results/v3_seed_boundary_case_study.md`
- 脱敏实验：`experiments/v3_seed_boundary/archive/`
- Hash-chain trajectories：`trajectories/v3_seed_boundary/`
