# GameVisualFix

GameVisualFix 是一个面向游戏开发场景的 Multimodal Coding Agent Evaluation 项目，关注模型能否利用截图或运行时视觉状态，完成从观察、代码定位、修改、运行验证到失败恢复的开发闭环。

> 当前定位是待研究和实验验证的项目假设，不是已经由文献或实验支持的结论。

## 当前状态（2026-08-21）

端到端 Pilot 已完成：Task 001 数据集、10 个隐藏主 case、100 分制自动 evaluator、真实多 provider 调用、trajectory、结果对比和最终报告均已产出。有效结果包括本地登录 Codex `gpt-5.6-sol` **100/100、成功**、Seed Evolving via Codex compatibility run **100/100、成功**，以及 Qwen **42/100、失败**。本地 Codex 与 Seed 成功 run 使用相同 public text/图片预载和 Controller action 包装；Qwen 使用逐步探索，因此结果适合作为 qualified case comparison，不构成严格模型排名。详见 [`report/final_report.md`](report/final_report.md)。

## 要求基线

### HR 强制要求

- 在游戏开发、嵌入式开发、算法开发或网络安全中选择一个真实开发场景，设计一道原创 Coding Agent 任务，不直接使用 OpenBenchmark 已有题目。
- 任务必须基于代码仓库执行，要求 Agent 阅读和检索代码、定位文件、修改实现，并在需要时运行测试或调试，而不是只回答代码问题。
- 至少评测 Seed 模型和一个外部模型；尽可能统一 Agent Harness、Prompt、工具权限和运行环境，以减少混杂变量。
- 给出可复核的评测过程、评分指标、两个模型的分数及强弱差异，并分析代码理解、定位、多文件修改、工具调用、Debug、恢复和最终正确性等能力。
- 主要交付一份完整评测文档；代码仓库可作为附件，但不是强制要求。

### HR 建议项

- 将 Functional Correctness 作为主要指标，用过程指标解释模型为何成功、失败或低效。
- 将总分拆分为 Task Success、Functional Correctness、Code Quality、Agent Process、Debug / Recovery 和 Efficiency 等维度。
- 报告覆盖任务背景、Repository / 环境、任务描述、Agent 配置、评测协议、实验过程、得分、Case Study、能力差异和结论。

### 本项目自选方向

- 选择游戏开发场景，暂定项目名称为 **GameVisualFix**。
- 研究截图或运行画面能否成为定位 Bug 所必需的证据，而不仅是最终结果展示。
- 探索 `Visual Observation → Localization → Patch → Runtime Verification → Recovery` 的闭环评测，以及过程级错误传播分析。
- 上述方向需要先经过文献调研、Research Gap 分析和最小任务验证，不能预设为创新点或实验结论。

## P0 交付物

一天内优先完成一个小而完整、可复现的评测闭环：

1. 1 个经过人工 Oracle 验证的游戏 Coding Agent 任务；
2. Seed 模型与 1 个外部模型的受控对比实验；
3. 自动评分、功能与视觉正确性验证、回归检查；
4. 完整 trajectory 记录与成功/失败 Case Study；
5. 能回答“为什么设计、测出了什么、模型为何产生差异”的最终报告。

## 工作原则

- 每次只完成 `plan.md` 中的一个阶段，提交后等待审查，不越过阶段门禁。
- Benchmark 未通过 Bug State 与 Oracle State 人工验证前，不进入正式模型实验。
- 不根据模型自述判断成功；最终结果以 evaluator、测试和运行时证据为准。
- 将先验工作、本项目设计和真实实验结论明确分开。

## Repository 结构

| 路径 | 用途 |
| --- | --- |
| `research/` | 文献调研、Research Gap 与研究问题 |
| `design/` | 候选任务与最终 Benchmark Specification |
| `benchmark/` | 可运行任务、Bug 状态、测试、evaluator 与验证记录 |
| `harness/` | 统一 Agent Harness、工具适配与实验协议实现 |
| `experiments/` | 各次模型运行的配置、输出与可复现实验记录 |
| `trajectories/` | Agent 工具调用和观察—行动轨迹 |
| `results/` | 评分、模型对比与 Case Study |
| `report/` | 最终面试评测文档 |

## 评测隔离与安全

- 作者仓库可以保存 Oracle、ground-truth patch、隐藏测试和 evaluator；正式运行时必须导出独立的 Agent 工作区，只暴露任务允许的信息。
- Agent 工作区不得包含参考补丁、隐藏测试、其他模型的 trajectory / result，或能够直接泄露 Bug 注入差异的作者 Git 历史。
- 后续实验应以唯一 `run_id` 记录任务版本、输入版本、Harness 与模型版本、工具权限、预算、环境、终止原因及证据路径。
- `.env`、API key、Token 和其他凭据不得进入 Git、Prompt、trajectory、命令输出或报告；公开配置只写入不含真实值的 `.env.example`。

## 项目文档

- [`题目.md`](题目.md)：HR 正式题目，优先级最高。
- [`plan.md`](plan.md)：逐阶段执行计划。
- [`progress.md`](progress.md)：可追加的阶段进度、结论、风险和下一阶段输入。
