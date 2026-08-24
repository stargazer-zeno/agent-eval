# GameVisualFix

GameVisualFix 是一个面向游戏工程多模态 Coding Agent 的小型 Benchmark / Evaluation 项目，关注 Agent 能否把 task-essential runtime visual evidence 转化为代码定位、编辑、验证、状态维护与失败恢复。

## 当前交付状态

### v3：Seed 能力边界三任务原型

Suite：`gamevisualfix_v3_seed_boundary_3x1`。三个任务均使用 Godot 4.7.1、统一 Codex Controller Harness 和 `doubao-seed-evolving`，每题仅计一个有效 canonical attempt。

| Task | 能力重点 | Hidden cases | F | V | R | Total | Success |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| T004 Glyph Atlas | 跨图细粒度对应与空间变换 | 36 | 5 | 0 | 20 | 25 | false |
| T005 Checkpoint Mosaic | 持久状态、长程执行与延迟依赖 | 12 | 30 | 0 | 20 | 50 | false |
| T006 Mirrorstorm | 动态 phase 与生命周期诊断 | 12 | 45 | 35 | 20 | 100 | true |

主指标为 `Task Success Rate = 1/3`，平均总分 `58.333`。T004 与 T005 暴露了能力边界；T006 被 Seed 一次性完成，说明该原型的公开架构契约仍过于直接。结果只代表三道合成任务、单模型、单次有效 attempt 的 Case Study，不构成统计显著性或通用模型排名。

主要入口：

- [v3 完整原型设计](design/v3_hard_task_prototypes.md)
- [v3 数据集索引](benchmark/dataset_v3.json)
- [机器可读分数](results/v3_seed_boundary_scores.json)
- [trajectory Case Study](results/v3_seed_boundary_case_study.md)
- [v3 完整报告](report/v3_seed_boundary_report.md)

### v2.1：历史三任务 × 双 Provider 基线

v2.1 保留为历史基线，不进入 v3 主矩阵。Seed 在 T001–T003 为 3/3，Local Codex 为 2/3，形成了推动 v3 增难的 ceiling-effect 证据。

- [v2.1 分数](results/v2_1_seed_proxy_scores.json)
- [v2.1 Case Study](results/v2_1_seed_proxy_case_study.md)
- [v2.1 报告](report/v2_1_seed_proxy_report.md)

## HR 要求、建议项与自选方向

- HR 强制目标：形成可运行的软件工程 Agent 评测闭环，包括任务、至少两个模型的正式交付、自动评分、trajectory 分析和最终报告。
- 工程建议：任务应基于真实开发流程，Ground Truth 可复现，模型权限一致，结果可自动比较。
- 项目自选方向：游戏工程中的多模态视觉调试。v3 是额外的 Seed 能力边界探索，不替代原 HR 正式双模型交付。

“视觉闭环更能暴露 Agent 缺陷”不是先验事实。项目通过 Caption/no-image 候选空间 Gate、多个 runtime observation、隐藏 evaluator 和 trajectory 证据进行条件性验证，不声称宽泛首创。

## v3 Harness 契约

Agent 每个 turn 只返回一个严格 JSON Action：

```json
{
  "action": "list_files|read_file|write_file|run_smoke|observe|submit",
  "path": "",
  "content": "",
  "scenario": "",
  "summary": ""
}
```

- `lazy_workspace`：首轮只注入 Prompt 和声明图片，源码必须通过文件工具读取。
- `controller_persistent`：Task 005/006 的 session state 与 hash-chain ledger 位于 Agent workspace 外。
- `observe`：每次从当前 workspace 启动新的 Godot capture，并回传 fresh PNG 与不可伪造状态回执。
- `submit`：冻结最终 workspace 后运行隐藏 evaluator；隐藏结果永不回流模型。
- 每题最多 30 个 Controller actions、8 次 fresh observations、40 分钟。

Canonical 运行入口：

```powershell
python harness/run_codex_eval.py `
  --task-id task_005 `
  --provider seed_evolving `
  --env-file <ignored-env-file> `
  --godot .cache/tools/godot-4.7.1/Godot_v4.7.1-stable_win64.exe `
  --canary-receipt <valid-canary.json> `
  --suite-id gamevisualfix_v3_seed_boundary_3x1 `
  --output <new-run-directory>
```

重新生成脱敏汇总：

```powershell
python harness/summarize_v3_seed_boundary.py
```

## 评价指标

- Functional Correctness：45 分。
- Visual Correctness：35 分。
- Regression Safety：20 分。
- Build/launch 是硬门槛。
- `task_success=true` 仅当所有 mandatory groups 通过，总分不能补偿失败分项。

Outcome 由隐藏 evaluator 判断“是否做对”；trajectory 只解释 Perception、Localization、Editing、Verification、State Tracking/Recovery 为什么成功或失败，不使用模型自述或不可见 chain-of-thought 作为证据。

## 目录

- `research/`：文献与 Research Gap。
- `design/`：任务、协议与冻结设计。
- `benchmark/`：公开工程、私有 Oracle、evaluator 与 validation records。
- `harness/`：Codex Controller、Seed transport、state ledger、汇总脚本与测试。
- `experiments/`：脱敏 attempt receipt、patch、lifecycle 和评分归档。
- `trajectories/`：去 reasoning 的 action/state hash-chain 与 fresh images。
- `results/`：机器可读分数与 Case Study。
- `report/`：综合报告。

## 隔离与凭据保护

Agent 可见 workspace 只能由 task `public/` allowlist 构造，不能包含主仓库历史、`.env`、private tests、Oracle、reference patch 或 evaluator。隐藏评价从独立副本执行。

`.env`、API key、Authorization header、Provider 原始流、run-local Codex session、Agent workspace 和 reasoning 不得提交或写入归档日志。Git 中只保留脱敏 Action/state receipt、patch、截图、评分与结构哈希。任何输出目录提交前都必须执行凭据扫描，并确认 `.env` 未被跟踪。

## 当前最重要的后续工作

优先把 T005 扩展为 `stateful visual software-engineering agents` family：程序化生成 seal codebook、route DAG、跨版本 migration 和延迟引用。先构建 30–50 条 calibration set，并加入人类基线与至少两个强 Agent；不要根据当前 Seed 结果修改已冻结任务或提高像素阈值。

T006 下一版应把具名 Boolean 开关替换成真实事件队列、不可变 sample 与对象池实现，让后续 phase 图像承担候选消歧，而不是让公开注释直接暴露目标架构。
