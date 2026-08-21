# GameVisualFix v2：Seed + Local Codex 受限结果（历史版本）

> Suite：`gamevisualfix_v2_seed_local_3x2`。这是用户批准跳过 Qwen 后的受限执行结果，不是原 3×3 模型矩阵，也不是模型排名。

## 有效 canonical 评分

| Provider / model | Easy T001 | Medium T002 | Hard T003 | Task Success Rate | F / V / R 平均 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Local Codex / `gpt-5.6-sol` | 100 ✓ | 100 ✓ | 100 ✓ | 3/3 | 45 / 35 / 20 |
| Seed Evolving / `doubao-seed-evolving` | N/A | N/A | N/A | N/A | N/A |

`task_success` 只有 Functional、Visual、Regression 三个 mandatory category 都通过时才为真；不能由总分补偿。

## Provider availability 与无效 lineage

| Run | 状态 | 处理 |
| --- | --- | --- |
| Seed T001 run1 | `invalid_infrastructure` | 全任务流没有可用 thread ID / controller action；不计分。 |
| Seed T001 run2 | `invalid_infrastructure` | 多图参数修复后仍是同一流式 transport failure；达到两次上限，停止 Seed 后续 Task。 |
| Local T002 run1 | `invalid_infrastructure` | manifest adapter 路径使 smoke 与 fresh observation 找不到脚本；隐藏 100 分不计入。 |
| Local T002 run2 | `valid_canonical` | 修正 workspace-relative adapter 后的唯一有效 rerun，计分。 |

完整机器可读数据（含文件哈希、时间、actions、invalid reason）保留在历史提交的 [`v2_seed_local_scores.json`](v2_seed_local_scores.json)；本工作树中的旧运行目录和轨迹已按发布规则移除。最终正式指标请参阅 [`v2_1_seed_proxy_scores.json`](v2_1_seed_proxy_scores.json) 与 [`final_project_report.md`](../report/final_project_report.md)。

## 解释边界

- Local Codex 三题满分是本 task set 对该模型的 **ceiling effect**，不是难度或能力排序结论。
- Seed 的 N/A 是 Codex CLI 与外部 Provider 的 Responses 流式兼容性/availability 结果，不是 Seed 模型失败。
- 每个有效 task 只有一个 attempt；没有置信区间、显著性检验或跨模型胜负结论。
