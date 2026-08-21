# GameVisualFix 多模型评测报告

> **End-to-End Pilot Complete**
>
> **HR Formal Seed-vs-External Comparison Incomplete**
>
> 日期：2026-08-21

## 摘要

本项目构建并运行了一条面向游戏开发视觉调试的 Coding Agent Evaluation 全链路：文献边界与研究问题、原创 Godot repository task、可展示 dataset、统一指标、隐藏自动 evaluator、API tool-loop、真实 provider 调用、hash-chain trajectory、case study 与结果报告。Task 001 的 Bug 状态三次稳定为 20/100，reference patch 三次稳定为 100/100；七类投机补丁均被拒绝。

真实实验中，Qwen 是唯一形成有效提交的模型，得分 42/100 且失败；Seed 两次 provider timeout，GPT/Claude API 均 HTTP 403，Codex CLI 补充运行受 Windows sandbox/controller 阻断。因此“整条评测流水线”已经走通，但 HR 要求的有效 Seed 与外部模型双模型能力对比仍未完成，不能用无效运行冒充分数。

## 1. 研究问题与文献边界

主问题关注：Agent 能否在 Patch 后获取新的 runtime visual observation，并利用它验证修复或条件性恢复。次问题关注 `Perception → Localization → Editing → Verification → Recovery` 的阶段级错误传播。截图驱动编辑、多模态软件修复、失败重试和视觉定位均有近邻研究，本项目不声称宽泛“首次”；其价值在于把这些机制组合到受控的现有游戏仓库视觉修复 case 中。

详细一手来源与 novelty 边界见 `research/literature_review.md` 和 `research/gap_analysis.md`。

## 2. Dataset 与 Task

Pilot dataset 当前含 1 个原创任务：`Signal Courier — Twin Tracker Calibration`。输入包括 Godot 4.7.1 public repository、冻结 Prompt 和 960×540 初始 runtime screenshot。两个 HUD Tracker 共用正确方向算法，但两张自制箭头 PNG 原生朝向相反；Objective profile 错误复用 Threat 的 `PI` offset。正确修复是 Objective profile offset 归零，evaluator 接受行为等价补丁而不比对固定 diff。

数据资产包括：

- `benchmark/dataset.jsonl`：1 条可机器读取任务索引；
- `benchmark/task_001/task.json`：Prompt、图片、Engine、预算和 evaluator hash；
- 10 个隐藏主 case：五方向 × 两分辨率；
- 动态目标、Threat、WASD、Objective completion、节点/布局和 PNG hash 回归；
- `validation/results.json`：Bug/Oracle 重复性与 shortcut 验证数据。

## 3. 指标与 Oracle

Build/launch 与完整性是硬门槛。Functional Correctness 45 分、Visual Correctness 35 分、Regression Safety 20 分；只有三类全部满分才算 Task Success。视觉 Oracle 根据独占尖端颜色估计方向，预测与目标单位向量点积必须 `>= 0.98`。总分不能补偿 mandatory failure。

Task 验证结果：Bug 三轮均 20/100；Oracle 三轮均 100/100；每种状态各 33 张截图在对应 case 间哈希稳定。修改图片、翻转共享算法、隐藏/缩放 Tracker、固定方向、移动目标和修改错误 profile 均被拒绝。

## 4. Harness 与实验协议

统一 API Harness 使用 OpenAI-compatible chat completions 形式，但不把本地文件系统直接暴露给 provider。Controller 提供受限的 `list_files/read_file/write_file/run_smoke/observe/submit` JSON action；每个 provider 从 public allowlist 建立独立 workspace。`observe` 由 Controller clean import 后启动隐藏 Windows/OpenGL Godot 进程并把 fresh PNG 注入同一消息历史；hidden evaluator 只在终止后执行。

`.env` 只在进程内读取 key/base URL，未写入配置、trajectory 或报告。原始模型响应、最终 patch、evaluation 与运行 manifest 保存在 `experiments/`；规范化 trajectory 使用前向 SHA-256 hash chain。

严格 headless 不能产生真实 viewport，故按用户批准使用隐藏 Windows renderer。API Harness 是一天内 P0 的工程放宽：它实现 workspace 路径与写入限制，但不是 VM/Windows Sandbox 级 OS 隔离。Codex CLI 补充运行证明当前 Windows `workspace-write` 又过于严格，拒绝了全部模型命令；未使用危险的全磁盘绕过选项。

## 5. 真实结果

| Run | Validity | Score | Task Success |
| --- | --- | ---: | --- |
| Qwen `qwen3-vl-plus` | valid | 42/100 | false |
| Seed 2.1 Pro run 1 | provider timeout | 不计分 | — |
| Seed 2.1 Pro run 2 | provider timeout | 不计分 | — |
| GPT API `gpt-5.6-sol` | HTTP 403 | 不计分 | — |
| Claude API `claude-sonnet-4-6` | HTTP 403 | 不计分 | — |
| Codex login `gpt-5.6-sol` | sandbox/controller invalid | 不计分 | — |

Qwen 细分为 Functional 18、Visual 14、Regression 10。它执行 17 个可解析 actions，成功获得两张 fresh screenshot（另一次 capture timeout），并提交了修改；累计 API 请求报告 token 为 99,741。其最终共享算法修改在单一画面上看似改善，却在多方向隐藏矩阵中失败。

## 6. 阶段分析与工程洞见

Qwen 的 Perception 和文件定位范围部分正确，但根因判断错误导致共享算法过修。公开 smoke 触发一次语法恢复；成功 fresh screenshot 又触发一次基于新证据的 patch 变化，因此 Recovery 确实发生。最终 evaluator 说明“有闭环”和“做对任务”是两件事：视觉反馈提高了可纠错性，却不保证模型摆脱局部画面过拟合。

工程上最重要的结论是 validity 必须先于 score。HTTP 403、provider timeout 和 sandbox 阻断不能被记录为模型 20 分；20 只是未修改 Seed 的 Bug baseline。模型比较报告必须把 availability、harness validity 与 task outcome 分层。

## 7. 局限与后续正式续跑

- 单任务、单次有效轨迹不支持统计显著性、通用排名或模型家族强弱结论。
- Seed 未产生有效提交，HR 正式 Seed vs external 对比尚缺失。
- GPT/Claude `.env` 凭据或 endpoint 权限需修复；Seed endpoint 需确认流式响应、thinking timeout 或换用可稳定返回的部署 ID。
- 正式运行应采用 Windows Sandbox/VM 或独立低权限账号，同时保证 Godot GPU rendering 可用。
- 应增加 2–5 个同结构任务，覆盖 layout、动画/瞬态状态，并预注册 timeout 与成本指标。

续跑的第一优先级不是改题或放宽 Oracle，而是修复 provider 可用性：先做无任务图像 + JSON action canary；Seed 能在预算内稳定返回、GPT/Claude 鉴权成功后，从全新 workspace 各运行一次，再更新 `scores.json` 与本报告。Qwen 已有结果不应 best-of-n 重跑。

## 8. 交付索引

- Dataset：`benchmark/dataset.jsonl`、`benchmark/DATASET_CARD.md`
- Task 与验证：`benchmark/task_001/task.json`、`benchmark/task_001/validation.md`
- Harness：`harness/run_api_eval.py`、`harness/api_models.json`
- 机器结果：`results/scores.json`
- 对比与 Case Study：`results/comparison.md`、`results/pilot_case_study.md`
- 原始运行：`experiments/task_001/`
- 可审计轨迹：`trajectories/task_001/`
