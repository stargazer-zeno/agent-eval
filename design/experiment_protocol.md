# Codex 单模型 Pilot 实验协议（Step 6 暂停草案）

> 2026-08-21 执行更新：原严格 Codex Harness 保留为 hardening 设计，但当前 Windows sandbox gate 未通过。为优先走通完整流程，本轮新增 `harness/run_api_eval.py` controller-mediated API Harness，统一评测 Qwen、Seed、GPT 和 Claude 配置；文件动作被限制在 public clean workspace，hidden evaluator 终止后执行。该 P0 放宽不等价于 VM/Windows Sandbox 隔离。真实结果与 validity 分类见 `results/scores.json`。

> Seed Evolving 更新：`harness/run_codex_provider_eval.py` 通过 run-local Codex custom provider 接入 `doubao-seed-evolving`，使用 Agent Plan Responses endpoint、环境变量 key 和同一 thread resume。canonical 逐文件 run 超时；唯一 compatibility rerun 预载同一 public text/PNG，必须标记 `comparison_eligible=false`，不能与 Qwen 作严格效率或排名比较。

> 状态：已保存为 tracked WIP；最新 Harness 修改尚未重新回归，真实模型 canary 未执行。恢复前必须先解决
> [Harness 暂停检查点](../harness/CHECKPOINT.md) 中的阻塞项。本文件不是已冻结、可执行的正式实验协议。

## 1. 运行单位与冻结输入

每个 run 固定一个 Task 版本、public seed、public prompt、initial screenshot、模型 ID、native Codex
binary、action schema、renderer 和 hidden evaluator。Controller 在运行前记录这些输入或 adapter 的
SHA-256；模型接触任务后不得原地修改 Task、Oracle、阈值或预算。

Canonical 入口为 `run_pilot.ps1`。默认 `Preflight` 不调用模型；真实运行必须显式使用
`-Mode ExecuteModel -ConfirmModelExecution`。`Fixture` 使用 fake Codex/renderer/evaluator 子进程，
不调用任何模型。

## 2. Workspace 与信息隔离

每个 attempt 从 public seed 建立全新 sanitized copy。以下内容拒绝复制：原 `.git` 历史与 remote、
`.env*`、`.codex`、`AGENTS*`、Godot/Python 缓存、旧 result/trajectory，以及路径名包含
oracle、hidden、evaluator、reference patch 的文件；任何 reparse point 也拒绝。随后初始化
`main`，创建且仅创建一个 baseline commit，并记录 clean/no-remote invariant 与 tree manifest。

Agent 只看 workspace、public prompt 与当前图片。`observe` 后 Controller 冻结 workspace manifest，
复制到新的 render directory，再由 trusted renderer 产生图片。hidden evaluator 直到所有 Codex
进程结束后才复制到 private control directory；它只读取独立 evaluation copy。canonical standalone
评测入口为 `evaluate.ps1`，也必须在 Agent 进程结束后调用。

`workspace-write` 的 Windows 实际 read boundary 仍需 canary；正式 pilot 应优先使用独立低权限 OS
account 或 VM，不能只依靠随机目录名隐藏 private artifact。

## 3. Codex 0.142.5 调用

production 固定 native `codex.exe` 版本 `codex-cli 0.142.5` 与 SHA-256
`645F5A1A0347ABB2B31FAE4E594C198AD00E3A4B4A999DCFA3A66C0D0F8CD43B`。共同参数为：

```text
-a never -s workspace-write -C <workspace> -m <pinned-model>
-c sandbox_workspace_write.network_access=false
-c shell_environment_policy.inherit="none"
-c shell_environment_policy.ignore_default_excludes=false
-c tools.web_search=false
-c allow_login_shell=false
-c cli_auth_credentials_store="file"
--disable multi_agent --disable plugins --disable apps
--disable browser_use --disable computer_use
--disable skill_mcp_dependency_install
```

首轮：

```text
exec --ignore-user-config --ignore-rules --strict-config --json --color never
--image <initial.png> --output-schema <action.schema.json> <prompt>
```

续轮：

```text
exec resume --ignore-user-config --ignore-rules --strict-config --json
--image <fresh.png> --output-schema <action.schema.json> <THREAD_UUID> <observation-prompt>
```

THREAD_UUID 只能来自首轮 `thread.started` 并须通过 UUID 校验；禁止 `--last`、`--ephemeral`。最终
`agent_message.text` 必须本地再次验证为 `observe|submit` schema。

## 4. Auth 与进程环境

每个 attempt 创建独立 `CODEX_HOME`，只从 operator CODEX_HOME 复制 `auth.json`，核验副本 hash 并
移除继承 ACL，仅允许当前用户、SYSTEM、Administrators。Codex 所有 turn 共用该目录，便于显式
session resume。`auth.json`、完整 CODEX_HOME 与 private adapter 永不进入 archive；日志和 archive
前执行凭据模式扫描，命中时标为 `security_invalid` 且不重跑。

正式 canary 必须确认：复制后的 `codex login status` 可用、token refresh 只写 run-local 文件、ACL
对 Windows sandbox token 的实际阻断效果，以及代理/自定义 CA 所需环境变量。

## 5. 视觉闭环与预算

- Controller turns：4（initial + 最多 3 次 resume）。
- Fresh screenshots：最多 3；initial image 不计入，因此 `--image` 最多注入 4 次。
- Codex wall time：25 分钟，逐轮上限 10 + 5 + 5 + 5 分钟；capture 时间不计入 Codex wall。
- 完整 run hard deadline：35 分钟。
- unique `command_execution` items：60；按 item ID 在 `started/completed` 间去重，发现第 61 个即终止进程树。
- Public capture：每次 90 秒；hidden evaluator：180 秒。
- token telemetry gate：input 150,000、output 20,000；CLI 无法 turn 中途硬切，只在
  `turn.completed` 后检查，超限是有效 `budget_exhausted`。

`observe` 触发新的 snapshot + renderer process + fresh PNG + 同 thread resume；`submit` 停止 Agent
session，冻结 patch/manifest，再执行 hidden evaluation。evaluator-only 图片不得回流 Agent。

## 6. Trajectory 与审计产物

每个 turn 原样保存 stdout JSONL 与 stderr；同时生成逐行 normalized JSONL，补充 `run_id`、attempt、
turn、capture timestamp，并保留未知 Codex event。Controller 另外写入 turn/render/attempt lifecycle
event。唯一 command item、usage、图片、adapter、workspace 和 evaluation result 均有 hash/预算 receipt。

归档包含 raw/normalized trajectory、submission patch、workspace final state、公开截图、评分结果与公开
receipts；排除 `.git`、run-local auth、private renderer/evaluator 源码。所有 attempt（包括 invalid）都保留，
不能择优覆盖。

## 7. Valid、invalid 与唯一重跑规则

有效模型失败且不得重跑：拒绝/无 patch、错误命令、schema action 无效、未请求观察、timeout/预算耗尽、
Agent 修改导致 public render 失败（adapter receipt 标 `submission`）、错误提交、hidden test 失败。

仅下列情况为 `infrastructure_invalid`：输入/config/native binary hash 不一致、provider/CLI/Controller crash、
JSONL transport 损坏、thread UUID 缺失/改变、renderer 自身 infrastructure failure、hidden evaluator failure。
第一次允许一次全新 sanitized workspace + 新 CODEX_HOME + 新 session 的 attempt；记录 parent/child lineage，
保留首次 invalid attempt。第二次仍 invalid 则停止。`security_invalid` 与 benchmark defect 均停止、不重跑。

## 8. Canary 门禁（真实 pilot 前必须完成）

1. `codex exec --help` / `exec resume --help` 的 flag parse 与 hardened `doctor config.load`。
2. run-local `CODEX_HOME` 的 `login status`，以及不读取用户 `config.toml`。
3. `debug prompt-input --image` 能看见 initial PNG；真实首轮 JSONL 事件形状与 schema action。
4. 同一显式 UUID 的一次 `resume --image`，确认 fresh PNG 确实进入同 thread。
5. Windows sandbox/private ACL、shell network denial、outside-workspace read denial。
6. Godot 4.7.1 capture/evaluator 的稳定性、90/180 秒 timeout 和完整进程树回收。

第 1 项的 help/本机 config 语法已做无模型核验；第 2–6 项仍需单独 canary，其中第 3–4 项会产生模型调用，
必须获得正式 pilot 授权后执行。
