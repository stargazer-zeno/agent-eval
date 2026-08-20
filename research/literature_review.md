# GameVisualFix：游戏多模态 Coding Agent 文献调研

> 阶段：Step 1
>
> 调研截止：2026-08-20
>
> 目标：识别现有工作已经测量的能力、尚未充分覆盖的组合，以及适合一天内验证的候选 Research Gap。本文不确定最终 Research Question，也不设计具体 Benchmark Task。

## 1. 调研范围与方法

### 1.1 范围

本次不是追求穷尽文献数量的系统综述，而是围绕 GameVisualFix 的三个初始假设进行定向核验：

1. 视觉信息是否可以成为完成仓库级修复所必需的任务证据；
2. Agent 是否已被评价过“观察画面—修改代码—重新运行—根据新画面恢复”的闭环；
3. 现有评测是否能解释 Visual Perception、Code Localization、Editing、Verification 与 Recovery 之间的错误传播。

核心游戏工作为 GameDevBench 与 GameCraft-Bench；GameEngineBench、OpenGame / OpenGame-Bench 用于补齐游戏 Coding Agent 的任务谱系；Design2Code、VisualAgentBench、SWE-bench Multimodal、GUIRepair、SVRepair 与 MM-IssueLoc 用于反证过宽的 novelty 表述。另以 CodeV、FailureMem 与 CUADebug 作补充边界检查，避免把多模态 issue repair、失败经验利用或阶段级根因诊断误写成本项目首创。

### 1.2 来源与版本规则

- 优先级为：论文原文 > 论文直接链接的项目页或作者仓库 > 其他材料。
- 论文中的实验结论按明确版本引用；仓库仅用于核验实现、文件隔离和开放状态。
- 仓库内容可能持续更新。若论文数字与当前 README 不同，以本文标注的论文版本为准，不拼接不同时间点的 leaderboard。
- “未发现”只表示在本次定向检索范围内没有找到完整覆盖，不等于证明整个领域不存在相关研究。
- 文中“事实”来自一手材料；“判断”与“机会”是基于这些事实的综合推断。

### 1.3 术语边界

- **Task-essential visual evidence**：移除图片、截图或帧序列后，任务文本与仓库不能唯一确定正确诊断或 Patch；视觉内容不是装饰或答案展示。
- **Runtime visual feedback**：Agent 在 episode 内运行当前程序并看到该次执行产生的画面，而不只是读取 issue 中的原始截图。
- **Closed-loop visual debugging**：至少包含 Observation → Edit → Run/Render → New Observation → Re-plan/Repair；只在最终评分端使用截图不构成 Agent 闭环。
- **Benchmark-level recovery**：评测协议显式保留并分析失败后的恢复，而不只是允许 Agent 在一次长轨迹中自由重试。

## 2. 一手来源登记

| 工作 | 本文采用的版本 | 论文 / 正式页面 | 官方代码或项目页 | 核验重点 |
| --- | --- | --- | --- | --- |
| GameDevBench | arXiv v2，2026-06-30 | [Paper](https://arxiv.org/html/2602.11103v2) | [GitHub](https://github.com/waynchi/gamedevbench) · [Project](https://waynechi.com/gamedevbench/) | Godot 任务、视觉工具、隐藏测试与轨迹 |
| GameCraft-Bench | arXiv v1，2026-06-16 | [Paper](https://arxiv.org/html/2606.17861v1) | [GitHub](https://github.com/FreedomIntelligence/gamecraft-bench) · [Project](https://tongxuluo.github.io/gamecraft-bench-website/) | 端到端生成、runtime replay、VLM judge 与过程分析 |
| GameEngineBench | arXiv v2，2026-07-15 | [Paper](https://arxiv.org/html/2607.03525v2) | [GitHub](https://github.com/Nitrode-Research/GameEngineBench) | 现有 Unreal 仓库、C++ runtime behavior 与隐藏测试 |
| OpenGame | arXiv v1，2026-04-20 | [Paper](https://arxiv.org/html/2604.18394v1) | [GitHub](https://github.com/leigest519/OpenGame) | Web game 生成、自修复与 OpenGame-Bench 开放边界 |
| Design2Code | NAACL 2025 | [Paper](https://aclanthology.org/2025.naacl-long.199/) | [GitHub](https://github.com/NoviScl/Design2Code) | Screenshot-to-code 与渲染相似性评价 |
| VisualAgentBench / VAB-CSS | arXiv v1，2024；ICLR 2025 | [OpenReview](https://openreview.net/forum?id=2snKOc7TVp) · [arXiv v1](https://arxiv.org/abs/2408.06327v1) | [GitHub](https://github.com/THUDM/VisualAgentBench) | 多轮 screenshot-driven CSS editing |
| SWE-bench Multimodal | arXiv v1，2024；ICLR 2025 | [OpenReview](https://openreview.net/forum?id=riTiq3i21b) · [arXiv v1](https://arxiv.org/html/2410.03859v1) | [Project](https://www.swebench.com/multimodal.html) · [GitHub](https://github.com/SWE-bench/SWE-bench) | 真实多模态 issue、图像必要性与隐藏测试 |
| GUIRepair / Seeing is Fixing | arXiv v1，2025；ASE 2025 | [Paper](https://arxiv.org/html/2506.16136v1) | [Project](https://sites.google.com/view/guirepair) | Image2Code、Code2Image 与视觉 Patch validation |
| SVRepair | arXiv v2，2026-08-03 | [Paper](https://arxiv.org/abs/2602.06090v2) | [GitHub](https://github.com/codefuse-ai/CodeFuse-SVR) | 结构化视觉表示、定位、Patch 与失败后迭代 |
| MM-IssueLoc | arXiv v1，2026-07-16 | [Paper](https://arxiv.org/abs/2607.15205v1) | [GitHub](https://github.com/Jasaxion/MM-IssueLoc-Bench) | 配对视觉条件下的文件/函数定位 |
| CodeV / Visual SWE-bench | Findings of ACL 2025 | [Paper](https://aclanthology.org/2025.findings-acl.384/) | [GitHub](https://github.com/luolin101/CodeV) | 视觉 issue 的两阶段处理与文本修复衔接 |
| FailureMem | arXiv v1，2026-03-18 | [Paper](https://arxiv.org/html/2603.17826v1) | [GitHub](https://github.com/Ruize-Ma/FailureMem) | 主动视觉定位、混合 Agent 与离线失败记忆 |
| CUADebug | arXiv v1，2026-07-31 | [Paper](https://arxiv.org/html/2608.02643v1) | — | 多模态 trajectory 根因步骤、taxonomy 与 re-rollout |

版本提示：SWE-bench Multimodal v1 的摘要写 617 个实例，而正文的数据构建与特征段写 619 个实例（517 test + 102 development）。本文不使用该总数支撑核心结论；涉及规模时同时提示这一原文内部差异。

## 3. GameDevBench 深入分析

### 3.1 Existing Work

GameDevBench 将在线 Godot 4 教程转化为 333 个局部开发任务，其中 154 个 core tasks、179 个 variants。数据来自 57 个可用 YouTube 教程和 31 个 KidsCanCode Recipes 教程；任务经过 Agent 辅助构造、自动 refinement 和 8 名人工标注者复核。每项任务提供现有 Godot 项目和自然语言要求，并保留经过验证的参考工程及隐藏 Godot 测试；82.4% 的任务还包含图片、字体、shader、音频或资源文件等额外资产。

任务不是从真实 GitHub issue / PR 历史直接挖掘，但具有仓库级上下文。参考解平均修改 4.7 个文件、3.2 种文件类型和 114.1 行，项目可能包含场景、GDScript、图片、字体、shader、音频与资源文件。论文按 2D graphics and animation、3D graphics and animation、UI、gameplay logic 分类。

### 3.2 What It Measures

**Agent 输入与操作**

- Baseline Agent 在隔离后的现有项目目录中接收文字任务，可检索文件、阅读代码与素材、编辑脚本/场景/配置并执行 shell 或 Godot。
- 论文比较 Claude Code、Codex、Gemini CLI 与 OpenHands 等本地 harness。原生 action schema 不完全相同，因此结果同时包含模型与 harness 差异。
- 任务配置、参考实现和隐藏测试不会进入 Agent 工作区；正式验证时才在独立 workspace 注入测试。

**Screenshot 与 runtime video**

- Editor Screenshot MCP 启动 Godot Editor，返回 Scene Tree、Inspector 和编辑器场景等状态；它不是玩家视角的 runtime screenshot。
- Runtime Video 使用 Godot 录制当前场景，包含摄像机视角和时序变化。模型通常把视频拆为图像帧，而非直接消费完整视频。
- 两类视觉工具都属于开发期反馈，不进入最终 scorer。论文 v2 中，GPT-5.4 在同时开放 Editor Screenshot MCP 与 Runtime Video 时从 41.1% 提升到 52.0%；其他模型、harness 和单独工具组合并非都稳定提升。

**Ground truth 与自动评测**

- runner 将 Agent 的最终项目复制到 validation workspace，再注入隐藏测试。
- Godot 测试检查节点结构、属性、方法、signal、碰撞、动画、camera、polygon 等 engine/runtime state。
- 任务以隐藏测试是否输出通过标记形成二元 pass@1；不使用 VLM judge，也没有视觉美学部分分。

因此它主要测量：在含多种资产和引擎约束的现有工程中理解需求、跨文件定位与修改、正确连接 Godot 对象，并产生能被确定性测试验证的功能状态。

### 3.3 Limitation

1. **视觉存在不等于截图是必要证据。** 任务说明仍以文本为主，论文也明确任务可完全通过代码解决；视觉工具是可选反馈条件。它没有逐任务证明“移除视觉证据后正确 Patch 不可确定”。
2. **最终视觉表象未被直接评分。** Godot state tests 可稳定验证 camera、animation、碰撞等结构和行为，但可能漏掉构图、遮挡、可读性或整体视觉一致性。
3. **不是标准化交互 playthrough。** runtime video 可观察时序结果，却没有 evaluator 控制的统一玩家输入 replay。
4. **没有 evaluator-feedback repair round。** 隐藏测试只在 episode 结束后注入，失败结果不会返回 Agent。
5. **trajectory 保存多、过程评分少。** 当前仓库 runner 会保存最终工程和 Agent 日志；token/cost 及结构化 tool/file-edit events 的完整度依赖具体 solver。论文使用 LLM-as-a-judge 对最终失败做非互斥 taxonomy，而没有执行标准化的阶段 trajectory/recovery audit。
6. **结果存在版本漂移。** 当前仓库可能继续新增模型或结果；论文 v2 的任务与实验数字必须和后续 README 排行榜分开解释。

### 3.4 Opportunity

GameDevBench 已证明“现有 Godot workspace + 隐藏 engine-state tests + 可选视觉反馈”是可运行的评测基础。GameVisualFix 可以进一步研究一个更窄的组合：让 runtime 画面成为区分多个可能根因的必要证据，并在保持参考 Patch、隐藏测试与 Agent workspace 隔离的同时，单独评价 Agent 是否观察、是否正确定位以及失败后是否利用新画面改变策略。

这只是候选机会，不能表述为“首次让 Coding Agent 看游戏截图”或“首次进行多模态游戏开发评测”。

## 4. GameCraft-Bench 深入分析

### 4.1 Existing Work

GameCraft-Bench 包含 140 个 Godot 2D 端到端生成任务，覆盖 15 个 game families。12 名标注者为每个任务编写自然、开放的产品式 specification 和隐藏 rubric，并实现最小 oracle，验证要求能在 Godot 中实现、能通过 replay 到达、且 rubric 对应可观察状态。

Agent 接收自然语言游戏规格、Godot 开发环境、可写 workspace、共享素材与辅助工具，从头交付完整 Godot 项目以及 1–10 条 demo replay traces。它不是已有项目上的定点 Bug repair。

### 4.2 What It Measures

**Agent 输入与操作**

- Agent 可创建场景、脚本、input mapping 和项目配置，选择并复制素材，运行游戏、截图、继续修改。
- replay trace 包含定时键鼠事件和可选 scenario identifier；如果生成项目实现了对应初始化逻辑，就可直接进入 battle、late-game 等特定状态。
- 隐藏 rubric 不对 Agent 可见；Agent 需要同时完成项目和展示行为的 trace，因而也测量交付协议遵循能力。

**运行画面与交互式验证**

- 开发期 Agent 可以运行当前游戏并调用 screenshot helper，形成“实现—渲染—观察—修改”的内部闭环。
- 评测期先经过 build gate；随后每条合法 trace 在新的 Godot 进程中回放，固定 1280×720 viewport，通过键鼠事件驱动游戏，录制视频并以约 2 FPS 抽帧。
- 论文 v1 将 replay 视频与抽帧统称为 gameplay evidence；截至 2026-08-20，当前 OpenAI/GPT backend 实际只向 judge 发送最多 40 张按时间排序的 PNG 帧，原始 MP4 作为运行与审计 artifact 保留。

**评分**

- 论文 v1 中，项目无法启动，或提交的 trace 无一可解析时，BUILD=0、总分为零；单条 replay 失败会被跳过，其他合法 demo 仍可评分。当前仓库实现略有差异：无有效 demo 时 build_ok 可能仍为真，但所有 rubric item 因无证据得零，最终总分仍为零。
- 多模态 judge 按隐藏 rubric 分别评价 Core Mechanics、Content Depth、Functional Visuals、Art & Presentation。
- 总分为 build gate 乘以四项加权结果；论文默认权重依次为 0.15、0.35、0.15、0.35。
- scenario-specific requirement 在多个 demo 间取 max；persistent requirement 取 mean。

**过程观察**

论文不只报告最终分数，还统计 rendered-screen inspection 和 tool use。Kimi-K2.6 在 140 个任务中进行了 2,998 次画面检查，平均 21.41 次、中位数 19；案例显示其通过多次截图修正 grid alignment 和 selection highlight。对 MiMo-V2.5-Pro 的 140 个任务，total tool calls 与得分的相关系数约为 +0.016；这说明在该配置上增加动作量不是更高质量的充分条件，不能外推为所有模型的统一规律。

### 4.3 Limitation

1. **任务是 generation，不是 repair。** 视觉反馈用于把文本规格逐步实现为完整游戏，不能隔离“从视觉症状定位既有代码根因”的能力。
2. **任务输入中的视觉并非必要条件。** 初始 specification 是文本；截图是 Agent 主动运行后的反馈。该工作证明了 perception-guided iteration 的存在，但没有受控地比较同一任务有无必要视觉证据。
3. **评分反馈不回流 Agent。** 隐藏 rubric 和 judge verdict 在 episode 后使用，因此不存在 judge failure → Agent re-plan → re-evaluate。
4. **VLM judge 与稀疏抽帧有测量误差。** 快速瞬态可能被漏采；“看起来发生”也不一定等于逻辑因果正确。论文做了固定证据重复评分和小规模 human calibration，但仍存在模型版本漂移与边界视觉判断。
5. **Agent 自写 replay 引入覆盖风险。** 论文观察到部分可运行提交因未交 demo trace 而得零；合法 trace 是否会选择性展示有利状态、隐藏未修复失败，则是潜在风险，不是论文已验证结论。
6. **过程分析尚未形成恢复指标。** 已有截图调用统计和典型案例，但没有标准化 recovery rate、首次错误 Patch 后改善幅度或阶段级 error propagation。
7. **缺少确定性提交级 mechanics/state oracle。** 除 launch/build gate 外，模型提交没有类似 GameDevBench 的隐藏 mechanics/state unit tests；minimal oracle 只用于任务构造与质量验证，不参与提交评分，因此 rubric 正确性主要依赖 replay 中可见证据与 VLM 判断。

### 4.4 Opportunity

GameCraft-Bench 已提供 runtime screenshot 工具，并在部分 Agent 轨迹中观察到多轮 perception-guided debugging；但它没有把该闭环设为强制受控变量或独立恢复指标。因此不能主张“首次出现这种行为”，仍可研究受控、可归因的视觉恢复评测。可借鉴的是固定 viewport、固定输入 trace 的可复现 replay、可选 scenario 的确定性状态初始化、每条 replay 独立进程、保留视频/帧/rationale，以及把视觉和功能分项评分。

更窄的候选空间是：把 evaluator 控制的 replay 用于稳定复现一个现有项目中的视觉 Bug；要求 Patch 后产生新画面，并分析新观察是否触发重新定位和恢复；最终同时以确定性状态测试和视觉证据验证，而不是完全交给 VLM。

## 5. 其他游戏 Coding Agent 工作

### 5.1 GameEngineBench

GameEngineBench 在 9 个真实开源 Unreal Engine 项目上构造 110 个任务。Agent 接收可构建项目、纯文本行为规范和允许编辑的 C++ 文件列表，在既有架构中实现缺失的 runtime behavior。完成后才注入隐藏测试，经编译、PIE listen-server automation 和 LLM judge audit 判定单次 pass@1。

它补足了原生 C++、multiplayer authority、replication、object lifecycle 与 subsystem integration，却不向 Agent 提供截图或视频，也不允许用隐藏测试失败进行第二轮修复。论文只对部分 wrapper-visible trajectory 统计编译调用与错误，且明确提示不同 harness 的 trace 完整度不可直接等同。因此它是“真实引擎仓库 + 行为测试”的强参考，但不是视觉调试基准。

### 5.2 OpenGame / OpenGame-Bench

OpenGame 面向从自然语言生成完整 2D Web game。OpenGame-Bench 使用 150 个自包含文本 prompt；没有 starter repository、参考实现或截图输入。Agent 可基于模板和素材工具创建多文件 Phaser 项目，并通过 build/test/run 错误进入有限自修复循环。

评测端以 headless browser 运行项目，使用 Build Health、Visual Usability 和 Intent Alignment 三项指标；截图、像素/运动启发式与 VLM 用于判断最终输出。论文没有证明这些视觉 verdict 或新截图会返回 Coding Agent，所以不能把其自修复等同于 screenshot-driven repair。构建、HTTP 服务、fatal runtime error 或非空截图的前置条件不满足时，该次运行被单列为 pipeline error；论文主表报告 valid runs 上的均值，跨 benchmark 比较时需保留这个分母条件。

OpenGame agent framework repository 已公开；但官方 [README 固定版本](https://github.com/leigest519/OpenGame/blob/c54307efe1dab927e7fc52dbb92af6b3df1d1c66/README.md) 截至 2026-08-20 仍称 OpenGame-Bench evaluation pipeline “will be released soon”。论文给出了高层协议和实验结果，但不能据此认定完整 pipeline implementation 已公开或可独立复现。

## 6. 多模态代码生成与视觉修复近邻

### 6.1 Design2Code

Design2Code 使用 484 个真实网页截图评价 MLLM 将视觉设计转换为 HTML/CSS 的能力，并用 CLIP、Block-Match、Text、Position、Color 等自动指标与人工评价比较渲染结果。其 self-revision 条件把目标截图、text-augmented prompting 生成页面的截图及对应代码一并提供给模型，再进行一次修订。

它证明了参考图—渲染图比较和细粒度视觉指标的价值，但任务主要是静态网页重建，不包含真实仓库探索、运行时交互、代码定位、测试反馈或长程恢复。因此它适合提供视觉评分方法的反例和参考，不足以代表 Coding Agent debugging。

### 6.2 直接约束 novelty 的工作

**VisualAgentBench / VAB-CSS**

VAB-CSS 已实现多轮 target/current screenshot → CSS rule edit → new screenshot，并提供 revert；主设置最多进行有限轮编辑。它是 screenshot-driven editing 的直接先例，但 Bug 通常是受控的单个 CSS 属性，动作空间抽象、目标截图始终已知，也不要求终端、仓库定位、功能测试或游戏运行时状态。

**SWE-bench Multimodal**

SWE-bench M 从真实 JavaScript GitHub issue / PR 构造仓库级修复任务，问题或测试中含图片/视频，并用 fail-to-pass 与 pass-to-pass tests 判定 resolved。人工标注在 557 个带 issue 图片的实例中把 465 个（83.5%）标为图片对求解必要；有图/无图的 Agent 配置实验只在 development split 上进行。因此，它足以否定“软件工程领域尚未研究图像必要性标注或有图/无图性能差异”的宽泛说法，但不能逐实例证明文本与仓库在信息论意义上无法唯一确定 Patch；本文 §1.3 的严格 task-essential 定义仍是待检验假设。其领域集中在 Web/UI，而不是游戏引擎的场景树、资源、动画、物理与摄像机状态。

**GUIRepair**

GUIRepair 的 Image2Code 从 issue 图像和项目知识生成复现代码，辅助故障理解与定位；Code2Image 运行补丁、捕获 GUI rendering，并用视觉结果筛选候选 Patch。它已经把 visual symptom、localization、patch generation 与 visual validation 接起来，但主要是流水线式候选生成/筛选，不等同于同一 Coding Agent 根据每轮新画面重新规划。其 Code2Image 执行环境也不是完全自动复现：作者手工安装项目依赖、构建前端，并把构建后的 JS package 导入复现 HTML；因此相关视觉验证结果还包含人工环境配置这一前提。

**SVRepair**

SVRepair 将截图等视觉 artifact 转换为结构化 semantic scene graph，驱动 Coding Agent 定位和生成 Patch。候选 Patch 未通过测试时，下一轮会收到 test/compile logs，并用原始视觉 artifact、issue 与上一轮定位出的代码片段裁剪出更聚焦的区域；实验最多三轮。它是“多模态仓库修复 + 失败后迭代”的强近邻，但视觉 refinement 仍主要重用原始 artifact，而非观察 Patch 执行后新渲染的画面。论文报告的 held-out Pass@1 是最终 benchmark test 结果，需与循环内部的 validation 区分；其评价也未覆盖完整游戏链路的阶段错误传播。

**MM-IssueLoc**

MM-IssueLoc 提供 652 个 issue–PR 实例的文件级 gold labels，其中 343 个实例另有函数级 labels，并提供 text-only / with-image 配对设置，专门测量视觉证据对 repository-level localization 的作用。Gold 来自 human-vetted fixing PR 的编辑位置；新增函数因不存在于 pre-fix snapshot 而被排除。论文也明确该标签是可扩展、可审计的 edit-scope proxy，不是最小因果根因。它不生成或验证 Patch。由此，“Visual → Localization”不是空白；剩余问题是定位结果如何影响后续编辑、运行时验证和失败恢复。

### 6.3 补充边界检查

- **CodeV / Visual SWE-bench**：CodeV 先把 issue 中的图片/视频转成细粒度描述或结构化文本，再交给文本 issue-resolving 方法生成 Patch。它进一步确认“视觉 issue → 仓库修复”已有先例，但没有把 Patch 后新渲染画面作为下一轮 observation。
- **FailureMem**：FailureMem 结合受控 localization workflow、Agentic patch generation、Crop/Grounding 工具与失败记忆。其 memory bank 在离线阶段用历史失败 Patch 与 developer gold Patch 对比蒸馏，属于跨 episode 经验复用；这不同于同一 episode 内基于 Patch 后新 runtime 画面恢复。
- **CUADebug**：CUAErrorBench 对 204 条失败 OSWorld trajectory 标注 root-cause step、分层 taxonomy、证据、纠正策略与置信度，并测试 diagnosis-guided re-rollout。它证明多模态 Agent 的阶段级根因诊断与恢复已有直接研究；剩余候选边界必须限定为会修改代码并重新运行游戏仓库的链路，而不能声称通用 Agent trajectory diagnosis 为空白。

## 7. 统一比较矩阵

为避免一张超宽表掩盖差异，统一维度拆成“任务与视觉”和“评价与过程”两张矩阵。

### 7.1 任务、输入与视觉角色

| 工作 | 任务类型 | 起点 | Agent 初始输入 | 主要动作 | 视觉是否为必要输入 | Runtime / visual feedback |
| --- | --- | --- | --- | --- | --- | --- |
| GameDevBench | 局部功能实现 / 补全 | 现有 Godot 教程项目 | 文本要求、代码与场景；82.4% 含额外资产 | 检索、编辑、命令、运行；可截图/录制 | 未逐任务建立必要性；视觉工具可选 | Editor screenshot 与 runtime video 供 Agent 验证 |
| GameCraft-Bench | 完整游戏 generation | workspace scaffold + 素材池 | 文本产品规格 | 创建工程、选素材、运行、截图、提交 replay | 初始证据不是图片 | Agent 可查看 runtime screenshot；评测回放生成 MP4 并抽帧，当前 GPT judge 消费抽帧 |
| GameEngineBench | 缺失行为实现 | 现有 Unreal 仓库 | 文本规范、限定 C++ 文件 | 检索、编辑、编译 | 否 | 论文未定义 screenshot/video 输入或反馈通道 |
| OpenGame | Web game generation | 无 starter code；内部模板 scaffold | 自包含文本 prompt | 生成多文件工程、资产、build/test/run | 否 | 视觉主要用于最终 evaluator，未证明回流 Agent |
| Design2Code | 静态 screenshot-to-code | 空白网页实现 | 目标截图 | 生成 HTML/CSS；一次 self-revision | 是 | 渲染图用于比较，不是仓库级运行调试 |
| VAB-CSS | 受控 CSS repair | 损坏网页 | 目标/当前截图、HTML，主设置含差异描述 | 定位/编辑 CSS rule、revert | 视觉核心；文本差异会降低纯视觉性 | 每轮编辑返回新截图 |
| SWE-bench M | 真实 issue repair | 现有 JS 仓库 | issue 文本、图片/视频、仓库 | 检索、编辑、命令、浏览器/图像工具 | 465/557 经人工标为必要；非逐实例不可识别性证明 | Agent 可复现/截图，但不是统一强制闭环 |
| GUIRepair | 多模态 APR | 现有前端仓库 | issue、图片、仓库知识 | 复现、定位、候选 Patch、渲染筛选 | 是核心信号 | patched GUI rendering 用于 validation；执行环境含人工配置 |
| SVRepair | 结构化多模态 APR | 现有仓库 | issue、视觉 artifact、代码 | 结构化视觉、定位、编辑、验证 | 是核心信号 | test/compile failure 后裁剪原 artifact；非游戏新画面闭环 |
| MM-IssueLoc | issue localization | 现有多语言仓库 | issue、可选图片、只读仓库 | 检索并排序文件/函数 | 作为受控变量 | 652 个文件级、343 个函数级 edit-scope labels；无编辑或新画面 |

### 7.2 Ground truth、评分与恢复

| 工作 | Ground truth / evaluator | 侧重 | 失败反馈是否回流 | Recovery 评价 | Trajectory / 错误传播 |
| --- | --- | --- | --- | --- | --- |
| GameDevBench | 参考工程 + 隐藏 Godot tests；二元 pass@1 | localized implementation / completion | 隐藏测试不回流 | 未单列 | runner 保存日志，完整度依 solver；论文以 final-state failure taxonomy 为主 |
| GameCraft-Bench | 隐藏 rubric；build gate + Agent 提交的 replay frames + VLM judge；minimal oracle 只用于任务构造/QC | end-to-end generation；debugging 是过程现象，未独立评分 | judge 不回流 | 未单列 | 有截图/tool 统计与案例，无完整阶段评分 |
| GameEngineBench | 参考解 + 隐藏 PIE tests + judge audit | runtime behavior implementation | 不回流 | 未单列 | 仅有限编译诊断 |
| OpenGame | build/runtime checks + 视觉启发式 + VLM | generation / self-correction | build/test 错误回流；视觉 verdict 未证实 | 有迭代消融，无视觉恢复指标 | 无公开逐步视觉错误传播分析 |
| Design2Code | 自动渲染相似指标 + human evaluation | generation / 一次 revision | 仅 self-revision 条件 | 非通用恢复 | 无仓库 trajectory |
| VAB-CSS | SSIM / success 与 improvement | 受控 visual editing | 新截图回流 | 支持多轮与 revert | 有动作序列，但 Bug 与动作空间较窄 |
| SWE-bench M | F2P + P2P tests，部分 pixel tests | real-world repair | 隐藏测试不回流 | 未单列 | 视觉是否有用可比较，完整恢复链未分解 |
| GUIRepair | SWE-bench M hidden tests + visual patch selection | repair / validation | 渲染用于候选筛选 | 流水线级而非同一 Agent 重规划 | 按组件消融，不评价整条错误传播 |
| SVRepair | held-out tests / Pass@1；内部 validation 另行触发循环 | localization / repair / feedback | test/compile logs 触发迭代 | 最多三轮 | 有模块消融，缺少游戏运行时新观察链 |
| MM-IssueLoc | PR edit-scope proxy；Acc@K、MRR、Recall、Hit | localization | 不适用 | 不适用 | 精确隔离定位，但 gold 不是最小因果根因，也不连接 Editing/Recovery |

## 8. 对十个问题的综合回答

### 1. 游戏开发为什么适合测试 Coding Agent？

游戏工程同时具备传统软件工程的仓库检索、跨文件依赖、测试与调试，又包含场景树、素材引用、shader、动画、摄像机、碰撞和时序交互。许多错误只有运行后才显现，而部分行为可以通过引擎状态测试或固定输入的受控 replay 观察与评价。它能在同一任务中测量长期规划、工具使用、视觉理解与 runtime reasoning；代价是环境更重、渲染更易波动、Harness 差异更明显。

### 2. 当前 Game Coding Benchmark 的输入是什么？

- GameDevBench：现有 Godot 项目 + 文本指令 + 项目素材；视觉 feedback 工具按实验条件开放。
- GameCraft-Bench：文本产品规格 + Godot 环境 + scaffold / 素材池；Agent 自行生成完整项目和 demo traces。
- GameEngineBench：现有 Unreal 项目 + 纯文本行为规范 + 可编辑 C++ 文件范围。
- OpenGame-Bench：自包含文本游戏规格，无 starter repository 或参考图片。

由此，游戏 benchmark 中的“多模态”可能来自资产、Agent 运行反馈或 evaluator 证据，不应自动等同于 task-essential screenshot input。

### 3. Agent 可以操作什么？

能力范围从受限 C++ 编辑到完整工程生成。典型动作包括文件检索/读取/编辑、shell、编译或启动引擎、读取素材、截图/录制和创建 replay。不同工作使用原生 harness 或定制工具，因而模型对比可能混入 action schema、默认提示、视觉支持与终止策略的差异。

### 4. 如何验证最终结果？

现有路线主要有四类：

1. 确定性 tests：GameDevBench 用 Godot engine-state tests；GameEngineBench 用 Unreal PIE automation。
2. 交互 replay + rubric judge：GameCraft-Bench 运行 Agent 提交的键鼠 trace，以视频/帧和隐藏 rubric 评分。
3. Build/runtime gate + 视觉启发式/VLM：OpenGame 先检查可运行性，再结合像素、运动与 VLM 判断。
4. Rendered screenshot similarity：Design2Code 使用 CLIP 和元素级指标并辅以人工评价；VAB-CSS 以 SSIM 衡量视觉修复。

没有单一 Oracle 覆盖所有情况。纯测试可能漏掉肉眼异常，纯视觉相似或 VLM 又可能把表面效果误当成功。

### 5. 当前是否真正要求 Agent 使用视觉信息？

答案取决于“要求”的定义。Design2Code、VAB-CSS、SWE-bench M 的部分任务和多模态 APR 工作把图像作为核心输入；SWE-bench M 的人工标注把 465/557 个带 issue 图片实例判为图片必要，但有图/无图 Agent 对照只覆盖 development split，也没有逐实例证明去图后 Patch 严格不可识别。GameDevBench 中 82.4% 的任务含额外多模态资产，并按实验条件提供视觉反馈工具，但没有逐任务必要性对照。GameCraft-Bench 的部分受测 Agent，尤其 Kimi-K2.6 和 Opus-4.7，频繁使用运行截图；GPT-5.5 的使用明显更少，而初始要求仍是文本。GameEngineBench 与 OpenGame-Bench 的任务输入则不依赖视觉。

因此，以“图像必要性标注”或“有图/无图效果差异”为主题的多模态 SE 研究并不新；本文 §1.3 所定义的严格 task-essential / Patch 不可辨识性尚不能由这些结果直接推出，仍是待检验假设。“游戏引擎现有仓库中由 runtime 视觉症状决定修复”可作为更窄的候选组合，但仅有领域迁移本身不足以构成强创新。

### 6. Screenshot / runtime video 起什么作用？

至少有四种不同角色：

1. **问题证据**：SWE-bench M 的 issue screenshot/video；
2. **目标规格**：Design2Code、VAB-CSS 的 target screenshot；
3. **Agent 开发反馈**：GameDevBench 的 editor screenshot/runtime video、GameCraft-Bench 的 runtime screenshot；
4. **Evaluator 证据**：GameCraft-Bench replay frames、OpenGame 的最终截图、视觉测试或 VLM judge。

研究设计必须明确视觉位于哪一环，不能把“evaluator 看图”写成“Agent 用图恢复”。

### 7. 当前更关注 generation、repair 还是 debugging？

- Generation：GameCraft-Bench、OpenGame、Design2Code；
- Existing-project localized implementation / completion：GameDevBench、GameEngineBench；
- Real-world multimodal repair：SWE-bench M、GUIRepair、SVRepair；
- 受控 visual editing：VAB-CSS；
- 单独 localization：MM-IssueLoc。

游戏工作已覆盖 generation 与局部实现，也观察到调试行为；但“已注入视觉 Bug 的现有游戏工程”尚不是这些核心工作统一隔离的任务形态。

### 8. 是否评价 Agent 的失败恢复过程？

多数 benchmark 允许 episode 内重试，却只按最终结果评分。GameDevBench 和 GameCraft-Bench 不把隐藏 evaluator 反馈返回 Agent；OpenGame 有 build/test 自修复和轮次消融；VAB-CSS 有多轮截图与 revert；SVRepair 会依据 validation failure 迭代裁剪原始视觉 artifact；FailureMem 利用离线蒸馏的历史失败经验；CUADebug 则用结构化根因诊断指导 re-rollout。恢复机制本身已经存在，较窄的待测边界是游戏仓库 Patch 执行后，Agent 是否因新 runtime observation 改变定位、计划和编辑，而不是简单统计工具调用次数。

### 9. 是否分析 Visual Perception → Code Localization → Editing 的错误传播？

本次范围内尚未见一个游戏仓库代码修复 benchmark 完整分析这条链。MM-IssueLoc 精确隔离 Localization；GUIRepair 和 SVRepair 连接多个模块；GameCraft-Bench 有视觉调试案例和 tool statistics；GameDevBench 有最终错误分类；CUADebug 已在 computer-use Agent 上标注并评价 root-cause step、错误类型、证据与纠正策略。因此，通用的“阶段级错误传播分析”不能声称为空白；可继续检验的是同一游戏代码修复 episode 中，感知错误如何传到定位、编辑、验证与基于新画面的恢复。

### 10. 一天内可验证哪些小型 Research Gap？

本次保留五项候选，见下一节。它们都是待 Step 2 进一步审查的“部分未覆盖组合”或“测量机会”，不是已经成立的创新结论。P0 应优先使用单任务和可审计轨迹验证，不应为了 novelty 扩充任务数量。

## 9. 候选 Research Gaps（最多五项）

证据强度表示本次一手来源对“现有覆盖边界”的支持程度；P0 可行性只评估一天内做出一个完整任务的可能性。

| # | 候选 Gap | 已有覆盖与剩余边界 | 证据强度 | 一天内 P0 可行性 | 主要风险 |
| --- | --- | --- | --- | --- | --- |
| G1 | 游戏仓库中的 task-essential visual symptom repair | SWE-bench M 已研究图像必要性标注与有/无图差异，GameDevBench 已有游戏仓库与视觉工具；它更适合作为领域背景。待检验边界是初始视觉症状是否满足 §1.3 的严格必要性定义 | 中 | 中高 | 只换领域不足以构成强创新；no-image ablation 与文本泄漏审计只是必要性证据，不能预设严格不可辨识 |
| G2 | Patch 后新 runtime observation 驱动的再次规划与恢复 | VAB-CSS 有新截图，GameCraft 有生成期截图调试，SVRepair 重聚焦原 artifact，FailureMem 使用离线历史失败。较窄边界是新游戏画面触发同一 Agent 重新定位、规划和编辑 | 中高 | 中高 | 若首轮成功则观察不到恢复；若 Bug 太难则两模型都失败；需证明策略变化确由新画面驱动 |
| G3 | 游戏仓库修复的端到端阶段级错误传播 | MM-IssueLoc 隔离定位，GUIRepair/SVRepair 有模块流程，CUADebug 已有通用多模态 trajectory 根因诊断。候选边界是 Perception → Localization → Editing → Verification → Recovery 在游戏代码修复中的跨阶段归因 | 中 | 高 | 不能声称通用首创；人工 trajectory 标注可能主观，需预先定义证据和判定规则 |
| G4 | 时序/交互视觉证据必要性的受控 repair 评测 | GameDevBench 有 runtime video，GameCraft 有 replay，但近邻多以静态截图或 DOM 为主。候选重点是动画、瞬态、camera 或需输入触发的视觉症状是否真正改变修复 | 中 | 中低 | replay、帧时序和渲染确定性成本高，可能超出一天 P0 |
| G5 | 视觉 Oracle 的一致性、渲染方差与可审计性 | 功能测试与视觉 evaluator 的组合已有先例；可测机会是量化 deterministic check、像素/VLM 判断的分歧，并记录渲染波动和判定证据 | 中 | 高 | 阈值易显得任意；单任务只能做测量案例，不能证明通用 judge 可靠性 |

### 9.1 供 Step 2 检验的候选组合边界（非 Research Question 结论）

现有证据不允许 Step 2 使用以下宽泛说法：

- “首次研究视觉证据对代码修复是否必要”；
- “首次构建闭环视觉调试 Agent”；
- “首次评价视觉到代码定位”。

现有证据允许 Step 2 继续比较的组合边界之一是：

> 在现有游戏代码仓库中，分别检验初始 runtime 视觉症状是否满足 §1.3 的严格 task-essential 定义，以及 Agent 是否会利用 Patch 后 fresh runtime observation 重新定位、规划和修复；同时用阶段化 trajectory 解释错误如何从感知传播到定位、编辑和验证。

该表述只是五项候选的交集示例，仍需 Step 2 与更小、更可验证的替代问题比较并结合一天工期收缩；本阶段不作 Research Question 选择。

## 10. 对后续阶段的文献约束

1. 若后续选择 task-essential visual evidence，论证至少需要 no-image sanity check，并检查文本与仓库是否直接泄露修复位置或答案。
2. 若选择 closed-loop recovery，证据至少需要表明 Agent 看到 Patch 后新产生的 runtime observation；仅保存最终截图不能支撑闭环主张。
3. 若选择 process diagnosis，可信结果至少需要实验前定义阶段、证据与歧义处理规则，避免按模型输赢事后改变 taxonomy。
4. Oracle 可靠性的论证至少需要区分确定性功能/回归检查、受控视觉 evidence 与 VLM rationale，并报告它们的不一致，而非先验指定任意总分权重。
5. GameDevBench 和 GameCraft-Bench 已展示视觉工具与完整游戏评测的价值；后续论证至少需要明确区分“借鉴已有设计”和“本项目新增受控变量”。

## 11. 一手来源

### Game Coding Agent

- Chi et al. [GameDevBench: Evaluating Agentic Capabilities Through Game Development](https://arxiv.org/html/2602.11103v2), arXiv v2, 2026；[official repository](https://github.com/waynchi/gamedevbench)。
- Luo et al. [GameCraft-Bench: Can Agents Build Playable Games End-to-End in a Real Game Engine?](https://arxiv.org/html/2606.17861v1), arXiv v1, 2026；[official repository](https://github.com/FreedomIntelligence/gamecraft-bench)。
- La et al. [GameEngineBench: Evaluating Coding Agents on Real C++ Runtime Environments](https://arxiv.org/html/2607.03525v2), arXiv v2, 2026；[official repository](https://github.com/Nitrode-Research/GameEngineBench)。
- Jiang et al. [OpenGame: Open Agentic Coding for Games](https://arxiv.org/html/2604.18394v1), arXiv v1, 2026；[official repository](https://github.com/leigest519/OpenGame)。

### Multimodal Generation、Repair 与 Localization

- Si et al. [Design2Code: Benchmarking Multimodal Code Generation for Automated Front-End Engineering](https://aclanthology.org/2025.naacl-long.199/), NAACL 2025；[official repository](https://github.com/NoviScl/Design2Code)。
- Liu et al. [VisualAgentBench: Towards Large Multimodal Models as Visual Foundation Agents](https://openreview.net/forum?id=2snKOc7TVp), ICLR 2025；[arXiv v1](https://arxiv.org/abs/2408.06327v1) · [official repository](https://github.com/THUDM/VisualAgentBench)。
- Yang et al. [SWE-bench Multimodal: Do AI Systems Generalize to Visual Software Domains?](https://openreview.net/forum?id=riTiq3i21b), ICLR 2025；[arXiv v1](https://arxiv.org/html/2410.03859v1) · [official project](https://www.swebench.com/multimodal.html)。
- Huang et al. [Seeing is Fixing: Cross-Modal Reasoning with Multimodal LLMs for Visual Software Issue Fixing](https://arxiv.org/html/2506.16136v1), arXiv v1, 2025 / ASE 2025；[project page](https://sites.google.com/view/guirepair)。
- Wang et al. [SVRepair: Structured Visual Reasoning for Automated Program Repair](https://arxiv.org/abs/2602.06090v2), arXiv v2, 2026；[official repository](https://github.com/codefuse-ai/CodeFuse-SVR)。
- Zhan et al. [MM-IssueLoc: A Controlled Benchmark for Evaluating Visual Evidence in Multimodal Repository-Level Issue Localization](https://arxiv.org/abs/2607.15205v1), arXiv v1, 2026；[official repository](https://github.com/Jasaxion/MM-IssueLoc-Bench)。
- Zhang et al. [CodeV: Issue Resolving with Visual Data](https://aclanthology.org/2025.findings-acl.384/), Findings of ACL 2025；[official repository](https://github.com/luolin101/CodeV)。
- Ma et al. [FailureMem: A Failure-Aware Multimodal Framework for Autonomous Software Repair](https://arxiv.org/html/2603.17826v1), arXiv v1, 2026；[official repository](https://github.com/Ruize-Ma/FailureMem)。
- Zhang et al. [CUADebug: Diagnosing and Repairing Computer-Use Agent Failures](https://arxiv.org/html/2608.02643v1), arXiv v1, 2026。
