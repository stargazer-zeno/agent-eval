# GameVisualFix v3 Seed trajectory Case Study

Suite: `gamevisualfix_v3_seed_boundary_3x1`. 本文只引用 Controller action、fresh image/state receipt、最终 patch 与隐藏 evaluator；不引用模型自述或不可见 reasoning。

## 结果总览

| Task | Terminal | Actions | Fresh observations | F | V | R | Total | Success |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| T004 Glyph Atlas | model turn timeout | 11 | 4 | 5 | 0 | 20 | 25 | false |
| T005 Checkpoint Mosaic | action budget exhausted | 29 | 5 | 30 | 0 | 20 | 50 | false |
| T006 Mirrorstorm | submitted | 16 | 2 | 45 | 35 | 20 | 100 | true |

主指标为 `Task Success Rate = 1/3 = 33.3%`，三题平均总分为 `58.333`。这只是单模型、单次有效 attempt 的描述性结果。

## T004：证据齐全，但没有进入 Editing

- **Perception — Observed**：初始两图已注入；Step 7、9、10、11 又分别观察 `VERIFY_BASELINE`、`ROTATE_37`、`PORTAL_MIRROR`、`WIDE_VIEW`，四次 capture 均成功。
- **Localization — Observed**：Steps 2–6、8 读取了公开工程中的 registry、binding、projection 与相关文件。
- **Editing — Not observed**：有效 canonical trajectory 没有 `write_file`，最终 patch 为空。
- **Verification — Pre-patch only**：四张 fresh image 都来自未修改 workspace，不能算 Patch 后验证。
- **Recovery — N/A**：没有首次补丁，也没有 Patch 后失败证据可供恢复。

Step 12 的模型回合达到 240 秒上限，终止为 `model_turn_timeout`。隐藏 evaluator 仍正常完成 36 个 case，Bug 工程得 `F=5, V=0, R=20`。因此该结果说明 Seed 在跨图证据整合后未及时转化为工具编辑；它不能单独证明视觉对应本身失败。

首次 Task 004 运行在 Step 12 写入了一个仅修改 projection 的补丁，随后第 13 次 resume 发生上下文超窗型 transport failure，记为 `invalid_infrastructure`，其 45/100 不进入主结果。该 lineage 促成了早期自动 compact 的 Harness 修复，但不会替代 canonical 分数。

## T005：出现真实恢复，但延迟依赖未闭环

- **Perception — Observed**：Step 9 首次 `ADVANCE` 返回 `LOBBY -> LOBBY, advanced=false`；后续 fresh images 继续反映当前持久状态。
- **Localization — Observed with inefficiency**：失败后 Seed 回到文件读取，但 Steps 11、15 请求了不可读路径，Steps 12–13 重复列目录，Step 14 返回 `invalid action schema`。
- **Editing — Observed**：Steps 17–19 首次修改三个文件；Step 21 再次推进仍失败。Steps 22、24–26 继续修改，构成基于失败回执的实际修订。
- **Verification — Partial**：Step 20、27 smoke 均运行；Step 28 终于得到 `LOBBY -> RESTORED_MIDPOINT, advanced=true`，Step 30 在 midpoint 做了 `REPLAY_CURRENT`。
- **State Tracking — Partial**：运行到达 midpoint，但没有通过 `RESTORED_MIDPOINT -> POST_ELEVATOR`，更未验证 `FINAL_RESTORE`。
- **Recovery — Observed**：两次 Lobby 失败后，Seed 改变了文件内容并最终通过第一阶段。这是动作与回执支持的恢复，不依赖模型自述。

最终 patch 正确修复了 Lobby `route_order` 和最终 `RESTORED_HINT_ORDER`，但 `V1_TO_V2` migration 表仍保持初始值。隐藏评价因此为 route=true、migration=false、hint=true，得到 `F=30, V=0, R=20`。Visual 是 mandatory 全链 Gate，不能由两个局部正确表补偿。该轨迹直接暴露了延迟依赖：模型保留了早期视觉顺序，却在中间迁移状态上失败，并因 30-turn 循环耗尽而无法继续。

## T006：一次性架构修复，Recovery 不适用

- **Perception — Observed but limited**：模型收到初始 8-frame contact sheet；Step 14 推进到 `MIRRORED_ENRAGED`，Step 15 在同一 phase 重放。没有公开观察 `INTERRUPTED_RESUME`。
- **Localization — Observed**：Steps 2–8 读取 attack、sample、renderer、pool、trace 与相关文件。
- **Editing — Observed**：Steps 9–12 分别修改四个逻辑组件。
- **Verification — Observed**：Step 13 smoke 通过；Steps 14–15 提供 Patch 后 mirrored fresh evidence；Step 16 submit。
- **State Tracking — Partial**：公开 trajectory 只到 mirrored phase，但隐藏 evaluator 独立覆盖全部三 phase、两种 tick rate 和两个方向。
- **Recovery — N/A**：第一版补丁已通过全部 12 个隐藏 case，没有 Patch 后失败再诊断的机会。

最终补丁把 sample 移到 movement commit 后，补齐 position/facing/parity/epoch，禁止 renderer 重新读取 live state，并修复 pool epoch/reuse。隐藏评分为 `100/100`。这证明 evaluator 能接受行为等价修复，但也暴露原型难度不足：公开常量名和注释过于直接地表达了目标架构，Seed 不需要进入 interrupted phase 就能一次性补齐契约。

## 跨任务结论

T004 的边界出现在从视觉整合到及时编辑；T005 的边界出现在错误恢复后的持久状态与延迟迁移；T006 未触及边界。三者中，T005 提供了最强的阶段诊断信号：失败不是单一 0 分，而是可定位到 `migration` Gate，并有可审计的失败—修改—部分推进链。
