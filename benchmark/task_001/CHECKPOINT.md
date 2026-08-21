# Task 001 暂停检查点

> 2026-08-21 更新：本检查点已由 `validation.md` 和 `validation/results.json` 取代。其下内容保留为恢复历史；其中“尚未重跑”的描述不再代表当前状态。Task 001 当前已通过 Bug/Oracle 三次重复验证及七类 shortcut 拒绝验证。

> 日期：2026-08-21
> 状态：Step 5 实现已保存，但最新版本尚未通过最终验收；不得据此启动模型实验。

## 已保存内容

- `public/`：Godot 4.7.1 项目、两张原创箭头 PNG、当前 Bug 截图、公开 smoke/capture、WASD 与 Objective completion。
- `private/`：reference patch、Oracle manifest、隐藏 suite、Python evaluator、私有 asset generator 与依赖声明。
- 初始状态已对齐冻结规格：Objective 位于正东、Threat 位于西北；Objective Tracker 反向，Threat Tracker 正确。
- 会泄露两张 PNG 原生朝向的 asset generator 已从 public 移到 private。
- Hidden runner 已固定 Windows/OpenGL Compatibility、Dummy audio、隐藏窗口与屏外位置。
- Visual Oracle 草案已加入方向点积、tip/body 像素范围、scale、alpha、双分辨率和多方向检查；回归 Gate 已加入 required nodes、WASD 与 Objective completion。

当前输入哈希：

- `public/evidence/initial_bug.png`：`3F35E391F3E02496068DE95CB03B8FD5D558C9D08138FF4E84CE192BE916AB11`
- `public/TASK.md`：`257A9775F8DF7BD9FE7016EF07B07973ABFE11D624321EBABB5738BA57F335D4`

## 当前实验状态与结果

- 尚未调用 Codex 或任何其他模型；没有 Pilot trajectory、正式分数或模型结论。
- Step 4 Rev.2 的 Windows/OpenGL 环境 Gate 已有效通过并已在 `design/godot_preflight_rev2.md` 记录。
- 较早的 Bug 三轮均为 `0/45 + 0/35 + 20/20 = 20/100`，Oracle 三轮均为 `100/100` 且 `task_success=true`；但这些运行早于最新 Visual/Behavior Oracle 与初始场景修改，**已失效，不能作为最终证据**。
- 最新 shortcut 运行均被拒绝：asset swap、global flip、hidden/scale tracker、single direction、target swap 和 Threat offset edit 的 `task_success` 均为 `false`。其中 asset-swap 使用过旧 Godot import cache，仍须 clean-copy 重跑。
- 最后一批 shortcut 结束后未发现残留 Godot 进程。

## 尚未完成

- 生成最终 `task.json` 与 `validation.md`。
- 使用当前 evaluator 对 Bug State 与 Oracle State 各连续重跑三次，并比较每张 PNG 的 SHA-256。
- 从无 `.godot` cache 的 clean copy 重跑全部 shortcut，尤其是 asset swap。
- 完成 public multimodal leak audit；确认 Prompt、注释、测试和源码文本不直接泄露正确 profile/value。
- 清理并排除 `.godot/`、`*.uid`、`*.import`、`__pycache__/` 等派生缓存。
- 将 evaluator 从当前 private 工作布局整理到冻结目录契约，并完成最终 Markdown、凭据和 Git 验收。

## 恢复时第一步

先审查本检查点与当前 diff，不启动 Harness 或模型。随后修正/确认 public Prompt 的精确冻结文本，清理派生 cache，才从 cache-free public copy 开始全量 Step 5 验证。

## 需要重新运行的命令

以下命令仅在完成上述审查和 cache 清理后运行：

```powershell
Set-Location 'D:\pxc\EarnM\zijie'
$taskRoot = (Resolve-Path 'benchmark\task_001').Path
$godot = (Resolve-Path '.cache\tools\godot-4.7.1\Godot_v4.7.1-stable_win64.exe').Path

python -m py_compile "$taskRoot\private\evaluate.py"
& $godot --headless --path "$taskRoot\public" --import
& $godot --headless --path "$taskRoot\public" --script res://tests/smoke.gd

1..3 | ForEach-Object {
  python "$taskRoot\private\evaluate.py" `
    --candidate "$taskRoot\public" `
    --godot $godot `
    --output ".cache\validation\task_001\bug\run_$_"
}
```

Oracle 三轮与 shortcut 不应复用旧 workspace；先从 `public/` 建立独立 clean copy、应用
`private/oracle.patch` 或对应错误补丁，再以同一 `evaluate.py` 命令运行。最终还需重新执行
`git diff --check`、显式暂存清单、凭据扫描和 `.env` 未跟踪检查。
