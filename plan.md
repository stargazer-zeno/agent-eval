## 项目总目标

我正在完成一家模型评测公司的面试题。

HR 原始题目位于：

`D:\pxc\EarnM\zijie\题目.md`

请始终以该文件中的正式要求为最高优先级。

我决定重点研究：

**游戏开发场景下的 Multimodal Coding Agent Evaluation**

暂定项目名称：

**GameVisualFix**

核心关注：

> 当游戏开发 Bug 的关键信息来自截图、运行画面或视觉状态时，Coding Agent 能否利用视觉证据完成“观察 → 定位 → 修改 → 运行 → 再观察 → 失败恢复”的完整开发闭环。

整个项目只有一天完成，因此执行原则为：

**先完成一个小而完整的 Benchmark，再追求任务复杂度和创新性。**

禁止一开始设计大量任务。

P0 目标始终是：

**1 个完整任务 + Seed + 1 个外部模型 + 自动评分 + trajectory 分析 + 完整报告。**

整个项目使用 Git 管理。

---

# Step 0：项目初始化

首先读取：

`D:\pxc\EarnM\zijie\题目.md`

当前阶段只完成项目初始化，不进行具体 Benchmark 设计。

请：

1. 提炼 HR 的正式要求；
2. 初始化 Git repository；
3. 建立：

   * research/
   * design/
   * benchmark/
   * harness/
   * experiments/
   * trajectories/
   * results/
   * report/
4. 创建 README.md；
5. 创建 progress.md。

progress.md 固定记录：

* 当前阶段
* 已完成内容
* 关键结论
* 当前风险
* 下一阶段输入

完成后 Git commit。

**到此停止，不进入文献调研。**

---

# Step 1：游戏多模态 Coding Agent 文献调研

读取：

* 题目.md
* README.md
* progress.md

当前只做调研，不设计具体 Benchmark Task。

优先检索 2024–2026 年最新论文和官方代码。

必须重点研究：

### Game Coding Agent

* GameDevBench
* GameCraft-Bench
* GameEngineBench
* OpenGame / OpenGame-Bench

### Multimodal Code Generation

* Design2Code
* 与 screenshot-to-code、visual code editing 相关工作

### Visual Agent

检索：

* visually grounded agent
* visual feedback agent
* GUI agent
* interactive visual planning
* multimodal debugging

至少回答：

1. 游戏开发为什么适合测试 Coding Agent？
2. 当前 Game Coding Benchmark 的输入是什么？
3. Agent 可以操作什么？
4. 如何验证最终结果？
5. 当前是否真正要求 Agent 使用视觉信息？
6. Screenshot / runtime video 在当前工作中起什么作用？
7. 当前 Benchmark 更关注 generation、repair 还是 debugging？
8. 是否评价 Agent 的失败恢复过程？
9. 是否分析 Visual Perception → Code Localization → Editing 的错误传播？
10. 还有哪些可以一天内验证的小型 research gap？

特别重点分析：

**GameDevBench 与 GameCraft-Bench。**

不要大量罗列论文。

形成：

**Existing Work → What It Measures → Limitation → Opportunity**

输出：

`research/literature_review.md`

最后只保留最多 5 个值得探索的 Gap。

更新 progress.md。

Git commit。

**完成后停止。**

---

# Step 2：Research Gap 与研究问题

读取：

* research/literature_review.md
* progress.md
* HR 原始要求

现在基于文献，而不是凭空提出研究方向。

重点评估以下假设：

### Hypothesis A：Task-essential Visual Evidence

现有游戏 Coding Agent Benchmark 中，视觉反馈经常是辅助 Agent 验证结果。

我们能否进一步设计：

**视觉信息本身就是确定 Bug 的必要证据？**

### Hypothesis B：Closed-loop Visual Debugging

是否可以测试：

**Screenshot → Patch → Runtime Screenshot → Re-plan → Repair**

而不仅仅测试一次代码生成？

### Hypothesis C：Process-level Diagnosis

除了最终 Pass/Fail，是否可以分析：

* Visual Perception
* Code Localization
* Editing
* Verification
* Failure Recovery

请判断这些假设：

* 是否有已有工作；
* 是否真的构成 gap；
* 是否适合本次面试；
* 是否一天内可验证。

最终确定：

1 个主要 Research Question

* 最多 2 个 Secondary Research Questions。

输出：

`research/gap_analysis.md`

不要设计代码。

更新 progress.md。

Git commit。

**完成后停止。**

---

# Step 3：候选任务设计

读取：

* literature_review.md
* gap_analysis.md
* progress.md

根据前面的 Research Question，设计 **3 个候选游戏 Coding Agent Task**。

优先考虑：

### Candidate A

2D Character Visual-State Debugging

### Candidate B

Game UI Visual Layout Debugging

### Candidate C

Animation / Temporal Visual Debugging

每个任务分析：

1. 游戏场景；
2. 初始 Repository；
3. Bug 是什么；
4. 给 Agent 什么视觉输入；
5. 为什么视觉输入是必要的；
6. Agent 需要操作哪些文件；
7. 是否需要运行游戏；
8. 是否可能发生失败恢复；
9. Ground Truth；
10. 自动评价方式；
11. 模型区分度；
12. 一天内实现风险。

按照：

**Multimodal Necessity
× Agentic Depth
× Evaluation Reliability
× Model Discriminability
× Implementation Cost**

评分。

推荐一个 P0 Task。

注意：

不要为了创新而增加复杂度。

优先保证：

**这个任务真的可以跑完。**

输出：

`design/task_candidates.md`

更新 progress.md。

Git commit。

**不要实现任务，完成后停止。**

---

# Step 4：Benchmark Specification

读取：

* gap_analysis.md
* task_candidates.md

现在只定义 P0 Task。

不要写 Agent Harness。

Benchmark Spec 必须明确：

## Input

* Repository
* Natural-language request
* Screenshot / image / frame sequence

## Environment

优先评估 Godot 4 是否合适。

## Agent Tools

例如：

* file search
* file read
* file edit
* terminal
* run game
* screenshot

## Expected Workflow

Visual Observation
→ Bug Hypothesis
→ Repository Exploration
→ Code Localization
→ Patch
→ Run
→ Visual Verification
→ Recovery

## Ground Truth

明确正确修改应该满足什么行为。

## Success Criteria

至少区分：

### Functional Correctness

原有游戏逻辑不能被破坏。

### Visual Correctness

视觉 Bug 是否真正被修复。

### Regression Safety

无关功能是否仍正常。

---

## Multimodal Necessity Check

必须回答：

> 如果完全不给 Agent 图片，这道题是否仍然可以根据文字直接确定正确 Patch？

如果答案是“是”，修改任务设计。

视觉信息必须提供不可由文本完全替代的 Task Evidence。

---

## Contamination Check

任务不能直接复制：

* OpenBenchmark
* GameDevBench
* GameCraft-Bench

可以借鉴它们的：

* task construction methodology
* harness
* evaluation principles

但 Task 本身必须自行设计或从真实开发需求重新构造。

输出：

`design/benchmark_spec.md`

更新 progress.md。

Git commit。

**完成后停止。**

---

# Step 5：Minimal Viable Benchmark 实现

读取：

`design/benchmark_spec.md`

现在才开始实现代码。

当前只实现：

**Task 001**

不增加第二个 Task。

建议优先使用小型 2D Godot 项目。

必须生成：

* runnable initial project
* injected bug
* visual evidence
* user task
* ground truth patch
* visible tests
* hidden tests
* evaluator

首先人工验证完整链路：

### Bug State

Initial Project
→ Run
→ Bug 可稳定复现

### Oracle State

Apply Ground Truth
→ Run
→ Bug 消失
→ Functional Tests Pass
→ Regression Tests Pass

只有 Oracle 全部通过后 Benchmark Task 才视为有效。

记录：

`benchmark/task_001/validation.md`

Git commit。

更新 progress.md。

**Benchmark 未验证通过时，不进入模型实验。**

---

# Step 6：Agent Harness 与实验协议

读取：

* benchmark_spec.md
* validation.md

现在配置 Coding Agent。

目标：

**尽可能只改变底层模型，不改变 Agent Harness。**

首先确认：

1. Seed 模型的调用方式；
2. Seed 是否原生支持图像输入；
3. 外部模型的调用方式；
4. 是否存在同时支持两者的统一 Harness。

如果存在统一 Harness，优先使用统一 Harness。

如果无法做到，则必须记录 Harness Difference，并在最终报告中作为实验限制。

统一控制：

* Repository
* Prompt
* Screenshot
* Tools
* Maximum Steps
* Runtime
* Testing Rules

记录 trajectory：

* inspected files
* tool calls
* commands
* modifications
* test runs
* screenshots
* errors
* recovery actions
* final state

先用一个模型跑通整个 Harness。

确认可运行后停止。

更新 progress.md。

Git commit。

---

# Step 7：正式模型实验

正式测试：

### Required

Seed Model
vs
External Model

使用相同 Task。

主要评价：

## Outcome

* Task Success
* Functional Correctness
* Visual Correctness
* Regression Safety

## Process

分析：

* Visual Perception
* Code Localization
* Patch Correctness
* Verification
* Failure Recovery
* Efficiency

不要根据模型自述判断成功。

最终成功必须依据：

* evaluator
* test results
* runtime evidence

如果资源允许，再增加：

### Optional Ablation

Visual Input
vs
No Visual Input

用于分析：

> 视觉输入是否真正帮助 Agent 完成任务？

实验结果保存到：

`experiments/`

trajectory 保存到：

`trajectories/`

评分保存到：

`results/scores.json`

完成后更新 progress.md。

Git commit。

---

# Step 8：结果与 Case Study

读取：

* experiments/
* trajectories/
* scores.json

禁止先写结论再找证据。

所有分析必须从真实 trajectory 出发。

分别分析两个模型：

## Visual Perception

是否正确识别截图中的异常？

## Localization

是否找到真正相关的代码 / Scene / Asset？

## Editing

修改是否针对 root cause？

## Verification

是否主动运行游戏或测试？

## Recovery

第一次修复失败后，是否根据新 observation 改变策略？

形成：

**Observation
→ Action
→ Result
→ Failure / Success Cause
→ Capability Interpretation**

特别选择：

* 一个成功案例；
* 一个失败或低效案例。

输出：

* `results/comparison.md`
* `results/case_study.md`

最后总结：

> 强模型究竟强在哪里？

不要只比较总分。

更新 progress.md。

Git commit。

---

# Step 9：最终面试报告

最后才开始写：

`report/final_report.md`

结构：

1. Interview Task & Background
2. Related Work
3. Motivation
4. Research Question
5. Benchmark Design
6. Task Example
7. Agent Setup
8. Evaluation Protocol
9. Model Results
10. Trajectory Case Study
11. Strong vs Weak Model Analysis
12. My Design Insights
13. Limitations
14. Future Directions
15. Conclusion

报告必须明确区分：

### What Comes From Prior Work

例如 GameDevBench / GameCraft-Bench 的启发。

### What I Designed

例如：

* task-essential visual evidence
* visual debugging task
* process-level capability decomposition
* visual/no-visual ablation

### What Experiments Actually Show

不能把猜测写成实验结论。

最后确保面试官能够快速回答三个问题：

1. **你为什么设计这道题？**
2. **这道题到底测出了什么？**
3. **Seed 和外部模型为什么产生差异？**

完成 README 和最终 Git commit。
