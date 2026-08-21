# Qwen Task 001 Trajectory Case Study

本分析只引用 action、文件读写、公开工具结果、Controller screenshot receipt 与隐藏 evaluator；不使用不可见 chain-of-thought，也不把模型自述当作成功证据。

| 阶段 | 判定 | 可观察证据 |
| --- | --- | --- |
| Perception | 部分成功 | 最终两次成功 fresh observation 后，模型正确指出 Objective Tracker 与东侧目标相反，并检查了 Threat 的空间关系。 |
| Localization | 部分成功 | Steps 2–6 读取共享 tracker、profile schema、scene 及两个 profile；定位范围正确，但把两个 profile 同为 `PI` 错判为共享问题。 |
| Editing | 失败 | 最终修改共享 `tracker_arrow.gd`，反转 Y 并移除所有 profile offset；没有针对 Objective profile 根因做最小修复。 |
| Verification | 成功但不充分 | 三次 `observe` 消耗中第一次 capture timeout，后两次成功并真实注入新 PNG；模型根据第一张成功新图继续修改，最后也执行 smoke。 |
| Recovery | 成立 | 初次 patch 导致 parse failure；模型根据 smoke 错误修复语法。其后根据 fresh screenshot 改变 patch，满足条件性恢复定义。 |
| Outcome | 失败 | hidden evaluator：18/45 + 14/35 + 10/20 = 42/100，`task_success=false`。 |

关键错误传播链为：`Perception（局部正确） → Localization（范围正确、根因错误） → Editing（共享算法过修） → Verification（单画面看似改善） → Recovery（发生但仍过拟合）`。这说明仅记录最终 patch 会漏掉重要现象：模型确实利用了新视觉证据，也具备失败后恢复行为，但恢复方向没有回到正确的对象级配置根因。

Codex 补充轨迹只能支持一个额外的 perception 观察：它正确描述 Objective 的 180°反向和 Threat 正常，但 Windows sandbox 拒绝全部 workspace 操作，因而 Localization 以后均记为 `N/A (infrastructure invalid)`，不能与 Qwen 评分比较。
