# Step 3：候选任务设计

> 状态：候选设计与 P0 选择已预注册。本阶段只比较任务，不实现 Godot 项目、Oracle、Harness 或模型实验。

## 1. 冻结约束

三个候选均服务于 Step 2 已冻结的研究结构：

- **Main RQ：Closed-loop Visual Debugging。**Agent 应在 Patch 后运行项目、接收 fresh runtime observation 并验证；只有首次修复存在可验证失败时才评价 Recovery。
- **Secondary RQ：Process-level Diagnosis。**trajectory 应能区分 Visual Perception、Code Localization、Editing、Runtime Verification 与 Recovery。
- **Validity gate：Task-essential Visual Evidence。**任务文本和静态代码不能直接泄露唯一 Patch；初始画面必须在至少两个合理解释之间提供区分证据。

候选均是自行构造的小型 Godot 4 repository-level repair，不直接复制 OpenBenchmark、GameDevBench 或 GameCraft-Bench 的实例。P0 只选择一个任务，不因后续模型表现更换题目或调整难度。

## 2. 评分方法与预注册选择规则

五个维度均按 1–5 分评价，5 分表示更适合作为一天内 P0。`Implementation Cost` 使用反向计分：**5 表示成本最低，1 表示成本最高**。

| 维度 | 5 分含义 | 1 分含义 |
| --- | --- | --- |
| Multimodal Necessity | 去除视觉输入后，文本和静态工作区不能唯一确定诊断或 Patch | 图片只是装饰，文本或代码已给出答案 |
| Agentic Depth | 自然覆盖观察、检索、定位、编辑、运行、fresh observation 与可能的恢复 | 接近单文件或单属性盲改，无需运行验证 |
| Evaluation Reliability | 可由稳定的确定性行为/状态 Oracle 主判，视觉 artifact 可复核 | 主要依赖主观人工观感、VLM 或易波动像素阈值 |
| Model Discriminability | 存在多种合理但可由测试区分的路径，失败可映射到明确能力阶段 | 正确修改明显，或失败主要来自环境噪声 |
| Implementation Cost | 简单素材、固定状态、少量代码即可在一天内完成全链路 | 需要复杂资产、时序 replay、平台适配或大量标注 |

P0 候选必须同时满足以下硬门槛：

1. `Multimodal Necessity >= 4`；
2. `Evaluation Reliability >= 4`；
3. `Implementation Cost >= 4`；
4. 能在 Patch 后向 Agent 返回新的 runtime screenshot；
5. 功能、视觉和回归结果均可由预声明 Oracle 验证；
6. 不依赖复杂时序 replay 或自由 VLM judge 才能判定成功。

通过硬门槛后，按五维等权总分选择；同分时依次比较 Evaluation Reliability、Implementation Cost、对 Main RQ 的覆盖完整度。该规则和下列分数在任何模型运行前冻结。

## 3. Candidate A：Signal Courier — Twin Tracker Calibration

### 1. 游戏场景

一个小型 top-down 2D `Signal Courier` 场景。玩家位于 viewport 内，`Objective Beacon` 与 `Threat Drone` 可位于屏幕外；HUD 分别显示 Objective tracker 和 Threat tracker，帮助玩家判断两个目标的方向。

### 2. 初始 Repository

一个可直接运行的多文件 Godot 4 项目，拟包含主场景、玩家与两个目标、共享 tracker 方向脚本、两份 tracker profile/resource，以及两张项目自制 PNG：Objective tracker icon 与 Threat tracker icon。两张 PNG 的原生 forward direction 相反，不使用外部版权素材。

### 3. Bug 是什么

两个 tracker 共用的目标方向算法是正确的，Threat profile 为补偿其 PNG 原生朝向而正确使用 `PI` rotation offset。Objective PNG 的原生朝向与 Threat PNG 相反，本应使用不同 offset，但 Objective profile 错误复用了 Threat 的 `PI` offset。因此 Threat tracker 始终指向 Threat Drone，而 Objective tracker 稳定地反向 180°、背离 Objective Beacon。

该 Bug 是 **per-profile visual calibration error**，不是跟错 twin、跟错 target、目标绑定错误，也不是共享 `atan2` / 方向算法错误。

### 4. 给 Agent 什么视觉输入

提供未修复版本在固定 viewport、固定玩家与目标位置下生成的 runtime screenshot。画面同时展示：Threat tracker 与 Threat Drone 的方向关系正确，而 Objective tracker 与 Objective Beacon 的方向关系相反。Agent 还可检查两张 PNG，并在每次 Patch 后重新运行、获取 fresh screenshot。

### 5. 为什么视觉输入是必要的

任务文本只描述“画面中的一个 tracker 方向错误”，不命名 Objective、Threat、profile、文件、属性、正确数值或 Patch。仅看共享算法和两个相同的 `PI` 配置，至少存在“共享算法错误”“Threat calibration 错误”“Objective calibration 错误”等合理解释；代码数值本身也不能说明两张 PNG 各自把哪一侧画成箭头前方。

初始 screenshot 提供两条不可由文本数值替代的区分证据：Threat 的最终方向已经正确，而 Objective 恰好反向；PNG 像素则显示两张图的原生 forward direction 相反。二者共同把问题定位到 Objective 的 profile calibration。若命名、注释或可见测试能够在不看图时直接泄露这一结论，候选 A 即未通过 validity gate。

### 6. Agent 需要操作哪些文件

Agent 需要检查共享 tracker 方向脚本、Objective/Threat profile resource、引用这些 profile 的 HUD/scene，以及两张 PNG 的原生朝向。参考修复只需修改 Objective profile 的 rotation offset；共享算法、Threat profile、目标绑定和 PNG 均不应修改。

### 7. 是否需要运行游戏

需要。Agent 应先用初始 screenshot 建立假设，再运行当前项目确认症状；Patch 后必须在同一固定状态下生成 fresh screenshot，并至少验证 Objective 与 Threat 两个 tracker，不能只看被修改的一侧。

### 8. 是否可能发生失败恢复

可能，但不强制制造失败。合理的首次错误 Patch 包括：给共享算法整体增加 `PI`、修改 Threat profile、旋转场景节点或直接改 PNG。它们可能让 Objective 暂时正确，却会把原本正确的 Threat tracker 翻转或破坏其他方位。fresh screenshot 与可见回归结果可促使 Agent 撤销全局修改，转向 Objective-specific calibration。若首个 Patch 已通过所有 Gate，则 Recovery 记为 `N/A (not triggered)`。

### 9. Ground Truth

行为 Ground Truth 是：在固定的多个目标方位下，两种 tracker 的**最终可见 forward vector**都指向各自目标，同时屏幕边缘 clamp、目标绑定和无关游戏状态保持不变。参考 Patch 将 Objective profile 错误复用的 `PI` offset 改为适配 Objective PNG 原生朝向的 `0.0`，保持共享方向算法与 Threat profile 不变；最终评价不要求 byte-for-byte 复制参考 diff。

### 10. 自动评价方式

- **Bug-state check：**在多个预声明方位中，Objective 的可见 forward vector 与 Objective 方向的 dot product 约为 `-1`，Threat 对应 dot product 约为 `+1`。
- **Visual correctness：**根据两张 PNG 已知的原生 forward vector、最终 sprite transform 与目标方向，检查两种 tracker 的 dot product 均达到预声明正阈值；固定截图作为复核 artifact，而非由自由 VLM 主判。
- **Functional correctness：**检查 tracker 仍跟随各自原目标并随目标位置更新，项目可以正常启动和运行。
- **Regression safety：**覆盖至少四个目标象限，检查 Threat tracker、edge clamp、玩家与目标行为没有被 Objective 修复破坏。
- **Shortcut checks：**拒绝隐藏 tracker、交换目标或纹理、移动目标迁就箭头、写死单一方位，以及只把共享算法整体翻转的 Patch。

### 11. 模型区分度

任务可区分：是否从画面识别“一个正确、一个反向”；是否检查 PNG 的原生朝向；是否把共享算法与 per-profile calibration 分开；是否只验证 Objective 而漏掉 Threat 回归；以及首次全局修复失败后能否利用 fresh observation 收缩到 profile 层。它不靠复杂代码量制造难度，差异更容易映射到预注册过程阶段。

### 12. 一天内实现风险

风险低至中。两张 PNG 可用简单几何图形自制，运行状态和目标方位可完全固定，主要视觉判定可转化为确定性向量关系。主要风险是 PNG 的 forward direction 不够清楚、截图没有同时证明 Threat 正确与 Objective 反向、或者 repository 命名泄露唯一修复；这些都必须在正式实验前淘汰或修正。

## 4. Candidate B：HUD Safe-Area / Layout Repair

### 1. 游戏场景

一个小型 2D 游戏的移动端 HUD。在目标 viewport 中，右上角 Objective panel 越过 safe area、被裁切或与状态控件重叠；默认桌面分辨率下表面上正常。

### 2. 初始 Repository

一个可运行的 Godot 4 UI 项目，拟包含游戏主场景、HUD scene、嵌套的 `Control` / `Container`、Theme resource、viewport preset 和现有布局脚本。

### 3. Bug 是什么

Objective panel 混用了 full-viewport anchor 与固定 pixel offset，没有相对于 safe-area container 布局，导致特定纵横比或模拟 display cutout 下位置错误。

### 4. 给 Agent 什么视觉输入

提供目标 viewport 的当前 runtime screenshot，其中可见被裁切/重叠的 panel、其他正常 HUD 元素以及 safe-area 的可感知边界；Patch 后允许在多个固定 viewport 下重新截图。

### 5. 为什么视觉输入是必要的

图片用于指出究竟哪个控件、哪一条对齐关系和哪种可见异常需要修复；任务文本不直接给出节点名、anchor、margin 或像素值。但 safe-area 需求较容易被转写为精确文本，静态 scene 也可能暴露异常 offset，因此视觉证据的不可替代性弱于 Candidate A。

### 6. Agent 需要操作哪些文件

Agent 需检查 HUD scene、相关 container/anchor、Theme 与可能的 viewport 适配脚本；合理 Patch 应局限于布局约束，不修改游戏规则或用移动其他控件掩盖问题。

### 7. 是否需要运行游戏

需要。至少在默认 viewport 和一个受影响 viewport 下运行并截图，防止只修复单一分辨率。

### 8. 是否可能发生失败恢复

可能。首次使用固定像素 offset 可能修好给定截图，却在第二个 viewport 中重新溢出；fresh screenshot 或几何测试能够促使 Agent 改用 container/anchor 约束。首轮完整通过时 Recovery 仍记 `N/A`。

### 9. Ground Truth

目标 panel 在所有受测 viewport 中保持在 safe area 内，与邻近 HUD 控件不重叠，并维持预声明边距、内容可见性和层级；不要求唯一 scene diff。

### 10. 自动评价方式

用 Godot `Control` 的全局 `Rect2` 检查 containment、最小边距、控件间 overlap 和内容尺寸；在多个 viewport 重复执行。固定 screenshot 用于视觉复核，字体像素差异不作为唯一 mandatory Oracle，并用启动、输入和无关 HUD 状态检查回归。

### 11. 模型区分度

可以区分是否理解 scene tree、是否使用响应式布局、是否主动做多分辨率验证，以及是否用硬编码掩盖问题。但常见 anchor/offset 修复可能很快退化为单个 scene 属性修改，对强弱模型的区分预计低于 A。

### 12. 一天内实现风险

风险中等。几何 Oracle 较容易实现，但 headless 字体、Theme 最小尺寸、DPI 和 viewport rounding 可能造成波动；多个视觉上合理的布局也可能使边距 Ground Truth 显得任意。

## 5. Candidate C：Animation / Trail Phase Repair

### 1. 游戏场景

一个 2D 横版角色执行 dash 并产生 afterimage/trail；在启动、结束或转向附近，trail 提前一帧、落后一帧，或短暂出现在角色运动方向前方。

### 2. 初始 Repository

一个可运行的 Godot 4 动画项目，拟包含 Player 状态机、AnimationPlayer、trail pool/生成脚本、动画资源以及固定输入 replay 配置。

### 3. Bug 是什么

Trail 在错误的更新阶段采样 Player transform、facing 或 animation frame，使视觉残影与当前运动相位不一致；项目不报编译或运行错误。

### 4. 给 Agent 什么视觉输入

提供 dash 或转向前后的短帧序列/contact sheet，标明统一帧序但不文字描述具体错误帧；Agent 修复后可运行相同输入并重新采集序列。

### 5. 为什么视觉输入是必要的

单看静态代码时，多种 `_process` / `_physics_process` 更新顺序都可能成立。只有比较连续帧中的 Player 方向、位置与 trail 相位，才能判断异常是提前、滞后还是方向采样错误；单张截图也不足以完整表达该证据。

### 6. Agent 需要操作哪些文件

Agent 需检查 Player 状态机、trail 生成脚本、动画资源与更新顺序，可能需要协调多个文件，而不是只修改一项资源参数。

### 7. 是否需要运行游戏

必须运行固定输入 replay，并在 Patch 后重新采集相同帧区间。只通过静态检查或单次最终截图无法验证时序修复。

### 8. 是否可能发生失败恢复

很可能。整体平移 trail、增加固定延迟、删除首帧或直接禁用 trail 可能改善一个片段，却在反向 dash、不同帧率或下一轮动作中失败，适合观察多轮验证和恢复。

### 9. Ground Truth

Trail 在 dash 有效期内使用预声明更新阶段的 Player transform/facing；残影位于运动方向后方，并在转向和 dash 结束时按正确相位更新或清理，同时保持移动、碰撞和动画状态不变。

### 10. 自动评价方式

以固定 tick 输入 replay 记录 Player 速度、facing、trail transform、生成 tick 与生命周期，检查 trail 相对运动方向的有符号偏移和采样顺序；在至少两种更新频率下重复，并将帧序列作为辅助证据。该方案需要先解决 replay 与捕获确定性，不能主要依赖视频 VLM judge。

### 11. 模型区分度

理论区分度高，可同时考察时序视觉理解、跨文件定位、状态机推理、重复运行和恢复。但失败也容易由 frame scheduling 或 capture noise 引起，从而把基础设施差异误判为模型能力差异。

### 12. 一天内实现风险

风险高。固定 replay、多帧捕获、渲染与 physics tick 对齐、跨帧率复现和时序 Oracle 都会占用大量时间，可能挤压 Harness、模型实验与报告，不适合作为本次 P0。

## 6. 五维评分

| Candidate | Multimodal Necessity | Agentic Depth | Evaluation Reliability | Model Discriminability | Implementation Cost | 总分 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **A：Twin Tracker Calibration** | **5** | **4** | **5** | **4** | **5** | **23 / 25** |
| B：HUD Safe-Area / Layout | 4 | 3 | 4 | 3 | 4 | 18 / 25 |
| C：Animation / Trail Phase | 5 | 5 | 2 | 5 | 1 | 18 / 25 |

评分理由摘要：

- **A** 的视觉证据能区分共享算法与 profile calibration，结果可用多方位 forward-vector invariant 稳定评分，且不需要复杂素材或 replay；没有维度低于 4。
- **B** 的几何 Oracle 较稳定、成本可控，但视觉需求更容易被文字替代，任务也可能退化为常规 anchor 属性修复。
- **C** 的视觉与 Agentic depth 最强，但时序确定性和实现成本未通过 P0 硬门槛；高理论区分度不能抵消 evaluator confound。

## 7. P0 推荐与淘汰条件

按预注册规则，A 与 B 通过三个数值硬门槛，C 因 `Evaluation Reliability = 2`、`Implementation Cost = 1` 被淘汰。A 以 `23 / 25` 高于 B 的 `18 / 25`，并能以一个小型、可确定性评分的 profile calibration Bug 覆盖 initial observation、localization、editing、fresh visual verification 与可能的 recovery，因此固定推荐：

> **Task 001：Candidate A — Signal Courier — Twin Tracker Calibration**

这一选择不以“最复杂”或“保证拉开模型差距”为依据，而以一天内完成可运行、可评分、可复核的完整闭环为依据。B 仅保留为设计比较对象，C 延后为具备稳定 replay 基础设施后的 P1；不得在看到模型结果后切换到 B/C。

Candidate A 在 Step 4/5 必须继续通过以下淘汰条件：

1. **视觉必要性：**去除 screenshot 与 PNG 像素观察后，任务文本、命名、注释和可见测试不能唯一指出 Objective profile 或 `0.0`；否则淘汰。
2. **症状可辨识：**初始画面必须同时证明 Threat tracker 正确、Objective tracker 反向；若只能看出“某个箭头不自然”而不能区分合理解释，则淘汰。
3. **资产朝向可审计：**两张自制 PNG 的原生 forward direction 必须清楚、固定且确实相反；若人工审查存在方向歧义，则淘汰。
4. **确定性：**Bug State 至少连续三次稳定复现，Oracle State 至少连续三次通过多方位检查；若结果受随机或渲染波动影响，则淘汰。
5. **Oracle 完整性：**评价器必须能拒绝全局翻转共享算法、修改 Threat profile、交换/重画 PNG、隐藏 tracker、移动目标和写死单一方位等 shortcut；否则淘汰。
6. **fresh observation：**Agent 必须能在 Patch 后获得新 runtime screenshot；若画面只供最终 evaluator 使用，则不满足 Main RQ。
7. **环境与工期：**Godot 4、运行、截图或 evaluator 链路若预检失败，记录阻塞并停止，不自动换引擎或晋级 B/C。

若 A 触发任一条件，应在模型实验前记录失败并回到任务设计审查；不得为了保留既定推荐而放宽阈值，也不得用模型运行结果反向修改评分或淘汰条件。
