# GameVisualFix v2 Local Codex 单轨迹 Case Study（历史版本）

本分析只使用受控 Controller action、公开截图 receipt 与隐藏 evaluator 结果；不使用模型自述或不可见 reasoning 作为正确性证据。旧 v2 轨迹目录已按发布规则移除，历史内容仍可从 Git 历史追溯；v2.1 脱敏轨迹见 [`trajectories/v2_1_seed_proxy/`](../trajectories/v2_1_seed_proxy/)。

| Task | 可观察 action 序列 | Perception | Localization | Editing | Verification | Recovery | 自动评分 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 Easy | read tracker → read 两个 profile → write Objective profile → smoke → fresh BASELINE → submit | Ambiguous：初始图被预载，但 action 本身不证明视觉归因 | Supported：先读取 tracker 和两个 profile，随后只改 Objective profile | Supported：最小 profile offset 修改 | Supported：1 次 fresh BASELINE observation | N/A：首个补丁未失败 | 45/35/20，成功 |
| T002 Medium | read `scripts/main.gd` → write → smoke → fresh BASELINE → submit | Ambiguous：无可见动作能独立证明模型从截图识别坐标空间问题 | Supported：读取后在同一文件修改 Objective 方向计算 | Supported：隐藏 18-case 验证行为等价的 camera-space 修复 | Supported：smoke 成功且收到 1 次 fresh BASELINE | N/A | 45/35/20，成功 |
| T003 Hard | read `scripts/main.gd` → write → fresh RIGHT_TO_LEFT contact sheet → submit | Ambiguous：初始 contact sheet 已预载，未产生可独立验证的视觉解释 | Supported：先读 dash/trail 逻辑所在文件 | Supported：一次 phase/facing 根因修改 | Supported：收到 1 次 fresh RIGHT_TO_LEFT contact sheet | N/A | 45/35/20，成功 |

T002 的首次 run 因 Controller manifest 路径错误使 observation/smoke 不可用，归为 `invalid_infrastructure`，不写入上表。三个有效 run 都没有“先错后改”的机会，故 Recovery 统一为 N/A；不能以成功的首次编辑虚构恢复能力。
