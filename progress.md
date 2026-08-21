# GameVisualFix 项目进度

本文件采用追加式记录。每个阶段固定保留“当前阶段、已完成内容、关键结论、当前风险、下一阶段输入”五项，避免后续更新覆盖重要决策历史。

## 2026-08-20 — Step 0

### 当前阶段

**Step 0：项目初始化——已完成，等待用户审查。**

本阶段到此停止，不进入文献调研、Research Gap、候选任务或 Benchmark 实现。

### 已完成内容

- 以 `题目.md` 为最高优先级，提炼 HR 强制要求与建议项，并与 GameVisualFix 自选方向明确区分。
- 初始化 `main` 分支 Git repository，并建立规划中的八个工作目录。
- 创建 `README.md`、`.gitignore`、`.env.example` 与 `.gitattributes`，建立项目结构和凭据保护基线。
- 明确作者仓库与 Agent 可见工作区的隔离原则，防止 Oracle、隐藏测试、参考补丁和 Git 历史泄漏答案。
- 配置空 GitHub repository 为 `origin`，完成初始化提交与推送作为本阶段验收动作。

### 关键结论

- HR 考察的是一套小型但完整的 Coding Agent Benchmark / Evaluation，而不只是实现一个函数或提出一道代码题。
- 最终功能正确性应作为主要评价依据；trajectory 和过程指标用于解释模型能力差异，不能代替结果验证。
- 项目选择“游戏开发场景下的多模态 Coding Agent Evaluation”，但 task-essential visual evidence、视觉闭环调试等仍是假设，需经文献和实验验证。
- P0 始终限制为 1 个完整任务、Seed 与 1 个外部模型、自动评分、trajectory 分析和最终报告。

### 当前风险

- 总工期只有一天，研究新颖性不能挤压可运行任务、自动评分和真实模型实验等必交项。
- Seed 模型的精确调用方式、图像输入能力、额度和限流尚未确认；`.env` 当前没有模型 API 配置。
- 两个模型能否使用统一 Harness 和完全一致的工具权限尚未验证。
- Godot 4、本地无界面运行、截图采集与视觉自动评价链路尚未验证。
- 必须证明视觉输入提供不可由文字直接替代的任务证据，同时保证评分稳定可靠。

### 下一阶段输入

- 必读：`题目.md`、`README.md`、`progress.md`。
- Step 1 只进行 2024–2026 年游戏 Coding Agent、多模态代码生成和 Visual Agent 文献调研。
- 重点分析 GameDevBench 与 GameCraft-Bench，最多保留 5 个值得探索的 Gap。
- Step 1 不设计具体 Benchmark Task，不实现代码或 Harness。

## 2026-08-20 — Step 1

### 当前阶段

**Step 1：游戏多模态 Coding Agent 文献调研——已完成，等待用户审查。**

本阶段到此停止，尚未进入 Step 2 的 Research Gap 定稿与研究问题选择，也未设计或实现 Benchmark Task。

### 已完成内容

- 以论文、项目页和作者官方仓库为一手来源，完成截至 2026-08-20 的定向调研。
- 深入分析 GameDevBench 与 GameCraft-Bench 的任务构造、Agent 输入与动作、运行时视觉反馈、Ground Truth、自动评分、失败恢复和 trajectory。
- 比较 GameEngineBench、OpenGame / OpenGame-Bench 与 Design2Code，并用 VisualAgentBench、SWE-bench Multimodal、GUIRepair、SVRepair 和 MM-IssueLoc 核验 novelty 边界；另以 CodeV、FailureMem 与 CUADebug 检查多模态修复、失败经验和阶段诊断的相邻覆盖。
- 逐项回答 `plan.md` 中的十个问题，形成统一比较矩阵。
- 保留 5 个候选 Gap，并分别标注已有覆盖、证据强度、一天内 P0 可行性与风险。
- 输出 `research/literature_review.md`；本阶段未新增公共 API、Schema、Harness 或评测接口。

### 关键结论

- 游戏开发同时要求仓库理解、跨文件修改、引擎运行、异构素材和时序/视觉判断，且部分行为可由引擎状态测试或固定输入的受控 replay 观察与评价，适合构造有区分度的 Coding Agent 任务。
- GameDevBench 已覆盖现有 Godot 工程、隐藏 engine-state tests 和可选视觉反馈；GameCraft-Bench 已展示 runtime screenshot 驱动的多轮迭代、replay 评分和过程统计。
- 图像必要性标注、有/无图对照、screenshot-driven editing、仓库级多模态 repair、visual localization 和失败后迭代在相邻领域均已有工作，不能笼统声称为首次；严格的 task-essential / Patch 不可辨识性仍是待检验假设。
- 相对值得 Step 2 继续检验的组合需要收窄到：现有游戏仓库、初始视觉症状的增量信息、Patch 后新 runtime 画面驱动的再次规划/恢复，以及游戏代码修复链的阶段化诊断；本阶段未据此选择 Research Question。
- 功能测试与视觉 Oracle 应互补；纯 engine-state tests 可能漏掉肉眼异常，纯像素或 VLM judge 也可能奖励表面相似。

### 当前风险

- 本次是定向而非穷尽式综述，“未发现完整覆盖”不能写成全领域不存在。
- 2026 年论文和官方仓库更新较快，论文版本、当前实现和动态 leaderboard 必须持续分开引用。
- 视觉闭环、失败恢复与多模态 trajectory 根因诊断已被部分覆盖，若 Step 2 不继续收窄边界，Research Gap 容易与 VAB-CSS、GameCraft-Bench、GUIRepair、SVRepair、FailureMem 或 CUADebug 重叠。
- VLM judge、稀疏抽帧与像素相似度均有测量误差；联合 Oracle 的阈值和权重也可能显得任意。
- 一天工期不适合同时实现复杂 replay、时序视觉 Bug、多模型实验和精细人工标注，P0 仍需保持单任务。

### 下一阶段输入

- 必读：`题目.md`、`research/literature_review.md`、`progress.md`。
- Step 2 仅基于已核验文献评估 Hypothesis A/B/C，确定 1 个主要 Research Question 和最多 2 个 Secondary Research Questions。
- 优先审查候选组合的 novelty、面试价值和一天内可验证性；不得在 Step 2 编写 Benchmark 代码。
- 在用户审查并明确进入 Step 2 前，不继续执行后续阶段。

## 2026-08-21 — Step 2

### 当前阶段

**Step 2：Research Gap 与研究问题——已完成，按用户授权自动进入 Step 3。**

本阶段只冻结研究边界与问题，不选择具体任务，不实现 Benchmark、Harness 或模型实验。

### 已完成内容

- 基于 `research/literature_review.md` 逐项复核 Hypothesis A、B、C 及五个候选 Gap 的已有覆盖、剩余证据边界、面试价值与一天内 P0 可行性。
- 将 Hypothesis B 的 Patch 后 fresh runtime visual observation、验证与条件性恢复确定为主要 Research Question。
- 将 Hypothesis C 的 `Perception → Localization → Editing → Verification → Recovery` 阶段级错误传播确定为唯一 Secondary Research Question。
- 将 Hypothesis A 降为任务有效性 Gate；P0 不增加 no-image 因果消融，也不把单任务失败当作视觉必要性的证明。
- 预注册阶段定义、可观察证据、`N/A` / `Ambiguous` 规则、反证条件和单任务 case-study 外推边界。
- 输出 `research/gap_analysis.md`；本阶段未新增公共 API、Schema、Harness 或评测接口。

### 关键结论

- screenshot-driven editing、失败重试、视觉定位与 trajectory diagnosis 均有近邻工作，不能提出宽泛“首次”声明；本项目的价值是把它们组合到一个受控的现有游戏仓库视觉修复案例中。
- Outcome 由预声明的功能、视觉与回归 Oracle 判断；trajectory 只解释能力差异，模型自述不能代替成功证据。
- fresh observation 必须在当前 Patch 后由新运行进程生成并真实进入 Agent 上下文；只生成但未展示、复用旧图或只供 evaluator 使用均不构成视觉闭环。
- Recovery 仅在已有失败或不完整验证证据、且 Agent 随后改变 hypothesis、定位或编辑时可评价；首轮成功时记为 `N/A`，不能人为制造失败。
- 本轮 Codex-only pilot 只能验证链路可行性和单轨迹过程现象，不能回答 Seed 与外部模型谁更强。

### 当前风险

- 单任务、单次 pilot 不支持统计显著性、通用模型排名或跨任务能力结论。
- Agent 可能首轮成功，使 Recovery 没有观察机会；Verification 仍可评价，但 Recovery 必须记为 `N/A`。
- 若任务文本、文件名、资源命名或可见测试泄露唯一 Patch，Hypothesis A 的有效性 Gate 将失败。
- 视觉通道、Harness 权限和运行环境若不一致，会混淆后续正式双模型比较。
- VLM judge 可靠性不足，因此 P0 必须使用确定性功能、语义像素与回归 Oracle。

### 下一阶段输入

- 必读：`research/literature_review.md`、`research/gap_analysis.md`、`progress.md`。
- Step 3 比较 2D visual-state、HUD layout 与 temporal animation 三个候选，只选择一个 P0 Task。
- 选择标准固定为 Multimodal Necessity、Agentic Depth、Evaluation Reliability、Model Discriminability 与低实现成本。
- Step 3 仍不实现任务、评分器或 Harness；根据用户授权，阶段验收和推送通过后自动继续。

## 2026-08-21 — Step 3

### 当前阶段

**Step 3：候选任务设计——已完成，按用户授权自动进入 Step 4。**

本阶段只完成候选比较与 P0 选择，尚未编写 Godot 项目、Oracle、Harness 或模型实验。

### 已完成内容

- 设计并比较 `Signal Courier — Twin Tracker Calibration`、HUD safe-area/layout repair 与 animation/trail phase repair 三个候选任务。
- 对每个候选逐项说明游戏场景、初始 Repository、Bug、视觉输入、视觉必要性、可编辑文件、运行需求、恢复机会、Ground Truth、自动评价、模型区分度和一天内风险。
- 将五个维度统一为 1–5 分，`Implementation Cost` 采用反向评分，5 表示成本最低；预注册准入门槛后再比较总分。
- 固定选择 Candidate A 作为 Task 001：两个 Tracker 共享正确方向算法，但使用原生朝向相反的素材，Objective profile 的 art-axis offset 配置错误。
- 输出 `design/task_candidates.md`，并冻结 Candidate A 的淘汰条件；未根据任何模型结果调整选题。

### 关键结论

- Candidate A 的 runtime 空间关系能提供不可由题面唯一替代的故障证据，同时可用确定性的方向向量和语义像素 Oracle 评分。
- HUD layout 候选实现成本可控，但视觉要求容易被文本化，且多种合理布局会削弱 Ground Truth 唯一性。
- Animation/trail 候选具有较高 Agentic Depth 和区分度，但固定 replay、跨帧捕获与时序评分超过一天 P0 的风险预算。
- P0 选择优先保证可重复运行、稳定评分和完整端到端链路，不以复杂度或宽泛 novelty 为目标。
- Candidate A 仍须通过 Step 4/5 的 Godot preflight、文本泄漏审计、三次 Bug/Oracle 重复验证和 shortcut tests，才能进入模型实验。

### 当前风险

- PNG 的原生尖端方向、resource 字段名或可见测试若直接泄露正确 profile 值，会削弱 task-essential visual evidence。
- 简单一行配置修复可能被模型猜中；需通过对称 profile 设计、无答案命名和隐藏多方向场景降低猜测成功的解释空间。
- baseline 单帧可能被硬编码修复，需要多方向、双分辨率和资产哈希检查阻止表面作弊。
- Headless 渲染、截图时机和纹理过滤尚未在本机验证。
- 本轮仍只有 Codex 登录态，正式 Seed 与外部模型对比不在 pilot 范围内。

### 下一阶段输入

- 必读：`research/gap_analysis.md`、`design/task_candidates.md`、`progress.md`。
- Step 4 只冻结 Task 001 Benchmark Specification，并执行 Godot 4.7.1 环境预检。
- 必须在实现前固定 Prompt、Agent 可见内容、工具、预算、Oracle、评分规则、有效/无效运行标准与污染隔离。
- Godot preflight 若经一次诊断复现仍失败，则记录 blocker、提交推送并停止，不自动切换引擎。

## 2026-08-21 — Step 4（环境 Gate）

### 当前阶段

**Step 4：Benchmark Specification——环境 Gate 未通过，流程已按预注册规则停止。**

本阶段没有冻结 `design/benchmark_spec.md`，也未进入 Step 5–9P。

### 已完成内容

- 从 Godot 官方 release 获取 Windows x86-64 standard 4.7.1 便携包，并以官方 `SHA512-SUMS.txt` 验证 archive 完整性。
- 记录 Godot 精确版本、archive SHA-512、executable SHA-256、主机 OS 与 CPU；工具仅解压到被忽略的 `.cache/tools/`，未修改系统 PATH。
- 构造独立的最小 clean-copy probe，验证严格 `--headless` import 成功。
- 执行第一张非黑 runtime PNG Gate；失败后只进行一次预注册的诊断复现，没有继续第二、三次捕获或切换渲染方式。
- 输出 `design/godot_preflight.md`，保留命令、结果、根因、未尝试替代方案和恢复条件。

### 关键结论

- Godot archive、版本和 clean import 均有效，阻塞不来自下载损坏或项目 parse error。
- 当前 Windows official build 的严格 `--headless` 使用 headless display server 与 null rendering device；Viewport texture 读取落到 dummy backend，不能生成真实 runtime PNG。
- 进程退出码为 0 不代表截图成功；必须以 PNG 存在、尺寸与非黑像素作为捕获 Gate。
- 冻结方案依赖 Patch 后 fresh runtime screenshot，因此不能绕过视觉捕获继续实现或调用 Codex。
- 该结果是环境/设计阻塞，不是模型失败，不得计入 pilot 分数。

### 当前风险

- 改为隐藏 windowed renderer、offscreen display、VM/Windows Sandbox 或 CPU 语义渲染都会改变已批准的环境与隔离假设。
- 未经重新预检便实现 Task 001，可能在 Step 5/6 才暴露不可用的视觉闭环，浪费工期并污染实验设计。
- 若允许 windowed capture，还需验证无人值守运行、窗口焦点、分辨率、截图时机、进程清理与 sandbox 可用性。
- Seed 和外部模型凭据仍未配置；即使环境恢复，本轮也只能先完成 Codex-only pilot。

### 下一阶段输入

- 当前没有自动下一阶段；Step 5–9P 保持未开始。
- 恢复所需输入：用户明确批准一种非严格-headless 的 Windows runtime capture 策略。
- 恢复后必须新建 preflight revision，连续三次通过非黑 PNG 与语义像素稳定性检查，再创建 `design/benchmark_spec.md`。
- 本 blocker 记录和 Git 历史必须保留，不得 amend、squash 或改写为成功结果。

## 2026-08-21 — Step 4 Rev.2

### 当前阶段

**Step 4：Benchmark Specification——Rev.2 环境 Gate 与规格冻结已完成，按用户授权自动进入 Step 5。**

Rev.1 严格-headless blocker 继续保留；本阶段基于用户明确批准的受控 Windows hidden-window renderer 恢复执行。

### 已完成内容

- 以真实 `Windows` display server、OpenGL 3.3 / `gl_compatibility` 和项目内部 Viewport capture 重做环境预检。
- 保留首个成功渲染但缺失 exit-code telemetry 的 run 1 为 `invalid_telemetry`；只修复 runner instrumentation，未调整 scene、renderer、时机或阈值。
- 使用 run 2–4 三个新进程完成 canonical Gate：退出码、stderr、PNG 尺寸、非黑像素、四类语义像素、SHA-256 和逐像素比较全部一致，无残留 Godot 进程。
- 输出 `design/godot_preflight_rev2.md`，记录用户授权、Rev.1/Rev.2 差异、原始结果、焦点风险和正式 Harness 约束。
- 输出并冻结 `design/benchmark_spec.md`：Prompt、输入隔离、环境、动作协议、Ground Truth、45/35/20 Oracle、预算、有效/无效运行和 trajectory 标签均在模型接触任务前确定。

### 关键结论

- 严格 `--headless` 不可用不代表 Godot 不能自动截图；隐藏但非最小化的真实 Windows renderer 可以稳定提供完全一致的 Viewport PNG。
- 截图必须由 Controller 在冻结 workspace copy 中生成，并以 tree/image receipt 证明 freshness；Agent 自己保存的图片和 evaluator-only 图片均不可信作闭环证据。
- Task 001 的主要成功条件是完整性 Gate 以及功能 45、视觉 35、回归 20 全部满分；总分不能补偿 mandatory failure。
- 初始 screenshot 和 PNG pixels 用于在多个静态合理解释之间提供区分证据；本轮不通过 no-image model run 声称因果必要性。
- 窗口可能短暂抢 foreground 是已知宿主机限制；只要重复像素不受影响就作为 telemetry 记录，若导致差异则运行无效。

### 当前风险

- Agent submission 是不可信代码；正式 renderer 必须使用隔离 copy、最小权限、无网络、受控临时目录和完整进程树清理。
- 完全隐藏窗口在本机稳定，但跨机器、锁屏或 RDP 状态下不能直接外推，需要重新 preflight。
- 一行 reference patch 可能被猜中，因此对称 profile、文本泄漏审计、多方向双分辨率和 shortcut tests 必须全部落实。
- Codex image/resume、clean `CODEX_HOME`、private ACL 和 JSONL schema 仍需 Step 6 canary。
- 本轮仍是单模型 pilot，不能回答 HR 正式 Seed vs external comparison。

### 下一阶段输入

- 必读：`design/benchmark_spec.md`、`design/godot_preflight_rev2.md`、`progress.md`。
- Step 5 只实现 Task 001；Bug State 与 Oracle State 均须连续三次验证，且隐藏评价能拒绝预声明 shortcut。
- private tests、reference patch 和 expected artifacts 不得进入 Agent-visible package。
- Oracle 未全通过时不得进入 Harness 或模型实验。

## 2026-08-21 — Step 5/6 暂停检查点

### 当前阶段

**Step 5：Task 001 实现——进行中，已按用户要求暂停。Step 6 仅保存未验收草案；Step 7P–9P 未开始。**

当前有效 WIP 已迁入 tracked `benchmark/task_001/`、`harness/` 与
`design/experiment_protocol.md`。本记录不将 Step 5 或 Step 6 标为完成；禁止在恢复验收前调用模型。

### 已完成内容

- Step 2–4 与 Rev.2 Windows/OpenGL preflight 已独立提交并推送；冻结 RQ、Task 001 选择、Prompt/Oracle 规格和受控隐藏窗口策略均保留。
- 保存 Task 001 当前 Godot 项目、原创资产、Bug screenshot、WASD、Objective completion、公开 smoke/capture、private suite/evaluator/reference patch。
- 初始布局已对齐 Objective 正东、Threat 西北；泄露 PNG 原生朝向的 generator 已移出 public workspace。
- 保存 Visual/Regression Oracle 的最新源码草案：`dot >= 0.98`、五方向×双分辨率、tip/body 像素、scale/alpha、WASD、completion、required nodes 与资产完整性。
- 保存 Codex Harness 当前源码草案，包括显式 thread resume、strict action schema、fresh-image/turn/time/command 预算、sanitized workspace、日志/receipt 和 fixture。
- 未保存旧 `.godot`/Python cache、派生 Oracle/shortcut workspace、`.selftest`、凭据副本或失效的批量截图。

### 关键结论

- **当前没有模型实验结果。** 尚未调用 Codex、Seed 或其他模型，也没有可用于报告的 Pilot trajectory 或分数。
- Step 4 Rev.2 环境 Gate 仍有效；严格 headless 失败与隐藏 Windows/OpenGL 三次稳定通过的历史证据均已保留。
- 较早 Bug 三轮为 `20/100`、Oracle 三轮为 `100/100`，但它们早于最新场景与 Oracle 修改，已明确失效，必须重跑。
- 最新 shortcut 草案运行均得到 `task_success=false`，但 asset-swap 使用过旧 import cache；整个 shortcut 集合仍须 cache-free 重跑。
- Harness 较早 fixture 曾通过，Codex CLI help/config parse 也曾通过；最新 hash-chain、Godot PATH、token 与 strict-action 修改后尚未回归，因此不能声称 Step 6 已通过。

### 当前风险

- Step 5 尚缺最终 `task.json`、`validation.md`、Bug/Oracle 最新三轮、cache-free shortcut、截图哈希稳定性与 multimodal leak audit。
- Harness 尚未删除 run-local `auth.json` 副本；evaluator failure 可能被误分类为 infrastructure invalid 并触发错误重跑。
- adapter 环境/网络隔离、真实 Windows sandbox 读取边界、初始与 resume 图片感知、JSONL、进程树清理和 credential canary 均未证明。
- `public/TASK.md` 仍需在恢复时与冻结 Exact Agent Prompt 做最后逐字审计，之后更新 manifest hash。
- `benchmark/task_001/` 与 `harness/` 是可恢复源码检查点，不是可发布 Benchmark/Harness；执行真实 Pilot 会污染实验并带来凭据风险。

### 下一阶段输入

- 下一次继续时的**第一步**：阅读 `benchmark/task_001/CHECKPOINT.md` 与 `harness/CHECKPOINT.md`，先实现 Harness `auth.json` finally 清理和 evaluator failure classification 修复；不调用模型。
- 随后按 `benchmark/task_001/CHECKPOINT.md` 中的命令从 cache-free copy 重跑 Step 5：Python compile、Godot import/smoke、Bug/Oracle 各三轮、全部 shortcut、哈希与 leak audit。
- Step 6 修复后按 `harness/CHECKPOINT.md` 重新运行 `harness/tests/self_test.ps1`；只有 fixture 全绿并通过无任务 production canary，才允许 Step 7P。
- 恢复所需命令已分别固定在上述两个 CHECKPOINT 文档中；本次暂停后不再执行这些命令，等待用户回复。
## 2026-08-21 — Step 5

### 当前阶段

**Step 5：Task 001 实现与验证——已完成，自动进入统一多模型 Harness 实现。**

### 已完成内容

- 冻结并实现 1 条可展示的 pilot dataset record，包含 public Godot Seed、初始视觉证据、10 个隐藏主 case、reference patch 和独立 evaluator。
- 在当前 Windows/OpenGL Compatibility 环境中完成 Bug State 与 Oracle State 各三次 clean-copy 验证；每次覆盖 10 个方向/分辨率组合和 1 个动态回归 case。
- Bug 三轮均为 20/100 且失败；Oracle 三轮均为 100/100 且成功；对应截图哈希完全稳定。
- 通过 asset swap、共享算法翻转、隐藏/缩放 Tracker、固定方向、目标篡改和修改错误 profile 七类负例验证 evaluator 的拒绝能力。
- 输出 `benchmark/dataset.jsonl`、`benchmark/DATASET_CARD.md`、`task.json`、`validation.md` 和机器可读 `validation/results.json`。

### 关键结论

- Task 001 已具备可运行数据、明确指标、可复现 Bug/Oracle 边界和行为等价补丁评价能力，可以进入真实模型调用。
- 总分不能补偿 mandatory failure；只有 Functional 45、Visual 35、Regression 20 全部通过时 `task_success=true`。
- 严格 headless 限制仍存在；本机评价使用用户批准、已重复验证的 Windows 隐藏窗口渲染。

### 当前风险

- 数据集只有 1 个合成任务，结果只能作为 pilot/case study，不能形成统计排名。
- 单行修复仍可能被猜中；模型是否真正利用截图需结合 trajectory 中的观察、定位和验证证据谨慎解释。
- 多家 API 的模型命名、图像消息格式、限流和 OpenAI-compatible 兼容程度尚需真实 canary 确认。

### 下一阶段输入

- 以冻结的 `benchmark/task_001/public/`、`task.json` 和独立 evaluator 为输入，实现统一 API tool-loop Harness。
- Harness 只从 `.env` 读取凭据，不记录 key 或完整鉴权请求；每个 provider 使用独立 clean workspace。
- 完成确定性 fixture 与最小 API canary 后，依次运行 Seed、Qwen、GPT 和 Claude 配置，不重复 Task 001 验证。
## 2026-08-21 — Step 6

### 当前阶段

**Step 6：统一多模型 Harness——已完成 P0；严格 Codex/Windows isolation hardening 未完成。**

### 已完成内容

- 新增 controller-mediated OpenAI-compatible API Harness、四 provider 配置、受限文件/测试/观察动作和 clean workspace。
- 本地 fixture 通过 public smoke 与 fresh PNG capture；capture 后续补强为每次先 clean import。
- `.env` 凭据只在进程内读取，未进入 tracked 配置、日志或报告。

### 关键结论

- API tool-loop 足以走通一天内 P0，但它不是 VM 级安全隔离；strict Codex Harness 继续保留为 hardening 分支。

### 当前风险

- Provider 的协议兼容、限流、thinking latency 与鉴权状态会影响 validity；Windows `workspace-write` 当前拒绝 Codex 的全部动作。

### 下一阶段输入

- 使用冻结 Task 001，对 Qwen、Seed、GPT、Claude 与 Codex 登录态各建立独立运行记录；无效运行不计模型分。

## 2026-08-21 — Step 7

### 当前阶段

**Step 7：真实多 provider Pilot——已完成。**

### 已完成内容

- Qwen 完成 17 个 actions、两张成功 fresh screenshot 和 submit，隐藏评分 42/100。
- Seed 保留两次 timeout 历史；GPT/Claude 保留 HTTP 403；Codex 保留 sandbox/controller invalid 轨迹。
- 保存每次 workspace、patch、manifest、raw trajectory 与 hidden evaluation，并生成规范化 hash chain。

### 关键结论

- 仅 Qwen 是有效模型结果；其余 20/100 只是不修改 Bug baseline，不能冒充模型分数。

### 当前风险

- 有效模型数只有 1，HR 正式 Seed vs external 能力比较尚未完成。

### 下一阶段输入

- 只基于可观察事件分析 Qwen 的阶段错误传播；无效运行仅用于 infrastructure/availability 分析。

## 2026-08-21 — Step 8

### 当前阶段

**Step 8：Trajectory Case Study——已完成。**

### 已完成内容

- 输出 `results/pilot_case_study.md` 与 `results/comparison.md`，分离 Perception、Localization、Editing、Verification、Recovery 和 Outcome。

### 关键结论

- Qwen 确实根据 smoke failure 和 fresh screenshot 发生 recovery，但错误根因导致共享算法过修并对单画面过拟合。

### 当前风险

- 单轨迹不能外推模型总体能力，也不能把模型自述当作成功证据。

### 下一阶段输入

- 汇总 dataset、Oracle、Harness、真实结果、限制和正式续跑条件，发布最终报告。

## 2026-08-21 — Step 9P

### 当前阶段

**Step 9P：端到端多 provider Pilot 已完成；等待修复 Seed/GPT/Claude provider 后正式续跑。**

### 已完成内容

- 输出 `report/final_report.md`、机器可读 `results/scores.json`，并更新 README、实验协议和 Harness 状态。
- 完成从研究问题、数据集、指标、任务验证、模型调用、自动评分、trajectory 到报告的完整演示链路。

### 关键结论

- Benchmark 与 evaluator 可展示、可复现；本轮真实有效结果为 Qwen 42/100、task failure。
- HR 正式双模型比较仍不完整，因为 Seed 未形成有效提交；报告已明确标注而未伪造结论。

### 当前风险

- 数据集规模 1；严格 OS/VM 隔离、Seed 稳定响应和 GPT/Claude 鉴权仍是正式交付前缺口。

### 下一阶段输入

- 第一步运行无任务 image+JSON canary：修复 GPT/Claude HTTP 403，并确认 Seed 的推荐部署 ID、streaming/thinking timeout。
- Provider Gate 通过后，从全新 workspace 各跑一次 Seed 与至少一个外部模型；不重跑或择优覆盖当前 Qwen 结果。
## 2026-08-21 — Step 10：Seed Evolving via Codex

### 当前阶段

**Seed Agent Plan + Codex CLI Task 001 实验、汇总与报告已完成。**

### 已完成内容

- 核验 `.env` 新增 `Seed_Agent_Plan_key`，使用 Agent Plan 专属 Responses endpoint 和 `doubao-seed-evolving` model ID 完成 Codex canary。
- 新增 run-local Codex custom provider、严格 Controller action schema、同 thread resume、fresh screenshot 与 hidden evaluator 链路。
- canonical run1 保留为 provider timeout：10 个可解析 action，无 patch、无 observation，不计模型分。
- compatibility run2 预载相同 public text 并附上 public PNG；模型用 4 actions 完成根因修复、fresh observation、smoke 和 submit。
- hidden evaluator 得到 Functional 45、Visual 35、Regression 20，总分 100/100，`task_success=true`。

### 关键结论

- Seed Evolving 正确把 Objective 反向、Threat 正常定位到 `profile_alpha.tres` 的对象级 offset，并生成 `PI → 0.0` 的最小等价补丁。
- Patch 后 fresh screenshot 被真实注入同一 Codex thread；模型随后运行 smoke 并提交，Verification 成立；首次 patch 成功使 Recovery 为 `N/A`。
- HR 最低 Seed + external 有效分数现已具备：Seed Evolving 100、Qwen 42，但 public preload 差异使其只能作为 qualified case comparison。

### 当前风险

- Codex 0.142.5 不认识该第三方 model metadata，使用 fallback；Responses reasoning event 还产生兼容性 warning。
- canonical 逐文件 controller 会让上下文和延迟快速增长，run1 在约 124K 上下文后 timeout。
- run2 的 public preload 与 Qwen 逐步探索不一致，`comparison_eligible=false`；单任务也不支持通用排名。

### 下一阶段输入

- 若继续做严格比较，为 Qwen 与 Seed Evolving统一 public preload 或批量读取协议，并分别从全新 workspace 只跑一次。
- 增加 Codex custom model metadata/streaming timeout canary；保持当前两条运行与分数不可覆盖。

## 2026-08-21 — Step 11：本地 Codex Controller 复测

### 当前阶段

**本地 Codex `gpt-5.6-sol` Task 001 复测、隐藏评价、轨迹分析与报告更新已完成。**

### 已完成内容

- 将本地 Codex CLI 从 0.142.5 升级；修复弃用的 web search 配置和 OpenAI strict Structured Outputs Schema。
- 新增 `--local-login` Controller 模式：ChatGPT 登录、`ultra` reasoning、read-only sandbox；模型不直接执行 Windows 写命令，`.env` 不进入子进程。
- 无任务 canary 通过；fixture Harness 回归覆盖版本/哈希、隔离 workspace、图像循环、JSONL、凭据扫描与单次基础设施重跑。
- 从全新 public workspace 运行 `codex_local_gpt56_20260821_run1`，保留 raw JSONL、normalized hash-chain trajectory、fresh PNG、patch、manifest 和隐藏 evaluator 输出。
- 运行 `summarize_results.py`，同步更新机器可读 scores、对比、Case Study、最终报告与 README。

### 关键结论

- 本地 Codex 以 4 actions 完成一行等价补丁、1 次 fresh visual verification、public smoke 和 submit；耗时 63.078 秒。
- 自动评分为 Functional 45/45、Visual 35/35、Regression 20/20，总分 100/100，`task_success=true`。
- 10 个方向/分辨率主 case、动态目标、Threat、WASD、Objective completion、布局、节点、资产与输入哈希均通过；最低视觉点积约 0.99923。
- 历史 direct-write Codex invalid 继续保留；新结果证明 Controller action 可绕开 Windows `workspace-write` 阻断并正确评测模型。

### 当前风险

- 数据集仍只有 1 个合成任务，不能声称统计显著性或通用模型排名。
- Local Codex 与 Seed 成功 run 使用 public preload；Qwen 使用逐步探索，三者 input packaging 不完全一致。
- 实际任务运行使用 VS Code 扩展内 `codex-cli 0.149.0-alpha.4`；Harness 已在事后固定 npm native CLI 路径，但未为此重跑成功 attempt，以避免 best-of-n。
- Controller 是进程级白名单隔离，不等价于 VM/Windows Sandbox 级恶意代码隔离。

### 下一阶段输入

- 若需更严格的模型比较，从全新 workspace 为各模型统一 public preload、Schema、预算与 CLI pin，并预注册后各跑一次。
- 若需增强面试展示，新增 2–5 个同结构任务并报告 task-level success rate；现有 Task 001 和全部历史 run 不覆盖。
- 复现本地 Codex 时先运行 `codex login status`，再使用 `harness/README.md` 中的 `--local-login --preload-public` 命令；`run.json` 必须记录 CLI 路径与 SHA-256。

## 2026-08-21 — GameVisualFix v2 Task 002 Gate Blocker

### 当前阶段

**v2 统一 Harness / Task 002 Gate：已停止。Task 002 未通过 renderer Gate，后续 Task 003、Provider canary 与 9 次 canonical run 均未开始。**

### 已完成内容

- 已开始将 Controller action schema 扩展为统一接口：`scenario` 与其余字段同为 required，以支持 task-manifest 声明的公开 observation 场景。
- 已建立 Task 002 的独立 Godot public/private 目录、任务 Prompt、三个公开 observation 场景、18 个预声明隐藏组合及独立 evaluator 草案。
- 已完成一次 clean import/headless smoke 检查和一次允许的 renderer 诊断；完整技术证据与影响见 `benchmark/task_002/BLOCKER.md`。

### 关键结论

- 在本机 AMD Radeon + Godot 4.7.1 Windows/OpenGL Compatibility hidden-window 路径上，Task 002 的 capture 与 private suite 都在写出 PNG 前以 `3221225477` / `CrashHandlerException: signal 11` 结束。
- 将 HUD 三角形改为线段和圆点后故障不变，因此没有证据将其归因为任务逻辑、Oracle 或模型行为。
- 按 v2 计划的 Gate 规则，不能换引擎、改任务语义或对模型运行未通过 Gate 的任务；本轮自动流程到此停止。

### 当前风险

- v2 尚不具备三个可展示且验证完成的任务，任何“3×3”分数、模型成功率或难度结论都不能生成。
- Task 002 当前缺少 initial runtime evidence PNG，目录仅为被阻塞的实现草案，不能计入数据集。
- 旧 Qwen3-VL-Plus 当前树结果不得删除：新的 Qwen3.8-Max Task 001 canonical attempt 尚未有效完成。

### 下一阶段输入

- 需要用户明确批准并提供可验证的 Windows Sandbox/VM 渲染环境或其他 renderer 解决路径；随后从 Task 002 的 clean-copy Gate 第一步重跑。
- Gate 完成后才实现/验证 Task 003，随后执行三 Provider canary、9 次 canonical run、正式汇总和旧 Qwen 替换。

## 2026-08-21 — GameVisualFix v2 Task 002 Gate Recovered

### 当前阶段

**Task 002 已完成并通过 Gate；下一步为冻结统一 Codex Runner 后实现 Task 003。尚未运行任何 v2 模型实验。**

### 已完成内容

- 修复 Task 002 项目级 Windows/OpenGL 稳定性设置，重新生成 bug-state 初始 screenshot，并保留 renderer incident 记录。
- 完成 public prompt、三个 observation 场景、独立 private capture evaluator、18-case 隐藏矩阵与验证记录。
- 最终 Bug Seed 连续三次为 0/100；Reference Patch 连续三次为 100/100；所有 run 都覆盖 3 rotations × 2 zooms × 3 viewports。

### 关键结论

- 原 renderer crash 来自缺失的已验证 Godot project settings，而非 Task 002 题意、任务代码、Oracle 或模型行为。
- Objective 的 world/camera coordinate-space 混用会在多个相机状态下被图像方向 Oracle 稳定拒绝；Threat tracker 保持可见作为回归条件。

### 当前风险

- private evaluator 当前以每个隐藏组合的新进程 capture 和 image-derived color direction 实现，速度约 25 秒/18-case run；这是稳定优先的 P0 实现。
- Task 003、统一 canonical runner、Provider canary、9-run 矩阵与旧 Qwen 替换仍未完成，不能生成 v2 比较结论。

### 下一阶段输入

- 冻结 `run_codex_eval.py` 的 task-manifest dispatch，确保 Task 001/002 使用同一 Controller schema、预算、CLI pin 和 artifact contract。
- 随后实现并在模型接触前完成 Task 003 的 clean-copy Gate。

## 2026-08-21 — GameVisualFix v2 Task 003 Gate

### 当前阶段

**Task 003 已完成并通过 Gate；接下来实现统一 task-manifest Codex Runner，然后做 Provider canary 与 canonical matrix。**

### 已完成内容

- 新建独立 Echo Dash public/private Godot 任务，以 8-frame contact sheet 呈现 reversal 周围的 trail phase 错误。
- 实现 6 条 hidden replay × 30/60 fixed tick 的 12-case 像素 Oracle；任务不依赖视频、wall-clock 或 VLM judge。
- Bug Seed (`before`) 连续三次 0/100，Reference Patch (`after`) 连续三次 100/100；public Seed 已还原为 Bug 状态。

### 关键结论

- 任务的视觉区别集中在 reversal frame：trail 应在 Player 运动方向后方；bug 会短暂使用 previous facing 并出现在前方。
- 静止 interrupt frame 内紫色 trail 被 Player 覆盖属于正确视觉状态，evaluator 已显式处理而不把它误判为隐藏 trail。

### 当前风险

- Task 003 是最小化 fixed-replay 实现，尚未覆盖真实对象池、碰撞与完整 Dash 状态机；报告中必须如实称为 synthetic temporal visual repair task。
- 目前还没有 v2 canonical model run，因此不能比较模型能力或替换旧 Qwen 结果。

### 下一阶段输入

- 增加 `harness/run_codex_eval.py`，从 `task.json` dispatch Task 001/002/003 的 public package、Prompt、initial image、capture 与 private evaluator。
- 统一 Provider 配置/Canary 后按预注册顺序执行九次 single-attempt canonical run。

## 2026-08-21 — GameVisualFix v2 unified Codex Runner Gate

### 当前阶段

**统一 `run_codex_eval.py` 与 Provider canary 已通过；准备按预注册顺序启动 Task 001 的 Qwen3.8-Max canonical attempt。**

### 已完成内容

- 新增 manifest-dispatch Codex CLI Controller runner，支持 Task 001/002/003 与 `local_codex`、`seed_evolving`、`qwen38` 三个 Provider。
- 固定 npm native Codex CLI 0.149.0，使用 read-only sandbox、Controller allowlist、显式 thread resume、3 次 observation 上限、18 actions 与 task-local private evaluator。
- 无任务 canary 已验证三 Provider 的 32×32 PNG 感知、严格 JSON action schema、initial thread 与 resume；每次运行使用 run-local `CODEX_HOME`，结束后删除 provider session/config。

### 关键结论

- `--ignore-user-config` 会连同 run-local `CODEX_HOME` provider config 一起忽略并使 CLI 回退到 OpenAI；统一 Runner 不使用该冲突 flag，而保留 `--ignore-rules`、read-only sandbox、禁用 plugins/apps 与 sanitized environment。
- Qwen3.8-Max 对小于 11px 的图像拒绝请求，因此 canary 使用 32×32 无任务图像；Qwen 与 Seed 均已在当前 `.env` 配置下成功 Responses + resume。

### 当前风险

- Qwen CLI 会将未内置的 `qwen3.8-max` 以 fallback model metadata 运行；run manifest 会记录这一 Provider 限制，不能掩盖为官方 native Codex metadata。
- 旧 `harness/tests/self_test.ps1` 位于既有 PowerShell harness 分支；当前 PowerShell session 无 `powershell` executable alias，未把它作为统一 Python Runner 的 release gate。

### 下一阶段输入

- 从全新 workspace 使用 `run_codex_eval.py --task-id task_001 --provider qwen38` 运行唯一 canonical attempt；仅独立可复现的 Controller/CLI/provider/capture/evaluator基础设施故障允许保留 invalid 后重跑。
- 随后依序运行 Seed、Local Codex；Task 002 和 Task 003 使用同样 runner 与 frozen budgets。

## 2026-08-21 — Qwen Task 001 infrastructure invalidation

### 当前阶段

**Qwen Task 001 的第一次 v2 workspace/session 已标记 `invalid_infrastructure`；Harness feature gate 修复并通过无任务 Qwen canary，允许一次全新 rerun。**

### 已完成内容

- 保存首次 run 的 workspace、raw JSONL、patch、hidden evaluator 输出和 manifest；它没有提交 action，不能作为模型分数。
- 确认原因是 Codex CLI 的 `multi_agent` feature 未被先前参数关闭：Qwen 调用该工具后线程未产生最终 controller action。
- 在统一 Runner 和 canary 中显式禁用 `multi_agent`、browser、computer、shell、skill search、hooks、plugins 与 apps；修复后 Qwen image/schema/resume canary 通过。

### 关键结论

- 此次 invalidation 是由 Controller/CLI feature exposure 造成，独立于任务、模型补丁和 hidden evaluator，符合一次 fresh rerun 条件。
- 任何后续 Qwen Task 001 的无补丁、错误补丁、错误 action、超时或 task failure 都将是有效模型结果，不能再次重跑。

### 当前风险

- Qwen fallback metadata warning 仍存在，需在最终 manifest/report 中披露。
- 当前结果目录同时含 invalid run 与未来 canonical rerun，汇总器必须显式排除 `invalid_infrastructure`。

### 下一阶段输入

- 提交 Harness feature-gate 修复，从全新 output/workspace 启动 Qwen Task 001 的唯一 rerun；之后继续预注册顺序。

## 2026-08-21 — v2 automatic stop: Qwen Provider/CLI event stream

### 当前阶段

**自动流程已停止。Qwen3.8-Max / Task 001 连续两次为 `invalid_infrastructure`，未形成 canonical model score；Task 001 Seed/Local 与 Task 002/003 全部模型运行均未启动。**

### 已完成内容

- 保存两次 Qwen fresh workspace 的 `run.json`、规范化 controller trajectory、最终 patch 与 hidden evaluator 输出；raw provider event stream 不归档到 Git，避免保留模型内部 reasoning/event 文本。
- 首次 invalid 的 non-controller feature exposure 已修复并提交；第二次 fresh rerun 收到合法 JSON `read_file` action，但外部 Responses event 未提供 thread ID。
- 创建 `results/v2_infrastructure_log.md`，明确旧 Qwen 结果保留、没有 v2 分数以及自动停止原因。

### 关键结论

- Provider canary 成功不保证完整 prompt/event 流提供可 resume 的 Codex thread ID；这一差异必须作为 Harness/provider availability，而不是模型能力结果报告。
- 在不使用 `--last`、不伪造 thread ID、且不重跑超过规则上限的前提下，无法安全执行后续 controller turn，因此不能将未提交的 evaluator baseline 记为 Qwen 分数。

### 当前风险

- v2 有三个已验证任务和统一 Harness，但尚无有效 canonical matrix；不得生成 Task Success Rate、模型排名或替换旧 Qwen3-VL-Plus 结果。
- 继续运行 Seed/Local 会形成不完整的预注册矩阵，且违反当前计划在连续两次基础设施 invalid 后的停止规则。

### 下一阶段输入

- 需要一个明确批准的 protocol revision：允许经过验证的 Qwen session-ID adapter / Provider event normalizer，或变更为没有 resume 的单-turn controller contract；修复后应新建 v2.1 suite ID 并重新预注册全矩阵。
- 未获得该批准前，只可展示 Task 001/002/003 的 validation、canary 与 infrastructure log，不可展示 v2 模型分数。

## 2026-08-21 — v2 Seed + Local Codex 3×2 protocol revision

### 当前阶段

**已按用户明确指令跳过 Qwen3.8-Max；冻结 `gamevisualfix_v2_seed_local_3x2`，准备执行 Seed Evolving 与 Local Codex 在三个已验证任务上的六次 canonical attempt。**

### 已完成内容

- 保留 Qwen Task 001 的两次 `invalid_infrastructure` artifact 与基础设施日志，不将其错误地记作模型分数。
- 将统一 Runner 的 suite ID 参数化；新运行默认写入 `gamevisualfix_v2_seed_local_3x2`，使其不会混入原 3×3 预注册矩阵。
- 在实验协议中登记此次用户授权的范围缩减、有效 Provider、单次 attempt 规则与结果边界。

### 关键结论

- Seed 和 Local Codex 仍使用同一 Task manifest、public preload、Controller action schema、图片 observation、预算与 private evaluator；因此可形成受限但可复现的两模型 × 三任务比较。
- Qwen 的 provider/CLI event-stream 不兼容是 availability 记录，不是能力失败；本轮不再尝试规避或替换该 Provider。

### 当前风险

- 此 suite 不包含 Qwen，不能作为原计划的三模型结论；报告必须以“Seed + Local Codex 3×2”标示范围。
- 每个 Provider/Task 仍只接受一个 valid attempt；模型失败不重跑，只有独立可复现的基础设施故障可保留 invalid 后重跑一次。

### 下一阶段输入

- 使用更新后的 feature-disabled Runner 分别复验 Seed Evolving 与 Local Codex 的无任务 image/schema/resume canary；通过后按 Task 001、002、003 的顺序各执行 Seed、Local Codex 一次。

## 2026-08-21 — Seed Task 001 transport compatibility fix

### 当前阶段

**Seed Task 001 的首次 v2 attempt 已归档为 `invalid_infrastructure`；修复并验证多图 CLI 参数形状后，准备执行唯一一次全新 rerun。**

### 已完成内容

- 记录首次 attempt 未产生 `thread.started` 或 controller action，`valid_api=false`；未将 evaluator baseline 作为 Seed 分数。
- 审计到 Codex CLI 将 `--image` 定义为 variadic `--image <FILE>...`。统一 Runner 已由重复的单图 flag 改为一个 `--image` 携带全部 public preload 图。
- 对 Seed 执行无任务的三图 image/schema/explicit-resume canary，首轮与续轮均成功；无凭据、任务文本或 private artifact 进入 canary archive。

### 关键结论

- 首次失败只影响外部 Provider 的请求形状，和 Task 001、补丁、截图、Oracle 或 hidden evaluator 无关，符合一次基础设施 rerun 条件。
- 该修复同时使调用符合 Codex CLI 的 `--image <FILE>...` 接口；正式 rerun 仍使用完全相同的任务输入、预算、评分与 suite ID。

### 当前风险

- 若修复后的 Seed rerun 仍无 thread/action，则已达到该 Provider/Task 的两次基础设施失败上限，必须停止 Seed 后续任务并单独报告 availability blocker。
- 本地 Codex 尚未开始 Task 001；其 canary 已通过，且不受该外部 Provider 修复的能力结果影响。

### 下一阶段输入

- 使用 `harness/run_codex_eval.py` 与新的 output/workspace 运行 Seed Task 001 rerun；只在它有效完成后继续 Task 001 的 Local Codex 和后续任务。

## 2026-08-21 — v2 Task 001 execution outcome

### 当前阶段

**Task 001 已完成 Local Codex canonical run；Seed Evolving 因两次独立 workspace 的 transport invalid 被停止，准备继续 Local Codex 的 Task 002。**

### 已完成内容

- Seed Task 001 run1 与 run2 均保留。两次都在 API/CLI 传输层结束，缺少可用 `thread.started` 和 controller action；两者均为 `valid_api=false`、未提交，hidden evaluator 的 baseline 仅作为诊断 artifact，不计入分数。
- Local Codex Task 001 run1 从全新 public workspace 产生 7 个 Controller actions：读取 tracker/profile、最小化写入 Objective profile、public smoke、fresh `BASELINE` observation、submit。
- Local Codex run1 的 private evaluator 为 Functional 45/45、Visual 35/35、Regression 20/20，总分 100/100，`task_success=true`；耗时 106.032 秒，使用 1 次 fresh observation。

### 关键结论

- Task 001 的本地 Codex 成功由隐藏多位置/分辨率 Oracle 验证，而不是固定 diff；trajectory 的公开 action 记录支持“定位正确 profile 后进行最小根因修复”的解释。
- 即使多图参数形状已修正且 no-task 多图 canary 成功，Seed 的完整任务流仍只返回不符合 Codex 0.149 流式协议的 text delta。它是 Provider availability blocker，不能解释为 Seed 的能力失败。

### 当前风险

- 受限 suite 目前只有一个可计分 Local Codex run；Seed 不会继续 Task 002/003，以遵守连续两次 infrastructure invalid 的停止规则。
- Local Codex 的单个 Easy 成功不构成跨难度或模型比较；仍需运行冻结的 Medium/Hard 任务并如实报告可用性缺口。

### 下一阶段输入

- 固定同一 Runner、CLI、预算与隐藏评价器，运行 Local Codex Task 002 的唯一 canonical attempt；Task 003 仅在 Task 002 artifact 完整归档后启动。

## 2026-08-21 — Task 002/003 adapter-path infrastructure correction

### 当前阶段

**Local Codex Task 002 首次 run 已标记 `invalid_infrastructure`；正在修复并验证 Task 002/003 manifest 的 workspace-relative adapter 路径，随后允许一次全新 Local Codex Task 002 rerun。**

### 已完成内容

- 保存 Task 002 Local Codex run1 的完整 workspace、controller trajectory、patch、截图与 evaluator 结果；它的隐藏 Oracle 为 100/100，但不作为 canonical score。
- 定位到 `task.json` 的 `public/tests/smoke.gd` 和 `public/tools/capture.gd` 在 Runner 复制 public root 后会解析成不存在的 `res://public/...`。
- 已将 Task 002 与尚未接触模型的 Task 003 改为 workspace-relative `tests/smoke.gd`、`tools/capture.gd`；不改变 Prompt、bug、visual evidence、Oracle、阈值、资产或任务预算。

### 关键结论

- Task 002 run1 的两个 observation 和 smoke 均因 Controller/manifest 路径错误失败；模型没有获得成功的 post-patch visual feedback，因此必须按基础设施失败而非模型成功记录。
- 相同路径在 Task 003 若不预先修正也必然失败；提前更正是 shared Harness dispatch 修复，而非结果后调节任务难度或评分。

### 当前风险

- Local Codex Task 002 的 rerun 是其唯一一次 infrastructure rerun；任何模型补丁失败、预算耗尽或 hidden score 失败都将是有效模型结果。
- 该修复产生新的 Task manifest hash，rerun manifest 必须记录；Task 002 run1 的 artifact 保留以保持 failure lineage。

### 下一阶段输入

- 对 Task 002 与 Task 003 在 clean public copy 上执行 smoke/capture adapter preflight；通过后从全新 workspace 启动 Local Codex Task 002 rerun。
