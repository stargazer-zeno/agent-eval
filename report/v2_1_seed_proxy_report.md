# GameVisualFix v2.1 数据集设计与模型测试报告

## 结论

`gamevisualfix_v2_1_seed_proxy_3x2` 已完整执行。Seed Evolving 三题均形成可 resume、可观察、可提交、可隐藏评分的端到端结果，三题均为 100/100；Local Codex 在 T001/T003 为 100/100，在 T002 为有效 0/100。六个结果均为 `valid_canonical`，本 suite 没有正式 attempt 被标记为 `invalid_infrastructure`。

## 数据集设计

| Task | 难度标签 | 公开目标 | 隐藏 Oracle | 隐藏 case |
| --- | --- | --- | --- | ---: |
| T001 | Easy | Calibrate two HUD trackers so each points at its own moving world target. | 5 directions x 2 viewports, pixel direction/geometry checks, live updates, layout and asset integrity. | 10 |
| T002 | Medium | Correct a camera-space edge indicator while preserving the other tracker and camera behavior. | 3 camera rotations x 2 zoom levels x 3 viewports; objective direction, threat visibility and clean captures. | 18 |
| T003 | Hard | Keep a temporal trail on the correct side through direction changes and interruptions. | 6 fixed-tick replays x 2 physics rates, each with an 8-frame visual contact sheet. | 12 |

公开侧只提供任务描述、初始视觉证据、可读项目和有限场景 observation；参考补丁、case 矩阵与 evaluator 留在 Agent workspace 之外。三题统一以 Functional 45、Visual 35、Regression 20 计分，三项满分才算 task success。任务 prompt、Controller schema、Godot/Codex 二进制和同题输入 hash 在汇总时再次校验。

## Transport 修复

旧 v2 Seed 调用因 Agent Plan 的 Responses added envelope 缺少标准空容器，Codex 0.149 对 delta 报 `without active item`。v2.1 在 `127.0.0.1` 随机端口运行标准库代理，向固定 Seed 上游转发请求，为 message/reasoning item 和 part 补齐 `content`、`summary`、`text`、`annotations`、`logprobs`、`output` 等生命周期容器，统一生成单调 `sequence_number`，并在缺失时补 added/done。代理不改写 delta、reasoning、usage、HTTP 状态或完成状态；未知/畸形流直接失败。实现依据为 [official OpenAI Responses streaming events](https://developers.openai.com/api/reference/resources/responses/streaming-events)。

单元测试覆盖完整流、缺 text item、缺 reasoning item、multi-item、缺 done、HTTP error、畸形 SSE、单调序号、Seed 不完整 envelope 与凭据不落诊断。正式运行前，Harness fixture self-test、三题 import/smoke/capture/evaluator preflight、Seed 与 Local 三图/长 prompt/两次 resume canary 全部通过。成功 Seed canary 的 active-item error 为 0。

## 正式结果

| Task | Provider | F | V | R | Total | Success | Actions | Fresh obs | Seconds |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| T001 | seed_evolving | 45 | 35 | 20 | 100 | yes | 5 | 1 | 105.969 |
| T001 | local_codex | 45 | 35 | 20 | 100 | yes | 8 | 1 | 76.016 |
| T002 | seed_evolving | 45 | 35 | 20 | 100 | yes | 4 | 1 | 89.188 |
| T002 | local_codex | 0 | 0 | 0 | 0 | no | 4 | 2 | 107.485 |
| T003 | seed_evolving | 45 | 35 | 20 | 100 | yes | 3 | 1 | 111.875 |
| T003 | local_codex | 45 | 35 | 20 | 100 | yes | 6 | 1 | 80.172 |

Seed：成功率 3/3，平均 100.0，12 actions，3 次成功 fresh observation，总耗时 307.032s。Local：成功率 2/3，平均 66.667，18 actions，4 次成功 fresh observation，总耗时 263.673s。

最终 turn 的累计 usage 汇总：Seed input 223953、cached input 169832、output 9490、reasoning output 6222；Local input 412757、cached input 244480、output 5973、reasoning output 2393。这些是 Provider/Codex 返回的线程累计 telemetry，不代表计费核算。

## 过程与 Case Study

Seed 三题都完成补丁、fresh observation 和 submit，且没有 Controller action error。T002 中有 2 条上游流出现代理不负责猜测的 `function_call` item，代理按协议 fail closed，Codex 在同一 attempt 的既有 stream retry 内恢复并完成 4 个 Controller turn；这属于可观察的 transport recovery，不是额外 attempt。Local T002 的 `read_file -> observe -> observe -> submit` 没有写入补丁；隐藏 18-case 渲染链正常，但 bug 未修复，Functional/Visual/Regression 均为 0。这一结果按预注册规则保留，没有重跑。

## Lineage 与有效性

旧 `gamevisualfix_v2_seed_local_3x2` 的两次 Seed T001 transport invalid 和一次 Local T002 adapter-path invalid 均保留为历史，不进入 v2.1 指标。v2.1 adapter 开发中前两次 synthetic Seed canary 分别记录 active-item error，第三次修复后通过；它们不是正式任务 attempt。历史/诊断 lineage 共 5 条，详见机器矩阵的 `excluded_lineage`。

## 局限

每个模型只有 3 个合成 Godot 任务、每对只有 1 次有效 attempt，样本量不足以做显著性、稳定性或广泛泛化结论。五个满分产生 ceiling effect，Easy/Medium/Hard 是数据集设计标签，不等于对任一模型校准后的难度。Local T002 的单次失败也不能单独证明稳定的模型差异。运行使用单一机器、账户、Godot 4.7.1 与 Codex 0.149.0；外推到其他引擎、真实大型仓库或 Provider 版本需重新验证。

## 产物与安全

机器矩阵位于 `results/v2_1_seed_proxy_scores.json`；去 reasoning、去正文的 action/observation hash-chain 位于 `trajectories/v2_1_seed_proxy/`；对比与 Case Study 位于 `results/`。run-local Codex home 已回收，代理 receipt 只含事件类型、字段名、计数和结构哈希；`.env`、Authorization、API key、原始 Provider delta/reasoning 均不进入报告或 Git。
