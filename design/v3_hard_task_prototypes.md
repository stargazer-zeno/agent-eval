# GameVisualFix v3 Seed 能力边界原型设计

> Suite：`gamevisualfix_v3_seed_boundary_3x1`
>
> Engine：Godot 4.7.1 / Windows OpenGL Compatibility
>
> Provider：`doubao-seed-evolving` via Codex CLI + Seed Responses SSE normalizer
>
> 状态：在任何 v3 模型调用前冻结
> 统一预算：30 个 Controller actions、8 次 fresh observations、40 分钟

## 1. 设计动机与冻结边界

v2.1 中 Seed 的三条成功轨迹分别只有 5、4、3 个动作，都是一次编辑后观察并提交；T002/T003 甚至在首轮获得全量 public text snapshot 后直接写入。v3 不通过缩短预算、提高像素阈值或增加无意义上下文制造失败，而是引入三种真实能力耦合：跨图视觉对应、持久状态与延迟依赖、运行阶段变化与恢复。

Task 004–006 使用 `lazy_workspace`：初始 turn 只有本页冻结的 Prompt 与声明图片，Agent 必须使用 `list_files/read_file` 探索。Controller action schema 不变。Task 005/006 的阶段状态由 Agent workspace 外的受信 Controller 保存；hidden evaluator 总是从干净 State 0 重放。模型接触任务后不修改 Prompt、Bug、Oracle、阈值、预算或技术栈。

## 2. Task 004 — Glyph Atlas：Multi-View Landmark Registration

### 2.1 核心能力

测试 `Fine-grained Perception → Cross-image Correspondence → Spatial Reasoning → Tool Use`：Agent 必须在多个视角中识别无文字 5×5 glyph，恢复 8 个 landmark 的离散对应关系，并修复 camera rotation 与 portal parity 的连续空间变换。

### 2.2 Seed 预计失败原因

1. 只修 projection 而忽略 glyph permutation；
2. 把镜像后的 glyph 当成不同 identity；
3. 仅根据 baseline 过拟合固定 rotation/viewport；
4. 未获取旋转和镜像两类 fresh evidence 就提交；
5. 正确识别视觉关系，但在完整替换资源文件时破坏其他 binding。

### 2.3 初始环境

- 图片：`world_overview.png` 与 `broken_minimap.png` 两张；8 个地标/glyph 均无文字标签。
- Public 文件：Godot scene、`scripts/minimap/landmark_registry.gd`、`scripts/minimap/projection.gd`、`resources/landmark_bindings.tres`、公开 capture/smoke、匿名 glyph PNG。
- 工具：六个既有 Controller actions；公开 observation 为 `ROTATE_37`、`PORTAL_MIRROR`、`WIDE_VIEW`、`VERIFY_BASELINE`。
- 初始状态：binding 为固定 seed `24082401` 产生的 derangement；projection 错误地先反射 world vector 再应用 camera transform。

### 2.4 冻结 Agent Prompt

```text
The attached captures come from Glyph Atlas. Several minimap landmarks do not stay registered with their world landmarks across viewpoints. Repair the public Godot project so every minimap glyph preserves the correct landmark identity and spatial relationship under camera rotation, portal mirroring, and viewport changes.

The glyphs are intentionally unlabeled; the runtime images are the source of truth. Explore the repository through Controller actions, use the available public observation scenarios to disambiguate the defect, keep unrelated gameplay and assets unchanged, run the public smoke check, and inspect successful fresh post-patch observations before submitting. Do not hide markers, replace glyph art, disable camera/mirror behavior, move landmarks, or hardcode a scenario or resolution.
```

### 2.5 Ground Truth

1. 对照 world/minimap 图建立 8 个 glyph identity；
2. 通过 `ROTATE_37` 与 `PORTAL_MIRROR` 区分 permutation 与 transform-order；
3. 将 binding resource 恢复到 asset-hash 推导的唯一 mapping；
4. projection 先把 source/target 转入 camera-local space，再应用 portal parity，最后做 HUD clamp；
5. smoke 后至少验证一个 rotation 和一个 mirror 场景；
6. 所有 hidden states 保持动态更新。

### 2.6 关键视觉证据与 Caption Gate

唯一 identity 只编码在 5×5双色 bit pattern、镜像后的对应关系和跨图位置中。代码只含匿名 slot，普通 Caption“八个不同符号中部分对应错误”无法表示 bit pattern；移除图片后仍有至少 8 个行为合理候选。只有把像素级答案直接抄进 Caption 才能消除不确定性，该行为视为答案泄漏而非 caption replacement。

### 2.7 预期轨迹

`Observe initial pair → list/read registry/bindings/projection → Observe ROTATE_37 → Observe PORTAL_MIRROR → write binding → write projection → run_smoke → Observe rotation → Observe mirror → submit`

### 2.8 失败模式

- permutation-only 或 transform-only partial fix；
- mirror parity 重复/遗漏；
- identity 正确但方向/位置错误；
- hardcode camera angle/viewport；
- 修改或隐藏 glyph asset。

### 2.9 自动评测

- Build/import 为硬门槛；失败为 0。
- Functional 45：8 个 binding 20 分，transform composition 20 分，动态更新 5 分。
- Visual 35：6 rotation × 2 parity × 3 viewport，根据独占颜色与 glyph bitmask 同时验证 identity、中心和方向。
- Regression 20：player/camera、非目标节点、布局、landmark 与全部 PNG hash。
- `task_success=true` 仅在三类 mandatory checks 全通过。部分修复保留分项分数但 task failure。

### 2.10 扩展方式

用固定生成器改变 glyph codebook、derangement、D4 transform、landmark graph、camera rotation 与 viewport；要求 glyph 之间 Hamming distance ≥ 8，且任意 rotation/reflection 后不相等，可扩展 100–500 条。

## 3. Task 005 — Checkpoint Mosaic：Delayed Save-Migration Chain

### 3.1 核心能力

测试 `Visual Evidence → Multi-step Execution → Persistent State Tracking → Delayed Dependency`：Agent 需要逐阶段修复一次 v1→v2 内容迁移，并在最终阶段复用只在初始 Lobby 图出现的视觉 seal 顺序。

### 3.2 Seed 预计失败原因

1. 在长轨迹中丢失早期 seal mapping；
2. 错误理解 `ADVANCE` 未推进的状态回执；
3. 把 route、save migration、HUD restore 当成互不相关的三个局部 Bug；
4. 修改当前 checkpoint 后破坏新存档或重复加载；
5. 最终根据最近一张图猜测，而没有联合初始图与 state telemetry。

### 3.3 初始环境

- 图片：`lobby_initial.png` 一张，四扇门由无文字 5×5 seal 标识。
- Public 文件：route graph、v1/v2 schema、save migrator、HUD restore hints、三个 checkpoint scene、capture/smoke。
- Controller state：`LOBBY → RESTORED_MIDPOINT → POST_ELEVATOR → FINAL_RESTORE`，保存在 workspace 外。
- Observation：`REPLAY_CURRENT` 不推进；`ADVANCE` 运行当前 workspace 的确定性 replay，成功才推进并返回新 PNG 和 state receipt。

### 3.4 冻结 Agent Prompt

```text
Checkpoint Mosaic regressed after a level-content and save-schema migration. Starting from the attached Lobby capture, repair the public Godot project so an old save can follow the intended visual route, restore through every checkpoint, and show the correct HUD hint without breaking new saves or repeated loads.

The door seals are intentionally unlabeled and the images are the source of truth. Runtime progress persists across Controller observations. REPLAY_CURRENT reruns the current checkpoint; ADVANCE attempts the deterministic route and advances only when the current stage behaves correctly. Track what you learn across stages, inspect relevant files, make the required repository changes, run public smoke checks, and complete the full chain before submitting. Do not bypass progression, delete or rewrite the supplied save, display every hint, or hardcode one viewport or public replay.
```

### 3.5 Ground Truth

1. 从 Lobby 图记录四个 seal 的 screen order 与 door relation，修 route binding；
2. `ADVANCE` 到 `RESTORED_MIDPOINT`；
3. 联合 state receipt、v1 schema 与新截图修正 1-based legacy slot 到 v2 stable scene ID 的 migration；
4. 推进到 `POST_ELEVATOR`；
5. 使用 Lobby seal 顺序与恢复后的 active stable ID 修 HUD hint selection；
6. 推进 `FINAL_RESTORE`，验证旧存档、新存档和重复加载，smoke 后提交。

### 3.6 关键视觉证据与 Caption Gate

seal bit pattern、Lobby screen order、midpoint 中保留的 seal 与 final HUD 图案构成跨阶段唯一约束。代码中四个 candidate permutation 都满足 schema；普通 Caption 不编码这些图案，移除图片后至少存在 24 个等价候选。

### 3.7 预期轨迹

`Observe Lobby → read route/schema → write route → ADVANCE → Observe Midpoint → read migrator → write migration → ADVANCE → Observe Post-Elevator → read HUD restore → revisit early evidence mentally → write HUD logic → smoke → ADVANCE → Observe Final → submit`

### 3.8 失败模式

- 只完成第一个 checkpoint；
- overwrite save 或强制 progression；
- legacy/new save off-by-one；
- 忘记早期 seal order；
- 重复 ADVANCE 而不根据失败图改变 patch。

### 3.9 自动评测

- Functional 45：三个 checkpoint gate 各 15 分。
- Visual 35：Lobby route、midpoint restored seal、post-elevator hint、final hint 的 bitmask/位置；分配 9/9/8/9。
- Regression 20：新存档 5、旧存档重复加载 5、player/scene position 5、nodes/assets/hash 5。
- hidden evaluator 从干净 old/new saves 重放，不信任 Controller session；删除 save、跳阶段、全提示、prototype-seed hardcode 均被拒绝。

### 3.10 扩展方式

生成不同 route graph、seal codebook、schema version delta、checkpoint depth、延迟引用距离和恢复 layout，形成 50–300 条任务；每条保留可计算的 stage oracle 与 candidate entropy。

## 4. Task 006 — Mirrorstorm：Phase-Changing Telegraph Recovery

### 4.1 核心能力

测试 `Execution → Runtime State Change → Detection → Diagnosis → Multi-file Recovery`。核心不是单一视觉 offset，而是事件时序、coordinate parity 与 object-pool epoch 的一致 sample contract。

### 4.2 Seed 预计失败原因

1. 修复 CALM 后忽略 MIRRORED/INTERRUPTED 新 evidence；
2. 只改 parity，不改 tick/epoch；
3. 把 pool stale state 当成固定视觉 offset；
4. fresh observation 暴露失败后仍提交；
5. 多文件恢复修复引入 damage timing 或 pool-size 回归。

### 4.3 初始环境

- 图片：`calm_cw_contact_sheet.png`，8 帧带帧号 contact sheet。
- Public telemetry：tick/signal/epoch trace，不含视觉坐标答案。
- Public 文件：attack controller、telegraph sample、renderer、pool、replay/capture/smoke。
- Controller state：`CALM → MIRRORED_ENRAGED → INTERRUPTED_RESUME`。
- Observation：`STEP_FIGHT` 推进，`REPLAY_CURRENT` 保持当前 phase。

### 4.4 冻结 Agent Prompt

```text
Mirrorstorm's boss telegraphs intermittently disagree with the attack after the fight changes phase. Diagnose and repair the public Godot project using the attached CALM contact sheet, the public runtime trace, repository inspection, and fresh Controller observations.

The fight continues when STEP_FIGHT is observed and may expose a different runtime state; REPLAY_CURRENT repeats the current phase. Preserve attack timing, mirroring, interruptions, visibility, and pool limits. Inspect the evidence after each meaningful change and repair the underlying state-transfer contract rather than hiding the telegraph, freezing progression, disabling mirroring, moving the boss, or hardcoding phases.
```

### 4.5 Ground Truth

1. 联合逐帧 signed position 与 trace 定位 signal/sample 边界；
2. 在 movement/arena state commit 后创建不可变 sample，携带 tick、epoch、arena-local position/facing/parity；
3. renderer 与 pool 只消费 sample，不 deferred-read live nodes；
4. pool checkout/reset 校验 epoch 并清除 stale visual state；
5. 依次观察 mirrored 和 interrupted phase，必要时根据新 evidence 修订；
6. smoke、replay final phase、submit。

### 4.6 关键视觉证据与 Caption Gate

contact sheet 的 telegraph 尖端 signed position、handedness、alpha 出现/消失帧与 arena asymmetry 必须和 trace tick/epoch 联合。普通 Caption“残影方向偶尔错误”无法定位是 pre-commit、parity 还是 stale pool；无图保留三个合理根因。

### 4.7 预期轨迹

`Observe CALM + read trace → read controller/sample/renderer/pool → patch sample boundary → STEP_FIGHT → Observe MIRRORED → diagnose remaining parity/epoch → revise multi-file patch → STEP_FIGHT → Observe INTERRUPTED → run_smoke → REPLAY_CURRENT → submit`

### 4.8 失败模式

- CALM-only fix；
- double mirror；
- tick/facing 来自不同 frame；
- stale pooled telegraph survives interrupt；
- 清空/禁用 pool 或 telegraph 规避视觉失败。

### 4.9 自动评测

- Functional 45：tick/sample consistency 15、arena/parity 15、epoch/pool lifecycle 15。
- Visual 35：方向、mirror、30/60 tick、interrupt/pause 的 contact-sheet pixel geometry、alpha 与 cleanup frame。
- Regression 20：boss progression/damage 5、timing 5、pool bound 5、nodes/assets 5。
- 完全成功要求所有 phase mandatory checks 通过；一次性正确架构修复允许成功且 Recovery=N/A。

### 4.10 扩展方式

组合 phase graph、coordinate transform、signal ordering、pool reuse、interrupt/pause 和 replay rate，形成 50–200 条任务；生成器必须保持 deterministic fixed-tick oracle。

## 5. 自审、实验和论文边界

| 任务 | Seed难度 | Visual Necessity | Tool-use | Long-horizon | 状态管理 | 自动评测 | 规模化 | 创新价值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T004 | 5 | 5 | 4 | 4 | 4 | 5 | 5 | 5 |
| T005 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| T006 | 5 | 5 | 5 | 5 | 5 | 5 | 4 | 5 |

进入 Seed 前，每题必须通过 clean-copy import/smoke/全部 public transition、Bug 三次稳定失败、Oracle 三次 100、截图与 state ledger 稳定、caption/no-image ambiguity、public leak audit、shortcut rejection 和非 byte-identical 等价补丁。Seed 每题一个 valid attempt；模型错误不重跑，独立基础设施故障最多一次 fresh rerun。

若 Seed 三题全部失败，优先扩展 T005 的 stateful visual save-migration family。若 Seed 仍成功，不回调已冻结任务；下一轮增加状态图分支、跨版本组合和反事实 replay 多样性。论文潜力暂定位为“stateful visual software-engineering agents”，不在完成相邻工作检索前声称首创。
