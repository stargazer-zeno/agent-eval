# GameVisualFix v2.1 Dataset Card

## 概要

GameVisualFix v2.1 包含 3 个自行构造的 repository-level Godot 视觉修复任务，用于评估 Coding Agent 能否完成“运行时视觉证据、代码定位、仓库修改、fresh observation 与隐藏评测”的闭环。它是可复核的小样本评测集，不是统计意义上的大型 Benchmark。

| 字段 | 值 |
| --- | --- |
| 任务数 | 3 |
| 难度 | Easy / Medium / Hard |
| 主隐藏用例 | 40（T001 10、T002 18、T003 12） |
| 输入模态 | Godot repository + 初始 runtime PNG + 文本 Prompt |
| 输出 | Repository patch、脱敏 trajectory、自动评分 |
| 领域 | 2D 游戏引擎视觉调试 |
| 正式 suite | `gamevisualfix_v2_1_seed_proxy_3x2` |

## 任务构成

| Task | 名称 | 目标 | 隐藏条件 |
| --- | --- | --- | --- |
| T001 | Signal Courier | HUD tracker calibration | 5 个方向 x 2 个 viewport，加动态目标、输入、布局和资源回归 |
| T002 | Orbit Relay | camera-space edge tracker | 3 个 rotation x 2 个 zoom x 3 个 viewport，加 camera/player 回归 |
| T003 | Echo Dash | trail phase synchronization | 6 个 replay x 2 个 physics rate，加方向切换和中断检查 |

每个 `task_00x/public/` 是 Agent 可见 workspace，包含任务描述、代码、资源和初始证据；`task_00x/private/` 包含 reference patch、隐藏 case、Oracle 和 evaluator，仅在 Agent 结束后用于评分。每题的冻结配置位于对应 `task.json`。

`dataset.jsonl` 提供三题的机器可读索引。T001 最初作为 Pilot 建立，因此其内部 revision/split 字段保留历史命名；v2.1 正式 suite 使用冻结后的同一任务内容，不修改 Oracle 或评分阈值。

## 评价标签

- Functional Correctness：45 分。
- Visual Correctness：35 分。
- Regression Safety：20 分。
- `task_success=true` 仅在完整性 Gate 通过且三部分全部满分时成立。

评分同时记录 action、fresh observation、wall time、token telemetry、terminal status 与 failure class。可复现的 Provider/CLI/Controller/renderer/evaluator 故障归为 `invalid_infrastructure`，与 timeout、错误 action、错误 patch 或低分等有效模型结果分离。

## 完整性与发布

- 正式运行从 public seed 创建独立 workspace，不向 Agent 暴露 private evaluator、Oracle 或其他模型结果。
- 发布轨迹只保留去 reasoning、去模型正文的 action/observation hash-chain。
- `.env`、凭据、run-local workspace、Provider 原始流和 reasoning 正文不进入发布树。
- v2.1 正式结果见 `results/v2_1_seed_proxy_scores.json`；旧 Pilot/v2 仅作为历史摘要和 lineage。

## 已知限制

- 每个模型只有 3 题、每个 Provider/Task 只有一次有效 canonical attempt，不支持显著性检验或普遍排名。
- 6 个正式结果中 5 个满分，存在 ceiling effect。
- 任务补丁和仓库规模较小，重点是隔离视觉诊断与 runtime verification，不代表完整游戏开发能力。
- 当前只覆盖单机 Windows、Godot 4.7.1 和固定 Harness；跨引擎、跨平台与多次独立运行留待后续扩展。
