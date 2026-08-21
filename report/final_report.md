# GameVisualFix 多模型评测报告

> **End-to-End Pilot Complete**
>
> **Seed + External Model Minimum Completed; Controlled Comparison Qualified**
>
> 日期：2026-08-21

## 摘要

本项目构建并运行了一条面向游戏开发视觉调试的 Coding Agent Evaluation 全链路：文献边界与研究问题、原创 Godot repository task、可展示 dataset、统一指标、隐藏自动 evaluator、API tool-loop、真实 provider 调用、hash-chain trajectory、case study 与结果报告。Task 001 的 Bug 状态三次稳定为 20/100，reference patch 三次稳定为 100/100；七类投机补丁均被拒绝。

真实实验中，本地登录 Codex `gpt-5.6-sol` 和经火山方舟 Agent Plan 接入的 `doubao-seed-evolving` 均得到 100/100 并成功；外部模型 Qwen 得分 42/100 且失败。Local Codex 与 Seed 成功 run 使用相同 public-preload Controller 包装，形成可展示的同包装子组；Qwen input packaging 不同，不能把分差外推为一般模型排名。Seed canonical run1 timeout、GPT/Claude 403 与历史 Codex sandbox blocker 均保留为无效基础设施结果。

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

严格 headless 不能产生真实 viewport，故按用户批准使用隐藏 Windows renderer。API Harness 是一天内 P0 的工程放宽：它实现 workspace 路径与写入限制，但不是 VM/Windows Sandbox 级 OS 隔离。历史 Codex direct-write 运行证明 Windows `workspace-write` 在该环境中拒绝了全部模型命令；本次改用 read-only Codex 加受限 Controller，没有使用危险的全磁盘绕过选项。

Seed Evolving 使用 Codex CLI 0.142.5 的 custom model provider：run-local `CODEX_HOME/config.toml` 指向 Agent Plan `/api/plan/v3` Responses endpoint，key 通过 `Seed_Agent_Plan_key` 环境变量注入。Codex 对该第三方模型使用 fallback metadata。为避免 Windows 直接写入 sandbox，模型每轮输出一个受 Schema 约束的 Controller action；Controller 执行文件读写、smoke 和 observation。canonical run1 因逐文件调用导致 124K 以上上下文和 provider timeout；run2 预载相同 public text 并附上 public 资产，将动作压缩到 4 步。

本地 Codex 续跑使用 ChatGPT 登录、`gpt-5.6-sol`、`ultra` reasoning、read-only sandbox 和同一 Controller action 路径，不读取 `.env`。OpenAI Structured Outputs 要求 Schema 将全部 properties 列入 `required`，未使用字段传空字符串。升级 CLI 并修复 Schema 后，无任务 canary 通过；真实 run 在 4 actions 内完成 patch、fresh observation、smoke 与 submit。实际进程是 VS Code 扩展内 `codex-cli 0.149.0-alpha.4`，路径和 SHA-256 已进入 manifest；随后 Harness 固定 npm native CLI，消除 Windows PATH 解析漂移。

接入依据：[火山方舟 Agent Plan 三方工具文档](https://console.volcengine.com/ark/region:cn-beijing/docs/82379/2556054?lang=zh)、[Codex Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)、[Codex Non-interactive Mode](https://learn.chatgpt.com/docs/non-interactive-mode)。

## 5. 真实结果

| Run | Validity | Score | Task Success |
| --- | --- | ---: | --- |
| Local Codex `gpt-5.6-sol` | valid canonical local Controller | **100/100** | true |
| Seed Evolving via Codex run2 | valid compatibility preload | **100/100** | true |
| Qwen `qwen3-vl-plus` | valid | 42/100 | false |
| Seed Evolving via Codex run1 | provider timeout | 不计分 | — |
| Seed 2.1 Pro run 1 | provider timeout | 不计分 | — |
| Seed 2.1 Pro run 2 | provider timeout | 不计分 | — |
| GPT API `gpt-5.6-sol` | HTTP 403 | 不计分 | — |
| Claude API `claude-sonnet-4-6` | HTTP 403 | 不计分 | — |
| Codex login `gpt-5.6-sol`（历史 direct-write） | sandbox/controller invalid | 不计分 | — |

Qwen 细分为 Functional 18、Visual 14、Regression 10。它执行 17 个可解析 actions，成功获得两张 fresh screenshot（另一次 capture timeout），并提交了修改；累计 API 请求报告 token 为 99,741。其最终共享算法修改在单一画面上看似改善，却在多方向隐藏矩阵中失败。

Seed Evolving run2 细分为 Functional 45、Visual 35、Regression 20。它第一步将 Objective profile offset 从 `PI` 改为 `0.0`，随后请求 1 张 fresh screenshot、运行 smoke 并 submit；wall time 125.437 秒，4 actions，累计报告 token 206,913。补丁与 reference root cause 等价，10 个主 case 和所有回归检查通过。

Local Codex 同样得到 Functional 45、Visual 35、Regression 20；wall time 63.078 秒，4 actions，1 张 fresh screenshot，累计报告 token 67,498。10 个 Functional cases 的方向值均通过，视觉方向点积最低约 0.99923，高于 0.98 阈值；全部回归和输入哈希完整性检查通过。

## 6. 阶段分析与工程洞见

Qwen 的 Perception 和文件定位范围部分正确，但根因判断错误导致共享算法过修。公开 smoke 触发一次语法恢复；成功 fresh screenshot 又触发一次基于新证据的 patch 变化，因此 Recovery 确实发生。最终 evaluator 说明“有闭环”和“做对任务”是两件事：视觉反馈提高了可纠错性，却不保证模型摆脱局部画面过拟合。

Seed Evolving 的 Perception、Localization、Editing 和 Verification 均有成功证据；首次 patch 即正确，所以 Recovery 记为 `N/A`。它把 Objective 异常、Threat 正常和两张资产原生朝向组合为对象级配置根因，没有修改共享算法。

Local Codex 呈现相同的成功阶段链：首步对象级定位与编辑，随后 fresh screenshot 验证、smoke 和提交；Recovery 同样为 `N/A`。这次成功证明之前 Codex 无效结果的主要阻塞位于 Windows direct-write Harness，而不是隐藏 evaluator 或任务本身。

工程上最重要的结论是 validity 必须先于 score。HTTP 403、provider timeout 和 sandbox 阻断不能被记录为模型 20 分；20 只是未修改 Seed 的 Bug baseline。模型比较报告必须把 availability、harness validity 与 task outcome 分层。

## 7. 局限与后续正式续跑

- 单任务、三个有效轨迹不支持统计显著性、通用排名或模型家族强弱结论。
- Seed run2 的 public preload 与 Qwen 的逐步探索不同，结果可作成功/失败 case study，但不是严格受控排名。
- Seed canonical run1 仍有长上下文 provider timeout；Codex 对该模型缺少原生 metadata，fallback 可能影响行为和性能。
- Local Codex 实际 run 使用扩展内 alpha CLI，而 canary 使用 npm stable CLI；二者均成功访问同一指定模型，但严格复现时应使用 Harness 新增的显式 CLI 路径固定。
- GPT/Claude `.env` 凭据或 endpoint 权限仍需修复。
- 正式运行应采用 Windows Sandbox/VM 或独立低权限账号，同时保证 Godot GPU rendering 可用。
- 应增加 2–5 个同结构任务，覆盖 layout、动画/瞬态状态，并预注册 timeout 与成本指标。

下一轮应统一 input packaging：让 Qwen、Seed Evolving 与 Local Codex 都使用 public preload，或全部使用批量 read tool；固定同一 CLI/Schema 后从全新 workspace 各跑一次。现有 run 均不应被 best-of-n 覆盖。还应为 Codex custom model metadata、Responses reasoning events 和长上下文 timeout 建立专门 canary。

## 8. 交付索引

- Dataset：`benchmark/dataset.jsonl`、`benchmark/DATASET_CARD.md`
- Task 与验证：`benchmark/task_001/task.json`、`benchmark/task_001/validation.md`
- Harness：`harness/run_api_eval.py`、`harness/run_codex_provider_eval.py`、`harness/api_models.json`
- 机器结果：`results/scores.json`
- 对比与 Case Study：`results/comparison.md`、`results/pilot_case_study.md`
- 原始运行目录已按发布规则移除；历史内容仍可从 Git 历史追溯。
- 当前正式结果与脱敏轨迹：[`report/final_project_report.md`](final_project_report.md)、[`results/v2_1_seed_proxy_scores.json`](../results/v2_1_seed_proxy_scores.json)、[`trajectories/v2_1_seed_proxy/`](../trajectories/v2_1_seed_proxy/)
