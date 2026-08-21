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
