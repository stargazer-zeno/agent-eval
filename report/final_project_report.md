# GameVisualFix 项目最终汇报

日期：2026-08-24
交付版本：`gamevisualfix_v3_seed_fulltrace_partialfix_3x1`

## 1. 执行摘要

本次最终示例已替换为 GameVisualFix v3 的三道高难度 Godot 任务与 `doubao-seed-evolving` 的完整轨迹复跑结果。实验使用 Codex CLI Controller Action Harness；每题只接受一次传输层修复后的 canonical attempt，隐藏评价器从干净状态独立重放。

结果显示，Seed 在三题中完成 1 题：T004 的跨图 glyph–landmark 绑定失败，T005 的长程 checkpoint 恢复链在延迟 HUD hint 依赖处失败，T006 的动态 phase/pool 生命周期修复成功。Task Success Rate 为 **1/3（33.3%）**，平均总分为 **65.0/100**。这不是模型排名或统计显著性结论，而是一次可审计的能力边界 case study。

## 2. 研究问题与任务范围

v3 的问题不再是“模型能否修一个单点视觉 Bug”，而是测试视觉证据、仓库定位、连续工具操作与运行时状态是否能形成可靠闭环：

1. 跨图细粒度对应、空间变换与代码修改能否一致；
2. 模型能否保存早期视觉证据，并在后续状态中完成延迟依赖；
3. 面对运行时 phase 变化时，模型能否定位 sample 生命周期、修复多文件逻辑并验证回归。

三题均为 Godot 4.7.1 项目。Agent 只能经 Controller 输出 `list_files`、`read_file`、`write_file`、`run_smoke`、`observe`、`submit` 六类 JSON action；没有直接 shell、网络、私有评测器或 Oracle 访问权限。每题预算为 30 个 action、8 次 fresh observation、40 分钟。

## 3. 可展示数据集：三道 v3 原型任务

| Task | 名称 | 主要能力边界 | 视觉输入与关键状态 | 自动评价 |
| --- | --- | --- | --- | --- |
| T004 | Glyph Atlas — Multi-View Landmark Registration | 跨图 glyph 对应、相机旋转与镜像空间推理 | 初始 world/minimap 双图；`ROTATE_37`、`PORTAL_MIRROR`、`WIDE_VIEW` | 6 rotations × 2 parity × 3 viewports 的 identity、位置、朝向 Oracle |
| T005 | Checkpoint Mosaic — Delayed Save-Migration Chain | 视觉记忆、持久状态、存档迁移、延迟 HUD 依赖 | Lobby seal 图；`LOBBY → RESTORED_MIDPOINT → POST_ELEVATOR → FINAL_RESTORE` 状态机 | 三个 checkpoint gate、old/new save、重载、位置与 asset hash |
| T006 | Mirrorstorm — Phase-Changing Telegraph Recovery | 时序视觉、不可变 sample、phase 变化与 pool recovery | 带帧号 contact sheet；`CALM → MIRRORED_ENRAGED → INTERRUPTED_RESUME` | 30/60 tick replay、镜像 parity、epoch、pool lifecycle 像素/状态 Oracle |

每题的隐藏评分都固定为 Functional 45、Visual 35、Regression 20。`task_success=true` 必须三类 mandatory tests 全部通过；总分不能补偿任何一类失败。评测器同时拒绝隐藏 UI、替换图片、固定角度、关闭镜像、跳过状态机等 shortcut patch。

## 4. 实验设置与完整轨迹

模型为 `doubao-seed-evolving`，通过仅绑定 `127.0.0.1` 的 Seed Responses SSE compatibility proxy 接入 Codex CLI。所有任务在模型接触前已冻结 Prompt、公开文件树、截图、预算、Evaluator 与 Oracle 哈希；早期因上游缺失 terminal event 造成的 T004 运行保留为 `invalid_infrastructure`，不进入下表指标。代理修复只补足已完成 assistant item 缺失的终止事件，并显式传递 `partial=false`；没有改变任务、图像、预算、阈值、Oracle 或模型配置。

本交付包保留每个 canonical run 的：完整 agent JSONL、实际 assistant 文本、provider/Codex 返回的 reasoning summary（若有）、每轮 raw Codex JSON event、Controller tool receipt、截图、状态 ledger、final patch 与 evaluator 输出。它不合成或重建隐藏 chain-of-thought，也不包含 API key、Authorization header 或 `.env`。

## 5. 实验结果

机器可读汇总：[`results/v3_seed_fulltrace_replay_scores.json`](../results/v3_seed_fulltrace_replay_scores.json)。

| Task | Terminal | Actions | Fresh observations | Functional | Visual | Regression | Total | Task Success | 失败阶段 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| T004 Glyph Atlas | submitted | 15 | 4 | 25 | 0 | 20 | 45 | 否 | cross-view glyph binding |
| T005 Checkpoint Mosaic | model turn timeout | 27 | 8 | 30 | 0 | 20 | 50 | 否 | delayed HUD-hint dependency after route and migration |
| T006 Mirrorstorm | submitted | 17 | 2 | 45 | 35 | 20 | 100 | 是 | — |
| 平均 / 汇总 | — | 59 | 14 | 33.333 | 11.667 | 20.000 | 65.000 | 1/3 | — |

三次 canonical attempt 总耗时为 2,758.640 秒。T005 的 `model turn timeout` 是有效模型结果：Agent 已耗用 27 个 action 与 8 次观察，未在预算内完成最终状态的修复与提交，因此不能重跑或按基础设施失败处理。

## 6. 案例与轨迹分析

### T004：局部空间修复掩盖了 identity mapping 缺失

T004 是跨图标记注册任务。Agent 读取 projection、registry、binding 和 capture 代码，先后观察 baseline、rotation 与 mirror 场景，然后仅将 `projection.gd` 中的 rotation/mirror 顺序改为 rotate-then-mirror。公开 smoke 通过，且它请求了 patch 后的新镜像观察，但隐藏 Evaluator 仍给出 Functional 25、Visual 0、Regression 20。

原因是该补丁只覆盖空间 transform；8 个 glyph 与 landmark 的 binding permutation 仍错误。轨迹显示 Agent 把“identity 对应”与“位置变换”两项耦合问题过早归结为单一 projection 假设，未完成跨图 glyph codebook 的排除式匹配。这是可诊断的 `Perception/Localization → Editing → Verification` 断链，而不是渲染或评分器故障。

### T005：早期视觉线索未可靠跨状态保留

T005 中，Lobby 的细粒度 seal 顺序是后续 `FINAL_RESTORE` HUD hint 的必要输入。Agent 能推进 route binding 与部分 v1→v2 migration，因此 Functional 获得 30 分、Regression 获得 20 分；但在多轮状态推进、截图和代码修改后，未能将 Lobby 证据与最终 restore state 正确联结。最终 Visual 为 0，且最后一轮模型调用超时。

该案例将失败定位到 `Visual Evidence → State Tracking → Delayed Dependency`：问题不只是代码定位，而是视觉映射在长程执行中被保持、调用和验证的能力。

### T006：一次性架构性修复成功

T006 的 Agent 在 17 个 action、2 次 fresh observation 内完成 attack controller、不可变 sample、renderer/pool 的一致性修复，隐藏 evaluator 的 Functional、Visual、Regression 均通过。该成功说明该模型在可见 trace 与 contact sheet 辅助下，能处理一类跨文件的时序 sample 生命周期问题；因此不能把 v3 失败简单归因为“任务太难”或“模型不能处理动态视觉”。

三题的完整证据在交付包 `experiments/v3_seed_fulltrace/` 下；每个 canonical run 的 `full_trajectory.jsonl` 是单 episode 附件式记录，`codex_raw/turn_*.jsonl` 保留逐轮原始 JSON event，`trajectory.jsonl` 与 `state_ledger.jsonl` 则提供便于审计的 action/状态 hash-chain。

## 7. 结论、有效性与局限

- v3 的结果暴露了两个更稳定、可扩展的候选能力边界：跨图视觉 identity binding（T004）与有延迟引用的 stateful visual software engineering（T005）。
- T005 最适合作为 Benchmark Family 主线：可程序化生成 route graph、seal codebook、migration variant 与状态长度，并维持严格自动评分。
- T006 的成功是必要的反例，说明 suite 中仍保留模型可完成的真实工程任务，避免所有题目成为不可诊断的高难 Puzzle。
- 每题仅有一次 Seed attempt；结果应解释为 case study，不应外推为总体能力排名、成本优劣或统计显著性结论。
- 完整轨迹包含模型正文与 provider 返回的 reasoning summaries，因此只随本地 leader 交付包分发，不应直接提交到公共 Git 仓库或外部共享位置。

## 8. 交付内容与复现入口

`gameFix/` 交付目录包含：

1. `benchmark/`：T004–T006 Godot 源文件、public/private evaluator、Oracle 和 task manifests；
2. `harness/`：统一 Codex runner、Seed proxy、stateful controller、schema 与对应测试；
3. `experiments/`：三次 canonical run、截图、补丁、评分、完整轨迹与早期 T004 传输层无效谱系；
4. `results/`：机器可读结果和案例报告；
5. `design/`：任务设计、完整轨迹导出协议与 transport diagnosis；
6. 本报告的 Markdown 与 PDF 版本。

环境变量必须放在项目根目录被忽略的 `.env`；不得将 key、provider 原始授权头或登录态复制到交付包。典型复现命令如下（替换本机 Godot 路径，输出写到新的目录）：

```powershell
python harness/run_provider_canary.py --provider seed_evolving --godot <godot.exe>
python harness/run_codex_eval.py --task-id task_004 --provider seed_evolving --godot <godot.exe> --output <new-run-directory>
```
