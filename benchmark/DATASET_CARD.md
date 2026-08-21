# GameVisualFix Pilot Dataset Card

## 概要

当前 P0 数据集包含 1 个自行构造的 repository-level 游戏视觉修复任务。它不是统计意义上的大型
Benchmark，而是用于验证完整评测链路和开展模型 trajectory case study 的受控 pilot dataset。

| 字段 | 值 |
| --- | --- |
| 任务数 | 1 |
| 主隐藏用例 | 10（5 个方向 × 2 个分辨率） |
| 额外回归 | 动态目标、Threat tracker、WASD、Objective completion、节点/布局、资产哈希 |
| 输入模态 | Godot repository + 初始 runtime PNG + 文本 Prompt |
| 输出 | Repository patch、trajectory、自动评分 |
| 领域 | 2D 游戏引擎视觉调试 |

## 数据构成

- `dataset.jsonl`：任务级索引，可直接展示或由 Harness 读取。
- `task_001/task.json`：冻结任务、输入哈希、预算和 evaluator 版本。
- `task_001/public/`：Agent 可见 Seed repository、Prompt 与初始截图。
- `task_001/private/evaluation_cases.jsonl`：Evaluator-only 的 10 个主测试用例。
- `task_001/private/`：reference patch、隐藏 suite、Oracle manifest 与 evaluator。

## 评价标签

- Functional Correctness：45 分。
- Visual Correctness：35 分。
- Regression Safety：20 分。
- `task_success=true` 仅在 build/integrity Gate 通过且三部分全部满分时成立。

## 已知限制

- 数据集只有一个合成任务，不能支撑统计显著性或通用模型排名。
- 任务补丁很小，模型可能猜中；视觉证据、对称 profile、多方向隐藏测试和 trajectory 用于解释结果。
- 本轮优先保证数据、Harness、模型调用、自动评分和报告完整走通；严格 OS/VM 级隔离作为后续增强项。
