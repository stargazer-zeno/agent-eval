# GameVisualFix Codex pilot Harness（暂停检查点）

> 2026-08-21 执行更新：`run_api_eval.py` 与 `api_models.json` 已作为 P0 可执行统一 API Harness 完成真实运行；本文件下方描述的 PowerShell/Codex strict Harness 仍是未通过 Windows sandbox gate 的 hardening 分支。`summarize_results.py` 负责生成去凭据的分数汇总与 hash-chain trajectory。任何 provider 403/timeout 都标为 invalid，不计模型分数。

> **WIP：不得执行真实模型 Pilot。** 本目录保存 2026-08-21 暂停时的 Step 6 草案；最新修改尚未完成
> fixture 回归，且凭据清理、失败分类和 production isolation canary 仍有阻塞。完整状态与恢复顺序见
> [CHECKPOINT.md](./CHECKPOINT.md)。保存本草案不会读取项目 `.env`，既有 fixture 自测也未调用模型。

## 已锁定的安全边界

- 每个 attempt 都从 public seed 创建全新的 sanitized workspace，删除 `.git`、`.env*`、
  `.codex`、`AGENTS*`、Godot/Python 缓存、旧 trajectory/result，以及名称含
  `oracle`、`hidden`、`evaluator`、`reference_patch` 的内容；拒绝 reparse point。
- sanitized workspace 初始化为无 remote 的 `main` 仓库，且仅包含一个 baseline commit。
- 模型只收到 public prompt、workspace 与图像。renderer 在 sibling snapshot 上运行；hidden
  evaluator 直到模型进程结束后才复制到 private control 区并执行，从不进入 agent workspace。
- 每个 attempt 使用独立 `CODEX_HOME`，只复制 `auth.json`，并收紧 NTFS ACL。该目录和 private
  evaluator 都排除在 archive；日志与 archive 前都执行凭据扫描。
- production 固定 native `codex.exe` 的版本与 SHA-256。命令禁用 network、web search、
  multi-agent、plugins、apps、browser/computer use 和依赖安装，并使用
  `--ignore-user-config --ignore-rules --strict-config`。
- 最多 4 个 Codex turns（initial + 最多 3 次 resume）、3 张 **fresh screenshot**、25 分钟、60 个唯一
  `command_execution` item。initial image 不计入 fresh 上限，因此最多发生 4 次 `--image` 注入。首轮从 `thread.started` 取 UUID，后续只允许显式
  `exec resume <UUID>`；禁止 `--last` 与 `--ephemeral`。
- action 只有 `observe` / `submit`。`observe` 触发一次 fresh render；`submit` 结束模型会话并进入
  hidden evaluation。所有原始 stdout JSONL、stderr、规范化事件、hash receipts 和最终 patch 均保留。
- 只对明确的 harness/infrastructure invalidation 做一次 fresh-attempt rerun。timeout、预算耗尽、
  malformed action、agent 造成的项目失败或评分失败均不重跑。

## Adapter 契约

Renderer（模型会话期间可调用，不能含 oracle 信息）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File renderer.ps1 `
  -Workspace <read-only-snapshot-copy> -OutputImage <fresh.png> -ReceiptPath <receipt.json>
```

退出码必须为 0，并产生非空图片。失败时 receipt 可写
`{"failure_class":"submission"}` 表示代码无法渲染；否则按 infrastructure failure 处理。

Hidden evaluator（模型进程结束后调用）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File evaluator.ps1 `
  -Workspace <evaluation-copy> -ResultPath <result.json>
```

退出码必须为 0，且 `result.json` 必须是 JSON object。evaluator 源文件本身不归档，只归档 SHA-256
receipt 与结果。

## 入口与防误调用

默认只做 preflight：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_pilot.ps1 `
  -ConfigPath .\config.json -Mode Preflight
```

真实模型路径需要同时给出 `-Mode ExecuteModel -ConfirmModelExecution`。fixture 模式改用本地 fake
进程，永远不启动 Codex 模型：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\self_test.ps1
```

## 尚需 production canary 的事项

- Windows sandbox 对 sibling/private 目录的实际读边界；正式实验优先用独立低权限 OS account/VM。
- 当前账号/模型下首轮与 resume 的完整 JSONL event 形状、`--output-schema` 遵循情况。
- Godot 4.7.1 renderer/evaluator adapter 的真实退出码、窗口焦点、截图稳定性和进程树回收。
- `taskkill /T` 作为超时兜底的进程树清理效果；production 可进一步替换成 Windows Job Object。

这些 canary 均不在本 fixture 自测中执行。
