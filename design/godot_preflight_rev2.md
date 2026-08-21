# Godot 4.7.1 环境预检 Rev.2：受控 Windows 窗口渲染

> 日期：2026-08-21
>
> 结论：**PASS — 允许 Step 4 冻结 Benchmark Specification。**

## 1. 修订原因与授权边界

初始预检已经证明 Windows official build 的严格 `--headless` 使用 dummy/null rendering device，不能生成 runtime PNG；该失败及影响完整保留在 [Rev.1 blocker](./godot_preflight.md)，不覆盖、不删除。

用户于 2026-08-21 明确批准方案一：允许 Controller 使用非 `--headless` 的真实 Windows renderer，在隐藏 background window 中由 Godot 内部读取 Viewport 并保存 PNG。授权不改变 Task、Prompt、Oracle、预算、模型或 agent-visible workspace，只修订 screenshot transport 的基础设施假设。

## 2. 固定环境

| 项目 | 值 |
| --- | --- |
| OS | Microsoft Windows 11 专业版 10.0.22631，64-bit |
| CPU | AMD Ryzen 5 5600H with Radeon Graphics |
| Godot | `4.7.1.stable.official.a13da4feb` |
| Main EXE SHA-256 | `323F9C4CC5DB674E98815CDD8E69DA007D5EFC779ABEDC8C0E42883B7FDEA12A` |
| Display server | `Windows` |
| Rendering driver | OpenGL 3.3 / `opengl3` |
| Rendering method | `gl_compatibility` |
| Probe viewport | 320×180 |
| Fixed FPS | 60 |
| Window policy | `Start-Process -WindowStyle Hidden`，不最小化 |
| Screenshot source | 项目内部 `ViewportTexture`，不是 OS desktop screenshot |

每次 run 使用新的 Godot process。Probe 在 `RenderingServer.frame_post_draw` 后读取 Viewport，保存 RGBA8 PNG，并独立统计非黑像素与四组固定语义颜色。

## 3. Instrumentation incident

首次 windowed run 已成功渲染，但 PowerShell runner 在读取 `Process.ExitCode` 前没有正确物化/刷新 handle，导致 telemetry 中 exit code 为 null；这次运行保留为 `invalid_telemetry`，不计入三次 canonical Gate，也没有被覆盖或追认为有效样本。

唯一一次诊断只修复 evidence collection：显式等待 process、刷新 handle、将 stdout/stderr 分离为文件，并避免 `Get-Content -Raw` 的 ETS 属性污染。它没有修改 probe scene、capture timing、renderer、分辨率或成功阈值。随后只增加一个 replacement run，使 canonical set 为 run 2–4。

## 4. Canonical 结果

| 指标 | Run 2 | Run 3 | Run 4 |
| --- | ---: | ---: | ---: |
| Godot exit code | 0 | 0 | 0 |
| stderr bytes | 0 | 0 | 0 |
| PNG size | 320×180 | 320×180 | 320×180 |
| PNG file bytes | 1,534 | 1,534 | 1,534 |
| Non-black pixels | 57,600 | 57,600 | 57,600 |
| Background pixels | 39,648 | 39,648 | 39,648 |
| Cyan pixels | 3,740 | 3,740 | 3,740 |
| Gold pixels | 10,584 | 10,584 | 10,584 |
| Red pixels | 1,824 | 1,824 | 1,824 |
| PNG SHA-256 | `32717218508F56294B7A922E6FEDD7AE9A9B6B7E98A400796A24344F90FD2014` | 相同 | 相同 |
| Residual Godot processes | 0 | 0 | 0 |

逐像素比较：

- Run 2 ↔ Run 3：`different_pixels=0`、`max_delta=0`、`total_delta=0`；
- Run 2 ↔ Run 4：`different_pixels=0`、`max_delta=0`、`total_delta=0`。

三次 stdout 均确认 `display_server=Windows`、OpenGL 3.3 Compatibility 与 AMD Radeon Graphics。所有原始日志和 PNG 保存在被 `.gitignore` 排除的 `.cache/preflight/godot-4.7.1/`，不进入提交。

## 5. 窗口与焦点观察

三次运行的窗口监测均为 `visible=False`、`iconic=False`：窗口完全隐藏但没有最小化，真实 renderer 仍持续产出相同像素。Windows 将请求的完全屏外坐标钳制到桌面边缘，但窗口不可见，因此没有采用 off-screen visible fallback。

Godot 进程三次均曾短暂成为 foreground，随后前台 PID 回到原控制进程。截图来自内部 Viewport，不依赖窗口是否被遮挡或用户观察，因此该现象不影响 PNG 正确性；它仍构成宿主机 UI 干扰风险，正式 Harness 必须：

- 串行运行 renderer，不与人工桌面操作并发；
- 记录 capture 前后 foreground PID；
- 使用固定隐藏策略且不临时最小化；
- 以 Job Object/超时确保所有子进程结束；
- 若焦点变化导致任何重复性差异，立即把运行判为 infrastructure invalid。

## 6. Gate 结论

Rev.2 满足继续条件：精确版本可调用、真实 renderer 可启动、三次新进程生成非黑 PNG、尺寸/语义像素/文件 hash 完全一致、stderr 为空且无残留进程。因此允许冻结 `design/benchmark_spec.md` 并进入 Task 001 实现。

本结论只证明当前主机上的受控 capture transport 可行，不证明未来 Agent submission 必然可渲染。Agent 修改导致 parse/runtime/capture 失败属于有效模型结果；Controller 或 renderer 本身在已知正常 fixture 上失败才属于 infrastructure invalid。
