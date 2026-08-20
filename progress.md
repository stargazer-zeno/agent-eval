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
