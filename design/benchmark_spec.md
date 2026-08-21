# GameVisualFix Task 001 Benchmark Specification

> Task：`Signal Courier — Twin Tracker Calibration`
>
> Revision：`task_001_v1`
>
> 冻结日期：2026-08-21
>
> 状态：在模型接触任务前冻结

## 1. 目标与结论范围

Task 001 是一个自行构造的小型 Godot 4 repository-level visual repair。它用于观察 Coding Agent 能否：

1. 从 runtime screenshot 识别一个 Tracker 与场景空间关系不一致；
2. 在多文件/资源仓库中区分共享方向算法与 per-profile visual calibration；
3. 实施小而稳健的修复并保持原有行为；
4. 在 Patch 后请求和解释 fresh runtime screenshot；
5. 若验证失败，是否改变 hypothesis、定位或编辑并恢复。

本轮只运行一个 Codex pilot。它可以验证 Task、Harness、Oracle 与单条 trajectory 的可审计性，不能回答 Seed 与外部模型的总体强弱，也不支持因果、统计显著或宽泛首创结论。

## 2. Repository 与 Bug

`Signal Courier` 是固定状态的 top-down 2D 场景：

- 逻辑 viewport 为 960×540；
- 蓝色 Player 位于画面中部；
- 黄色 Objective Beacon 位于 Player 东方；
- 红色 Threat Drone 位于 Player 西北方；
- HUD 分别显示 Objective tracker 与 Threat tracker；
- WASD、Objective completion、两个目标绑定与共享方向计算均正常。

两个 Tracker 使用同一个公式：

```text
sprite_rotation = direction_to_own_target.angle() + profile.art_forward_offset
```

两张项目自制 PNG 的原生 forward 相反：

| Tracker | Native forward | Correct offset | Bug-state offset |
| --- | --- | ---: | ---: |
| Objective | `Vector2.RIGHT` | `0.0` | `PI` |
| Threat | `Vector2.LEFT` | `PI` | `PI` |

因此初始画面中 Threat 正确指向西北，Objective 稳定反向指向西。Bug 是 Objective profile calibration error，不是 target binding 或共享算法错误。

## 3. Exact Agent Prompt

两模型未来必须使用以下完全相同的英文 Prompt；Codex pilot 也使用这一版本：

```text
Players report a visual inconsistency in the two HUD trackers. Use the attached runtime screenshot as the primary bug evidence.

Diagnose the root cause in this existing Godot project and implement the smallest robust fix. Both tracker types must continue to point toward their own tracked world object as targets move, at different directions and window sizes. Preserve existing game behavior and committed image assets.

After a candidate patch, request a fresh runtime observation from the harness and inspect it. If the fix is incomplete, use that new evidence to revise your diagnosis and patch. You may run the provided public checks.

Do not modify the task evidence or tests. Keep the patch focused. When you need a new screenshot, return action "observe". When the task is complete, return action "submit" with a brief summary of checks performed.
```

图片说明固定为中性文本：`Runtime screenshot captured from the current buggy build.` Prompt 不出现错误 Tracker、文件、resource、offset、PNG 原生朝向、正确数值或 reference patch。

## 4. Input 与隔离

### 4.1 Agent-visible

- 上述 Prompt；
- 仅含 Bug State 的 sanitized single-commit repository；
- 初始 960×540 runtime screenshot；
- scenes、scripts、resources 和两张自制 PNG；
- 运行/公开检查说明与不泄露答案的 visible smoke tests；
- Controller 提供的 `observe` / `submit` 响应协议。

### 4.2 Evaluator-only

- reference patch、正确 offset/native-forward manifest；
- hidden scenarios、hidden evaluator、scoring config；
- expected semantic markers、protected asset hashes；
- research/design/report、作者 Git history、remote 与 `.env`；
- 其他模型的 prompt、trajectory 和结果。

Agent workspace 不得通过 sibling path、Git objects、环境变量、网络或日志读取 private artifacts。

## 5. 固定环境

- Godot：`4.7.1.stable.official.a13da4feb` official Windows x86-64 standard build；
- Display：真实 `Windows` display server，受控 hidden background window；
- Rendering driver/method：`opengl3` / `gl_compatibility`；
- VSync：关闭；physics/render cadence：固定 60 FPS；
- Viewports：960×540 和 1280×720；
- 随机性：禁用；每个 capture 使用新进程、新 render copy 和独立临时 `user://`；
- 截图：等待固定 warm-up frames 与 `RenderingServer.frame_post_draw` 后读取 root Viewport；
- 网络：Agent shell 与 renderer 均禁用；
- Controller：串行运行、固定 hidden-window policy、超时后清理完整进程树。

Rev.2 环境证据见 [Godot preflight](./godot_preflight_rev2.md)。窗口曾短暂取得 foreground 是已知限制；只要图片重复性不受影响，它作为 Harness telemetry 记录，不改变评分。

## 6. Agent 工具与动作

Codex 通过统一 CLI Harness 获得文件检索、读取、`apply_patch`、terminal 和初始图片能力，不提供 web、MCP、plugin、skill、subagent 或 private filesystem。公开 Godot smoke test 可在 workspace 内运行。

每个 turn 的最终响应必须符合：

```json
{
  "action": "observe | submit",
  "summary": "observable work and checks only"
}
```

- `observe`：Controller 冻结当前 tree hash，复制到新的 render directory，以 trusted runner 生成 fresh PNG；成功则通过同一 thread 的 `resume --image` 注入，失败则只返回公开 build/capture stderr。
- `submit`：冻结最终 diff，结束 Agent session，再在 Agent 不可访问的 evaluator copy 中运行 hidden tests。
- evaluator-only screenshot 永不回流 Agent，不计为 fresh observation。

## 7. Expected Workflow

```text
Initial screenshot O0
→ Visual hypothesis
→ Repository exploration/localization
→ Candidate patch P1
→ observe request
→ New process + fresh screenshot O1
→ Verification
→ [if incomplete] revised hypothesis/location/edit
→ P2 and another observation
→ submit
```

每个 observation receipt 必须包含当前 workspace tree SHA-256、Godot version/exe hash、scenario、viewport、进程时间/exit code、PNG hash 与 stdout/stderr hash。复用旧图、只生成未注入、或 evaluator 私下截图都不构成闭环。

## 8. Ground Truth 与 Reference Patch

行为 Ground Truth：在五个方向和两个分辨率下，两种 Tracker 的最终可见 forward 均指向各自原目标；动态更新、edge clamp、HUD、控制、Objective completion 与资产保持不变。

Reference patch 只修改 Objective profile：

```diff
-art_forward_offset = 3.1415927
+art_forward_offset = 0.0
```

Evaluator 接受行为等价 Patch，不要求 byte-for-byte diff；任何等价方案仍须通过完整性、功能、视觉和回归全部 mandatory gates。

## 9. 自动评价

### 9.1 Build / integrity hard gate

项目必须由固定 Godot 正常 import/launch，无 parse error、缺失资源或必要节点。task evidence、visible tests、protected assets 和 evaluator contract 不得被修改。Gate 失败时总分为 0，`task_success=false`。

### 9.2 Functional Correctness：45

Objective 在 `E / N / W / S / NE` 五个方向与两个 viewport 下共 10 cases。每 case 4.5 分，同时要求：

- Objective tracker 仍绑定原 Objective；
- tracker 和 profile 存在、方向向量非零；
- `dot(actual_visible_forward, target_direction) >= 0.98`；
- 目标移动后下一帧继续更新，而不是为 baseline 写死。

### 9.3 Visual Correctness：35

同一 10-case 矩阵各生成一张 runtime PNG，每张 3.5 分。Evaluator 使用自制 PNG 中独占的 center/tip marker colors，从实际渲染像素恢复 forward vector，并要求：

- Objective 与 Threat 两个 Tracker 均可见；
- tip/body/center 像素数量在冻结范围内；
- 两者 visual forward 与各自目标方向的 dot 均 `>= 0.98`；
- HUD 位置、scale、alpha 与遮挡检查通过。

不以整图 exact hash 或自由 VLM judge 作为 mandatory Oracle。

### 9.4 Regression Safety：20

| 检查 | 分数 |
| --- | ---: |
| Threat 在 10-case 矩阵保持正确 | 10 |
| 两个目标运行中改变位置后仍动态跟随 | 4 |
| 两个 viewport 的 edge clamp、可见性和 HUD 布局 | 2 |
| 两张 PNG SHA-256 不变 | 2 |
| 启动、WASD、Objective completion、必要节点 | 2 |

### 9.5 Primary success

```text
task_success =
  integrity_gate_pass
  AND functional_score == 45
  AND visual_score == 35
  AND regression_score == 20
```

总分只用于诊断，不能用部分得分补偿 mandatory failure。

### 9.6 Shortcut rejection

隐藏测试必须拒绝：翻转共享算法、修改 Threat profile、交换 target/texture/profile、重画或旋转 PNG、隐藏 Tracker、移动目标迁就箭头、写死 baseline/viewport，以及只修改 evidence 或 tests。

## 10. Multimodal Necessity Gate

正式运行前确认：

- Prompt、命名、注释和 visible tests 不泄露 Objective、offset 或正确值；
- 不看 screenshot/PNG/runtime pixels 时，共享算法、Objective calibration、Threat calibration 和 binding 至少是多个合理解释；
- 初始 screenshot 提供 Threat 正确而 Objective 反向的区分证据；PNG pixels 提供两种 native forward 相反的证据。

该 Gate 只证明本任务接口下视觉信息具有非冗余诊断价值，不证明普遍或因果必要性。本轮不运行 no-image ablation。

## 11. Contamination Check

- Task、代码和素材均由本项目自行创建，不复制 OpenBenchmark、GameDevBench 或 GameCraft-Bench 实例；
- 模型运行前检索精确标题、Prompt 长短语和关键代码片段；若发现实质同源实例则停止；
- 模型接触任务前不公开 agent-visible package，运行时移除 remote、压平 Git history 并关闭网络；
- private artifacts 即使存在于作者仓库，也不复制到 Agent workspace。

## 12. Pilot 预算

| 资源 | 上限 |
| --- | ---: |
| Controller turns | 4（initial + 最多 3 resume） |
| Agent-visible fresh screenshots | 3 |
| Codex wall time | 25 分钟（10 + 5 + 5 + 5） |
| 完整 run hard deadline | 35 分钟 |
| Command execution events | 60 |
| Public capture | 每次 90 秒 |
| Hidden evaluator | 180 秒 |
| Telemetry input-token gate | 150,000 |
| Telemetry output-token gate | 20,000 |

CLI 无法在 turn 中途硬切 token；Controller 在每个 `turn.completed` 后检查 usage。wall time、turn、command 与 screenshot 是硬限制。超限属于有效 `budget_exhausted`，不得免费重跑。

## 13. Valid / Invalid Run

以下是有效模型失败：拒绝或无 Patch、错误命令、Agent 修改导致 Godot/capture 失败、未请求 observation、超时/预算耗尽、错误提交、hidden tests 失败。首轮成功同样有效，Recovery 记 `N/A`。

只有 Seed/Prompt/image/model/config hash 错误、provider/CLI/Controller crash、日志写入损坏，或 capture/evaluator 在不可变 Seed/Oracle fixture 上也失败，才是 `invalid_infrastructure`。最多允许一次 Harness-only 修复与全新 session 重跑；必须保留首次运行，不能择优。第二次 infrastructure invalid 即停止。

模型看过任务后若发现 Prompt 歧义、Oracle 错误或阈值缺陷，属于 Benchmark defect：归档 v1 并停止，不能原地调题后继续比较。

## 14. Trajectory 标签

实验前冻结 `Perception / Localization / Editing / Verification / Recovery` 的 observable-evidence 定义。每阶段只取 `Pass / Fail / Ambiguous / N/A`；Recovery 仅在首次 Patch 有可验证失败后评价。最终 evaluator 回答“是否做对”，trajectory 只解释原因，模型自述和不可见 chain-of-thought 不作为成功证据。
