# Step 2：Research Gap 与研究问题

> 状态：研究问题已冻结，供 Step 3 选择候选任务。本文只定义研究边界、可观察证据与反证条件，不设计具体 Benchmark Task，不实现代码。

## 1. 决策摘要

本项目定位为一个**受控的单任务 case study**，而不是新的大规模 Benchmark。最终选择如下：

- **Main RQ：Hypothesis B — Closed-loop Visual Debugging。**关注 Agent 是否真实接收 Patch 后新生成的 runtime visual observation，并用它完成验证；若验证失败，再观察其是否改变定位、计划或编辑并恢复。
- **唯一 Secondary RQ：Hypothesis C — Process-level Diagnosis。**用预注册阶段标签解释 Seed 模型与外部模型的差异最早出现在哪里，以及该差异如何传播到最终结果。
- **Validity gate：Hypothesis A — Task-essential Visual Evidence。**它约束任务是否合格，但不作为本次独立 Research Question，也不以单任务宣称视觉输入具有普遍或因果意义上的必要性。

这一选择的价值不在于声称“首次”提出视觉修复、闭环调试或 trajectory diagnosis，而在于把以下元素放进同一个可审计案例：现有游戏代码仓库、初始 runtime 视觉症状、Patch 后 fresh observation、确定性 outcome Oracle，以及阶段化轨迹解释。

## 2. Evidence boundary

### 2.1 本研究可以支持什么

在同一任务、同一 Harness、同一工具权限和尽可能一致的运行环境下，本研究可以报告：

1. Seed 模型与一个外部模型在**该任务、该次运行**中的最终功能、视觉和回归结果；
2. 每个模型是否执行了可观察的 `Observe → Patch → Run → Fresh Observe → Verify` 行为；
3. 在已有可验证失败的前提下，是否出现 `Fresh Observe → Re-plan/Re-localize → New Patch`，以及随后是否通过全部 outcome gates；
4. 两条 trajectory 中最早有充分证据支持的阶段差异，以及该差异与后续工具动作、Patch 和最终结果的时序关系；
5. Oracle 之间是否一致，以及本案例中存在的渲染波动或判定歧义。

### 2.2 本研究不能支持什么

单任务、每模型一次正式运行不支持以下结论：

- 统计显著性、模型总体排名、跨仓库或跨游戏类型的能力外推；
- “视觉输入导致更高成功率”或“fresh screenshot 导致恢复”等因果结论；
- 严格的信息论必要性，或视觉证据对所有模型、所有 Agent 配置都必要；
- 视觉 judge、阈值或阶段 taxonomy 的普遍可靠性；
- “首个视觉代码修复 Benchmark”“首次闭环视觉调试”或“首次进行过程诊断”等首创声明。

因此，本文中的“利用”“驱动”和“错误传播”均指**可观察轨迹所支持的案例级行为序列**。若 fresh observation 与后续改变之间缺少可审计证据，应标记为 `Ambiguous`，而不是补写因果解释。trajectory 用于解释结果，不替代 outcome Oracle；模型自述或不可见 chain-of-thought 也不构成成功证据。

## 3. 从已有工作到本项目边界

详细的一手来源与版本边界见 [Step 1 文献综述](./literature_review.md)。与本次决策最相关的约束如下。

| 候选假设 | 已有覆盖 | 尚可检验的窄边界 | novelty 判断 | 面试价值 | 一天 P0 可行性 | 决策 |
| --- | --- | --- | --- | --- | --- | --- |
| A：Task-essential Visual Evidence | SWE-bench Multimodal 已有人类必要性标注与有/无图条件；多模态 repair/localization 也已有近邻工作 | 在一个现有游戏仓库中，通过文本泄漏审计与可辨识性审查，保证初始 runtime 画面提供非冗余的 Bug 证据 | 低至中；领域迁移本身不足以构成 gap | 高；能说明任务为何真正需要多模态 | 中；严格必要性难由一个模型实验建立 | 降为 validity gate |
| B：Closed-loop Visual Debugging | VAB-CSS 已有反复截图编辑；GameCraft-Bench 已观察到生成期 screenshot debugging；SVRepair 与 FailureMem 已覆盖相邻的验证/恢复机制 | 在现有游戏仓库 repair 中，审计 Patch 后 fresh runtime observation 是否进入同一 Agent 上下文、是否伴随验证，以及失败后是否出现新的定位/计划/编辑 | 中；是受控组合边界，不是宽泛首创 | 很高；直接覆盖工具使用、运行、验证和失败恢复 | 中高；单任务可实现，但 Recovery 可能不被触发 | **Main RQ** |
| C：Process-level Diagnosis | GUIRepair、SVRepair、MM-IssueLoc、CUADebug 等已覆盖视觉定位、模块化修复或多模态轨迹诊断 | 在同一游戏 repair case 中，以预注册阶段找出两模型最早的证据化差异并追踪其下游影响 | 低至中；通用方法并不新 | 很高；直接回应 HR 对 trajectory、强弱项和 Case Study 的要求 | 高；复用正式运行轨迹，不需新增模型调用 | **唯一 Secondary RQ** |

### 3.1 G1–G5 取舍

| Gap | 处置 | 理由与约束 |
| --- | --- | --- |
| G1：游戏仓库中的 task-essential visual symptom repair | 并入 A，作为任务有效性 Gate | 它是 Main RQ 成立的前提，但单任务不能把严格视觉必要性升级为普遍研究结论。P0 做设计审计，不把模型无图失败当作必要性的证明。 |
| G2：Patch 后新 runtime observation 驱动再次规划与恢复 | 选为 Main RQ | 与 HR 要求的运行、调试、验证、恢复最贴合，也能用同一条 trajectory 审计。将“驱动”收窄为有证据的时序关联，不声称因果。 |
| G3：端到端阶段级错误传播 | 选为唯一 Secondary RQ | 一天内可复用两条 trajectory；但必须预注册阶段和歧义规则，并限定为 case-level diagnosis。 |
| G4：时序/交互视觉证据必要性 | 延后 | 固定输入 replay、帧时序、瞬态画面和渲染确定性的成本过高，容易牺牲 P0 完整度。Step 3 不把复杂时序交互设为必选条件。 |
| G5：视觉 Oracle 的一致性与可审计性 | 降为评测设计约束 | 固定环境、重复截图和 Oracle 分歧记录是质量控制，不是本次独立 RQ；一个任务不足以评价 judge 的普遍可靠性。 |

## 4. 冻结的 Research Questions

### 4.1 Main RQ — Closed-loop Visual Debugging

> 在相同 Agent Harness、工具权限和运行环境下，Seed 模型与外部模型能否利用每次 Patch 后新产生的 runtime visual observation 验证现有游戏仓库中的视觉修复；当验证失败时，能否据此重新定位、调整 Patch 并最终恢复到功能、视觉和回归均正确的状态？

这里的“能否”只在本次单任务 case study 中回答。Main RQ 包含两个可分开报告的部分：

1. **Verification：**每次候选 Patch 后是否实际运行并看到 fresh observation，再结合可见检查判断结果；
2. **Conditional Recovery：**只有已出现可验证的失败或不完整修复时，才评价是否重新定位、改变 Patch 并最终通过全部 outcome gates。

若首个 Patch 已通过全部 gates，则 Verification 仍可评价，Recovery 必须记为 `N/A (not triggered)`，不能人为制造失败，也不能将其记作恢复成功。

### 4.2 Secondary RQ — Process-level Diagnosis

> 两个模型的结果差异最早出现于 Visual Perception、Code Localization、Editing、Runtime Verification 还是 Recovery 阶段，这些阶段性错误如何传播到最终正确性？

Secondary RQ 只解释可观察轨迹。若某阶段没有发生、证据不足，或两模型没有可判定差异，应分别报告 `N/A`、`Ambiguous` 或“未观察到差异”，不能为了形成故事而强行指定根因。

### 4.3 Hypothesis A — Validity gate，而非 RQ

任务进入正式实验前，初始 runtime screenshot 必须通过以下 Gate：

- 它展示的是当前错误运行状态，而不是答案图、目标图或装饰性素材；
- 任务文本不直接命名损坏对象、文件、节点、属性、正确数值或 Patch；
- 文件名、资源名、注释和可见测试不泄露唯一修复路径；
- 仅凭任务文本和静态可见工作区，审查者不能唯一确定 Patch；初始画面应在至少两个合理候选解释之间提供区分证据；
- 画面证据与功能/视觉 Oracle 指向同一个用户可见问题，但 Oracle 的隐藏实现不对 Agent 泄漏答案。

该 Gate 是本项目对“task-essential”的**操作性要求**，不是严格必要性的理论证明。可选的 no-image run 只能作为 exploratory sanity check：无图失败不能证明必要性；无图成功则会反驳“对该模型和该任务设置严格必要”的强说法，并触发任务重新审查。

## 5. Operational definitions

| 术语 | 本项目中的操作性定义 | 不计入的情况 |
| --- | --- | --- |
| Existing game repository | 可运行、已有多个相关文件/资源和既有行为的小型游戏项目；Agent 执行 repair，而非从空目录生成产品 | 空项目、纯单文件算法题、只生成截图 |
| Initial runtime visual evidence | 在未修复版本上由固定环境生成并明确提供给 Agent 的当前状态画面；它通过 §4.3 Gate | 目标图、README 插图、只供 evaluator 使用的图 |
| Patch | Agent 对仓库产生的一个可区分候选变更；用 diff 与时间戳界定版本 | 只讨论方案、只打开文件、未落盘修改 |
| Fresh runtime observation | 在当前 Patch 落盘后，以新的运行进程和固定捕获条件产生，并真实进入 Agent 可见上下文的画面 | 复用初始图、缓存旧图、只生成但不展示给 Agent、仅 evaluator 可见 |
| Runtime visual verification | Agent 在 Patch 后启动项目、接收 fresh observation，并对修复状态采取可观察的检查或后续动作 | 仅声称“应该修好”、只跑静态检查、只在最终评分时截图 |
| Verification failure | 当前 Patch 经预声明的功能、视觉或回归 Oracle 判定未完全通过；或 Agent 明确观察到仍有异常且该观察可由 artifact 核验 | 仅凭模型自述失败、无证据的猜测、Harness 故障 |
| Re-plan / re-localize | 在 fresh observation 后，公开输出或工具动作显示 Bug hypothesis、检查位置、计划步骤或编辑目标发生实质变化 | 原命令原样重跑、无关浏览、同一 Patch 的格式改动 |
| Recovery | 已有可验证失败；之后 Agent 收到 fresh observation，进行实质不同的定位/计划/编辑；后续 Patch 通过全部 mandatory outcome gates | 首轮成功、没有 fresh observation、最终仍失败、仅重复同一修改 |
| Functional correctness | 预声明的确定性检查确认游戏状态/交互逻辑满足任务要求 | 画面“看起来差不多”、模型自评 |
| Visual correctness | 在固定 viewport、状态、时刻和渲染条件下，预声明的可重复视觉检查通过 | 临时人工印象、未固定窗口的截图、仅 VLM 自由打分 |
| Regression correctness | 与目标 Bug 无关但容易被错误 Patch 破坏的既有行为仍通过预声明检查 | 只验证目标症状消失 |
| Trajectory evidence | 带顺序的可见输入、工具调用、文件读取、diff、命令、stdout/stderr、截图、Oracle 结果和时间信息 | 私有 chain-of-thought、事后臆测、无 artifact 的口头总结 |

## 6. 证据映射与反证规则

### 6.1 Main RQ 的最小证据链

Main RQ 的完整闭环证据按以下顺序审计：

`Initial observation O0 → Repository inspection/localization → Patch P1 → Fresh run R1 → Fresh observation O1 → Verification → [若失败] changed hypothesis/location/edit → Patch P2… → Final outcome gates`

| 待判断现象 | 支持证据 | 反证、降级或不可评价条件 |
| --- | --- | --- |
| Agent 使用了初始视觉证据 | O0 确实进入上下文，后续可见描述/检索/定位与 O0 中可核验特征一致 | O0 未送达；动作完全不依赖其可见信息时只能记 `Ambiguous`，不能从最终成功倒推“使用过” |
| 发生 Patch 后视觉验证 | P1 后启动新进程，产生 O1，O1 进入 Agent 上下文，随后存在可见检查或决策 | 复用 O0；只由 evaluator 截图；只运行未查看画面；先查看后 Patch 均不成立 |
| fresh observation 后发生 replanning | O1 暴露的残留/新问题与随后改变的 hypothesis、检查位置或编辑目标存在可核验对应 | 单纯重跑、同样修改、改变发生在 O1 之前，或无法判断改变依据时记 `Ambiguous` |
| 发生成功 Recovery | 已确认 P1 未完全通过；满足 fresh observation 与实质性改变；后续 Patch 同时通过功能、视觉、回归 gates | 首轮全通过时为 `N/A`；缺任一前置条件或最终未全通过均不记成功 |
| 最终修复正确 | 三类 mandatory outcome gates 全部通过，且由 evaluator 独立复核 | 任一 gate 失败即不算 complete；模型自称完成不改变判定 |

报告时区分四种闭环结果，避免把“没机会恢复”混为失败：

- `Verified recovery`：完整满足失败后恢复证据链并最终全通过；
- `Attempted but unsuccessful recovery`：满足恢复尝试前置证据，但最终未全通过；
- `Verification only; recovery N/A`：首个被完整验证的 Patch 已全通过；
- `No auditable visual loop`：没有 fresh observation 进入 Agent 上下文，或证据链不足。

### 6.2 Secondary RQ 的阶段证据

阶段编码在查看模型结果前固定，单条 trajectory 的每阶段取 `Pass`、`Fail`、`Ambiguous` 或 `N/A`。最早差异只能来自两模型中**最早具有充分可观察证据且标签不同**的阶段。

| 阶段 | 可观察证据 | 典型失败证据 | 传播分析边界 |
| --- | --- | --- | --- |
| Visual Perception | Agent 实际接收画面；公开描述或随后动作正确对应可核验的视觉症状 | 误认对象、方向、层级或状态，且后续动作与误认一致 | 只能说与后续定位/编辑在时序上相符；自述单独不足以定根因 |
| Code Localization | 搜索、读取并锁定与症状机制相关的文件、节点、资源或属性 | 持续检查无关位置，或遗漏决定性路径 | 若感知已 `Ambiguous`，不得武断归因“感知导致定位失败” |
| Editing | diff 可构建，且修改语义与当前 hypothesis 一致并保持合理范围 | 语法/加载错误、修改错误对象、硬编码表象、引入回归 | 由 build 与 outcome gates 判断效果，不以 Patch 大小替代正确性 |
| Runtime Verification | Patch 后运行、fresh observation 送达并进行检查；相关 Oracle 结果被记录 | 未运行、未查看新图、忽略明确失败、过早结束 | Harness 或渲染故障单列为基础设施问题，不计模型能力失败 |
| Recovery | 在已验证失败后出现实质性新定位/计划/编辑，并继续验证 | 重复无效 Patch、放弃、扩大无关修改或最终仍不通过 | 首轮成功为 `N/A`，不是 `Pass`；证据不足为 `Ambiguous` |

“错误传播”只记录为证据链，例如“错误对象识别 → 搜索错误场景节点 → Patch 未改变 Oracle 状态 → 未恢复”。如果中间箭头缺少 observable evidence，就拆成多个独立观察，不使用因果连接词。最终报告同时保留原始事件索引、关键 diff、截图 ID 和 Oracle 结果，以便复核。

### 6.3 Validity gate 与 Oracle 的反证

- 若独立文本泄漏审查能从 task description、命名或可见测试唯一还原修复位置和正确值，A Gate 失败，任务应在正式运行前重写或淘汰。
- 若初始 screenshot 未提供可区分信息，或仅展示期望答案，A Gate 失败。
- 若 no-image exploratory run 在同一可见信息下稳定得到唯一正确 Patch，应降低“task-essential”措辞并复查泄漏；该结果不影响如实报告，但不能被忽略。
- 若固定条件下重复捕获产生足以改变视觉判定的波动，visual Oracle 不合格；需在 Step 4 修正捕获条件或换用更稳定的语义检查。
- 若功能、视觉、回归 Oracle 互相冲突，分别报告，不用任意加权总分掩盖分歧；mandatory gate 未全通过时不得判完整成功。

## 7. 一天内 P0 可行性

### 7.1 必做范围

- 仅 1 个小型、已有结构的游戏仓库 repair task；
- Seed 模型与 1 个外部模型各进行 1 次正式运行；
- 两者使用同一任务包、Harness、工具权限、预算与固定运行/截图条件；
- 至少包含功能、视觉和回归三类可重复 outcome checks；
- 保存完整可见 trajectory、每个候选 Patch、fresh screenshot 和 Oracle 证据；
- 用预注册阶段规则完成一个并排 Case Study。

### 7.2 主动舍弃

P0 不扩展到多任务排行榜、多 seed 方差、统计检验、复杂视频理解、长时交互 replay、VLM judge 校准、视觉通道因果消融或自动化根因分类器。no-image run 仅在核心链路完成且时间允许时作为 exploratory check，不能挤占两模型正式对比。

### 7.3 预期风险与预案

| 风险 | 预案 |
| --- | --- |
| 两个模型都首轮成功 | 正常报告 Verification；Recovery 对两者均记 `N/A`。不在看到结果后换题以制造差异。 |
| 两个模型都失败 | 保留失败轨迹，区分是否存在 fresh observation、replanning 和 recovery attempt；不把尝试误报为成功。 |
| 只有一个模型触发失败恢复 | 这是有效的 case difference，但不能外推为模型总体恢复能力排名。 |
| 模型未查看 fresh screenshot | Main RQ 对该轨迹记 `No auditable visual loop`，不使用 evaluator 的截图替它补齐证据。 |
| Harness/API/渲染故障 | 与模型能力分开标注；若破坏同环境可比性，则该 run 无效并按预声明规则重跑，而非修改评分。 |
| Oracle 分歧或画面抖动 | 保留分项结果，先修复确定性和重复捕获；不临时调整阈值迁就模型输出。 |

这个范围能在一天内产生一个完整、可复查的 P0，同时诚实接受 Recovery 可能 `N/A`。研究价值来自任务、Harness、outcome 与 trajectory 的闭环完整性，而不是样本规模。

## 8. Step 3 handoff

Step 3 应围绕已冻结的 Main/Secondary RQ 设计并比较 **3 个候选任务**，但不得重新扩大或改写研究问题。每个候选至少满足：

1. 来自可运行的小型现有游戏项目，修复目标是 repository-level change；
2. 初始 runtime screenshot 通过 §4.3 的 A Gate，并且文本不泄露对象、位置、正确值或 Patch；
3. Agent 可在每次 Patch 后以固定条件重新运行，fresh screenshot 能送入同一 Agent 上下文；
4. reference patch 小而可审计，同时存在至少一个合理但不完整的错误修复路径，以便自然观察验证与可能的恢复；这不意味着强制模型先失败；
5. 功能、视觉和回归 Oracle 可确定性执行，visual check 不以自由 VLM 判断作为唯一 mandatory gate；
6. 环境、viewport、初始状态、随机种子和捕获时机可固定，并能重复捕获验证；
7. 能保存完整工具轨迹、diff、stdout/stderr、截图和分项 Oracle 结果；
8. 实现与两模型运行成本适合一天 P0，且不是对已有 Benchmark 实例的直接复制。

候选比较维度固定为：`Multimodal Necessity`、`Agentic Depth`、`Evaluation Reliability`、`Model Discriminability` 和 `Implementation Cost`。以下情况应直接淘汰：

- 仅凭题面、文件名或可见测试即可唯一确定 Patch；
- screenshot 只是装饰、答案图，或对定位没有增量信息；
- 无法让 Agent 在 Patch 后获得 fresh runtime observation；
- 只能依赖主观人工观感或不稳定 VLM 分数判断正确性；
- 需要复杂时序 replay、不可控随机状态或超过一天的资产/引擎工作；
- 修复退化为单次文本生成，无法体现仓库理解、运行和验证。

Step 3 的交付只需说明三个候选如何满足这些约束、按五项维度排序并选出一个 P0 任务。具体任务实现、Oracle 代码、Harness 与模型调用仍留待后续阶段。

## 9. 冻结结论

本项目不把 A、B、C 并列成三个研究问题。A 负责保证输入确有多模态研究价值；B 是唯一 Main RQ；C 是唯一 Secondary RQ；G4 延后，G5 作为评测质量约束。后续阶段可以把这些定义实例化为任务、评分器和轨迹分析，但不得依据运行结果事后修改 Gate、阶段标签或成功标准。
