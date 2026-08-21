# Task 001 验证记录

## 验证结论

Task 001 已通过进入模型实验所需的确定性验证。当前 Bug State 在三次独立 clean-copy 运行中均为 `20/100`、`task_success=false`；应用 reference patch 后三次均为 `100/100`、`task_success=true`。每次运行生成 10 张主测试截图和 1 张动态回归截图，两种状态各 33 张截图在对应 case 间 SHA-256 完全一致。

机器可读的逐项数据见 `validation/results.json`，10 个主视觉 case 的定义见 `private/evaluation_cases.jsonl`。

## 环境与评价规则

- Engine：Godot `4.7.1.stable.official.a13da4feb`。
- Renderer：Windows display server + OpenGL Compatibility；窗口隐藏且移出可见桌面区域。
- 主矩阵：`E`、`N`、`W`、`S`、`NE` 五个方向，分别在 `960×540` 与 `1280×720` 下运行，共 10 cases。
- Functional Correctness：45 分；Visual Correctness：35 分；Regression Safety：20 分。
- Build/integrity 为硬门槛；三类 mandatory tests 必须全部通过，累计分数不能补偿任何一类失败。
- 视觉方向以箭头独占尖端颜色估计，预测单位向量与目标单位向量点积阈值为 `0.98`。

## Canonical 重复性结果

| State | Run 1 | Run 2 | Run 3 | task_success |
| --- | ---: | ---: | ---: | --- |
| Bug | 20/100 | 20/100 | 20/100 | 三次均 false |
| Oracle | 100/100 | 100/100 | 100/100 | 三次均 true |

Bug 状态只保留完整的 20 分回归分；Objective Tracker 在全部主 case 中方向错误。Oracle 状态的功能、视觉和回归三部分全部满分。评价结束后没有残留 Godot 进程。

## Shortcut 拒绝结果

| 错误或投机补丁 | Diagnostic score | Reported score | 拒绝原因摘要 |
| --- | ---: | ---: | --- |
| 替换受保护图片资产 | 64 | 0 | integrity gate 失败 |
| 翻转共享方向算法 | 55 | 55 | Threat/视觉回归失败 |
| 隐藏 Objective Tracker | 63 | 63 | 视觉与可见性条件失败 |
| 缩放 Objective Tracker | 65 | 65 | 视觉契约失败 |
| 固定为单一方向 | 17 | 17 | 多方向功能与视觉失败 |
| 移动/替换目标关系 | 6 | 6 | 功能与回归失败 |
| 修改错误的 Threat profile | 10 | 10 | Objective 未修复且 Threat 回归失败 |

`threat_edit` 首次执行时 mutation 未实际写入 workspace，因此旧结果只是 Bug baseline。该 setup-invalid 产物被保留在本地验证缓存；修正 setup 后以新输出目录 `result_r2` 重跑，上表和 `validation/results.json` 仅采用有效的 10/100 结果。

## 泄漏与隔离检查

- Agent 可见目录仅包含 public Godot project、冻结 Prompt、初始截图和公开 smoke/capture helper。
- Reference patch、正确值、隐藏场景、case manifest 与 evaluator 均位于 private/control 区域，不应复制到模型 workspace。
- Prompt 不透露错误对象、错误文件、错误类型或正确数值。
- 本任务是 1 个合成 case 的 pilot dataset，只支持端到端工程可行性和 trajectory case study，不支持统计显著性、通用排名或广泛能力结论。

## 已知边界

严格 `--headless` 在当前 Windows Godot build 下无法产生真实 viewport 像素，因此评价与 fresh observation 使用用户批准的隐藏窗口渲染。该方案已在当前宿主环境重复验证，但迁移到锁屏、RDP、VM 或其他 GPU/驱动环境时必须重新执行 preflight。
