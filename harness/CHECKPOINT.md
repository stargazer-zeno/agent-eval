# Step 6 Harness 暂停检查点

> 日期：2026-08-21
> 状态：源码草案已保存；禁止使用 `-Mode ExecuteModel`，直至全部阻塞项关闭。

## 已保存内容

- sanitized single-commit/no-remote workspace 草案。
- Codex 0.142.5 native binary 版本与 SHA-256 固定，以及显式 thread UUID 的 `exec/resume --image --json --output-schema` 调用。
- `gpt-5.6-sol` 配置入口、`ultra` reasoning、default service tier（未显式覆盖）。
- 严格 `action + summary` JSON Schema。
- 4 turns、initial 之外最多 3 张 fresh screenshot、25 分钟 Codex、35 分钟 run、60 command events 的预算逻辑。
- run-local Godot PATH、raw/normalized trajectory、hash-chain/receipt、凭据扫描、renderer/evaluator adapter 与一次 infrastructure rerun 的实现草案。
- fixture、自测和公开入口文件；生成的 `.selftest/` 产物未保存。

## 当前实验状态与结果

- 未运行 Task 001、未调用真实 Codex 模型、未生成 Pilot 分数或 trajectory。
- 较早 Harness 版本曾两次通过 fixture 的 `observe → render → resume → submit` 与单次 infrastructure rerun 流程。
- Codex 0.142.5 help parse、`ultra` config load 和 Godot 4.7.1 version 检查曾通过。
- 上述通过发生在最新 Godot PATH、strict action、token telemetry 与 hash-chain 修改之前；当前保存版本尚未重新执行完整 self-test。

## 阻塞与未完成项

- run-local `auth.json` 尚未在所有成功/异常路径的 `finally` 中精确删除；当前仅保证不归档。
- evaluator 非零退出与“模型提交未通过”必须和 infrastructure crash 分开；否则会错误触发免费重跑。
- renderer/evaluator adapter 的最小环境、网络关闭和 stdout/stderr 保存尚需收口。
- `evaluate.ps1` 尚未成为 Controller 实际使用的唯一 standalone evaluator 入口。
- Windows sandbox 对 main repo、private/control 和 run-local credential 的读取阻断尚未通过真实 production canary；同用户 ACL 本身不足以作为证明。
- 初始与 resume 图片感知、JSONL 真实事件形状、进程树超时回收、环境中无 key/token/secret 均未完成无任务 canary。
- 60-command 限制当前在观察到第 61 个 JSONL item 时终止，尚未证明能在命令开始前硬阻断。
- normalized hash-chain 的最新实现和 head/count receipt 尚未重新自测。

## 恢复时第一步

先实现 run-local `auth.json` 的 `finally` 清理与不存在断言，同时修正 evaluator failure classification；这是再次运行 fixture 前的第一步。完成前不得创建真实 Task session。

## 需要重新运行的命令

完成上述代码修正后，先运行无模型 fixture：

```powershell
Set-Location 'D:\pxc\EarnM\zijie'
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
  -File .\harness\tests\self_test.ps1
git status --short
```

只有当最新 self-test 全绿、attempt 内不存在 `control\codex_home\auth.json`、archive 不含 private/auth、
hash-chain receipt 可复算后，才实现并运行不含 Task 001 信息的 production canary。Canary 通过前不得运行
`run_pilot.ps1 -Mode ExecuteModel`。
