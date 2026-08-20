# Godot 4.7.1 环境预检记录

> 日期：2026-08-21
>
> 结论：**BLOCKED — 严格 `--headless` 模式无法生成 runtime PNG。**
>
> 影响：按冻结计划，本项目在 Step 4 停止；未冻结 `benchmark_spec.md`，未进入 Task 001 实现、Harness 或模型调用。

## 1. 预检范围与通过标准

本次预检发生在任何 Benchmark 代码或模型实验之前，只验证冻结方案依赖的基础能力：

1. 官方 Godot 4.7.1 Windows x86-64 standard build 可下载并通过官方 SHA-512 校验；
2. 可执行文件版本与 hash 可固定；
3. clean-copy 最小项目能完成 import，并以 `gl_compatibility` 启动；
4. 严格 `--headless` runtime 能从 Viewport 连续生成三张非黑 PNG；
5. 截图尺寸、语义像素、stdout/stderr 与退出码可由未来 Harness 稳定获取。

第 4 项是硬 Gate。冻结规则要求首张失败后只做一次诊断复现；若仍不能渲染，则记录 blocker 并停止，不自动尝试 windowed/offscreen、虚拟显示、其他引擎或伪造截图。

## 2. 主机与工具

| 项目 | 冻结值 |
| --- | --- |
| OS | Microsoft Windows 11 专业版 10.0.22631，64-bit |
| CPU | AMD Ryzen 5 5600H with Radeon Graphics |
| Godot archive | `Godot_v4.7.1-stable_win64.exe.zip`，84,198,557 bytes |
| Godot version | `4.7.1.stable.official.a13da4feb` |
| Renderer request | `gl_compatibility` |
| Portable executable | `.cache/tools/godot-4.7.1/Godot_v4.7.1-stable_win64.exe` |

下载自 [Godot 4.7.1 官方 archive](https://godotengine.org/download/archive/4.7.1-stable/)，并使用该 release 的 [官方 `SHA512-SUMS.txt`](https://github.com/godotengine/godot/releases/download/4.7.1-stable/SHA512-SUMS.txt) 校验。

| Artifact | Digest |
| --- | --- |
| ZIP SHA-512 | `A6B02C527C18BA9936E63562032701432B2DC57D98D6483CEACCB00FE14AF16AF5773AE8A55E7B4D614EDF121C4D9E420D870F804EDB1DAC16362298A01CE6C4` |
| Main EXE SHA-256 | `323F9C4CC5DB674E98815CDD8E69DA007D5EFC779ABEDC8C0E42883B7FDEA12A` |

ZIP 的本地 SHA-512 与官方清单条目完全一致。所有下载、解压、临时项目与探针均位于 `.gitignore` 已排除的 `.cache/`，未进入 Git。

## 3. 最小探针

临时 clean-copy 项目使用 320×180 viewport 和 `gl_compatibility`。`Node2D._draw()` 绘制高对比背景、圆、矩形与三角形；capture script 等待两轮 `process_frame` 与 `RenderingServer.frame_post_draw` 后调用：

```gdscript
var image := get_viewport().get_texture().get_image()
image.save_png(output_path)
```

有效 PNG 必须满足：文件存在、尺寸为 320×180，且亮度阈值以上的非黑像素不少于 1,000。

## 4. 执行结果

实际命令如下；原始探针使用 `2>&1` 合流输出，因此本记录不声称具备严格的 stdout/stderr 分离：

```powershell
# Version
& '<godot-console.exe>' --version 2>&1

# Clean import
& '<godot-console.exe>' --headless --path '<probe-project>' --import --verbose 2>&1

# Capture attempt 1
& '<godot-console.exe>' --headless --path '<probe-project>' --fixed-fps 60 `
  --quit-after 120 --verbose -- --output '<captures>/headless_capture_1.png' 2>&1

# The single permitted diagnosis
& '<godot-console.exe>' --headless --path '<probe-project>' --fixed-fps 60 `
  --quit-after 10 --verbose -- --diagnose 2>&1
```

路径占位符均解析到 §2 所列 `.cache/` portable tool 与 probe 目录；使用占位符避免文档绑定作者机器的绝对盘符。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 官方 archive checksum | PASS | 本地 ZIP SHA-512 与官方清单一致 |
| 版本固定 | PASS | `4.7.1.stable.official.a13da4feb` |
| Clean headless import | PASS | 退出码 0，生成 `.godot/` import state |
| 第一次 runtime capture | **FAIL** | 进程退出后目标 PNG 不存在，PNG count 为 0 |
| 第二、三次 capture | NOT RUN | 首次失败即按预注册规则进入唯一诊断，不继续凑样本 |
| 唯一诊断 | **FAIL / ROOT CAUSE CONFIRMED** | `display_server=headless rendering_device_null=true`；Viewport texture 使用 dummy backend，无法返回可保存图像 |

严格 `--headless` 仍可解析项目并以退出码 0 结束，因此单看进程退出码会产生假阳性；必须把实际 PNG 与非黑像素检查作为 Gate。

诊断中的关键原始输出为：

```text
HEADLESS_DIAGNOSTIC display_server=headless rendering_device_null=true
ERROR: Parameter "t" is null.
   at: texture_2d_get (./servers/rendering/dummy/storage/texture_storage.h:110)
SCRIPT ERROR: Cannot call method 'is_empty' on a null value.
   at: _ready (res://capture.gd:18)
DIAGNOSTIC_EXIT=0
PNG_COUNT=0
```

第一次 capture 的 Godot 退出码同样为 0，但文件门禁记录为 `CAPTURE_EXIT=0 EXISTS=False`。这进一步证明未来 Harness 不能仅依赖引擎退出码。

## 5. 根因与边界

唯一诊断确认当前 Windows official build 在严格 `--headless` 下使用 headless display server 与 null rendering device。Viewport texture 读取落到 dummy `texture_2d_get`，未产生真实渲染像素。这与 Godot 官方说明一致：headless rendering server 不进行真实渲染并返回 dummy 值，参见 [`RenderingServer` 文档](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html)。

这不是 Task 001、Agent Patch 或 evaluator 的失败，而是冻结环境假设不成立。以下替代方案均可能可行，但会改变已批准的环境/隔离设计，本阶段没有擅自尝试：

- 使用普通 Windows display driver，在隐藏窗口中运行并捕获；
- 使用可渲染的 offscreen/display 配置，而不是严格 `--headless`；
- 使用 Windows Sandbox、VM 或虚拟显示；
- 改用非 Viewport 的 CPU 语义渲染或其他引擎。

## 6. 停止状态与恢复条件

按自动执行计划的硬停止规则：

- 不创建 `design/benchmark_spec.md`；
- 不实现 `benchmark/task_001/`；
- 不创建 Harness；
- 不复制 Codex 凭据，不调用模型，不生成实验或 trajectory；
- 不把该基础设施失败包装为 Codex pilot 结果。

恢复需要用户明确批准一种非严格-headless 的 Windows 渲染/截图策略。恢复后应先建立新的 Step 4 preflight revision，连续完成三次非黑 PNG 与稳定性检查，再冻结 Benchmark Spec；不得删除或覆盖本 blocker 记录。
