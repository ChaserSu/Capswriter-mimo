# MiMo 语音输入

当前版本：**0.0.1**

按住热键说话，松开后自动识别并把文字粘贴到光标处的语音输入工具。
识别用 **mimo-v2.5-asr**，热词用音素（拼音）相似度匹配，润色（可选）用 **mimo-v2.6-flash**。

> 本项目只做「语音 → 文字输入」。字幕、时间戳、强制对齐等字幕功能已按需求删除。

> **参考说明**：本项目参考 [CapsWriter-offline 2.6 版本](https://github.com/HaujetZhao/CapsWriter-Offline)，
> 为适配 MiMo 做了最精简化的修改（识别改为 MiMo 云端 API，删除全部字幕/转录相关功能，
> 只保留语音输入链路）。**目前只测试了 macOS 版**，Windows / Linux 启动脚本已提供但未实测。
> 原项目为 MIT 许可证，本项目沿用 MIT 并保留原始版权声明（见 `LICENSE`）。

## 功能链路

```
按住右 Command 说话
   │ 松开
   ▼
麦克风录音（16kHz WAV，自动去首尾静音）
   ▼
mimo-v2.5-asr 语音识别（云端 API，自动标点）
   ▼
音素热词匹配（hot.txt 别名 + 音素模糊匹配 + hot-rule.txt 正则规则）
   ▼
文本后处理（繁简转换、中文数字转阿拉伯数字）
   ▼
（可选）mimo-v2.6-flash 润色
   ▼
粘贴到当前光标处（剪贴板 + 模拟 Cmd+V）
```

## 目录结构

```
Capswriter-mimo/
├── main.py            主程序（热键监听 + 流水线编排 + 调试命令）
├── config.py          接口地址、模型名、热键、热词路径等全部配置
├── config_local.example.py  密钥模板（复制为 config_local.py 后填入密钥，不入库）
├── core/
│   ├── recorder.py    麦克风录音 → WAV 字节
│   ├── asr.py         mimo-v2.5-asr 识别
│   ├── hotword.py     音素热词匹配
│   ├── textproc.py    繁简转换 / 中文数字转阿拉伯数字
│   ├── polish.py      mimo-v2.6-flash 润色（可选）
│   └── output.py      剪贴板 + 粘贴上屏
├── hot.txt            热词词表（规范写法 | 别名...）
├── hot-rule.txt       正则替换规则
├── requirements.txt
├── 启动.command        macOS 一键启动（双击运行）
├── 启动.bat            Windows 一键启动（双击运行）
├── 启动.sh             Linux 一键启动（双击或终端运行）
└── MiMo语音输入.desktop Linux 桌面快捷入口
```

## 安装与启动

三个启动器**共用同一份源代码**，首次运行都会自动创建 `.venv` 并安装依赖：

| 操作系统 | 启动方式 |
|---|---|
| macOS | 双击 `启动.command` |
| Windows | 双击 `启动.bat`（需先安装 [Python 3.10+](https://www.python.org/downloads/)，安装时勾选 Add to PATH） |
| Linux | 双击 `启动.sh`（文件管理器里选择“运行/在终端中运行”），或把 `MiMo语音输入.desktop` 放到桌面后右键“允许启动” |

### 配置密钥（首次必做）

仓库出于安全考虑**不含真实密钥**，启动前二选一：

1. 复制 `config_local.example.py` 为 `config_local.py`，填入你自己的 MiMo API Key；
2. 或设置环境变量 `MIMO_API_KEY`。

（本机已自动生成 `config_local.py` 的用户可跳过此步；该文件已被 `.gitignore` 排除，不会上传。）

手动方式（三平台通用）：

```bash
python3 -m venv .venv            # Windows 用 py -3 -m venv .venv
./.venv/bin/python -m ensurepip --upgrade   # 若 venv 缺 pip（Windows 路径为 .venv\Scripts\python.exe）
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python main.py
```

> 如果 `zhconv` 安装时构建失败，执行
> `./.venv/bin/python -m pip install --no-build-isolation zhconv` 后重试（启动器已自动处理）。

### 额外依赖

- **Linux**：剪贴板需要 `xclip`（X11）或 `wl-clipboard`（Wayland）：
  `sudo apt install xclip` 或 `sudo apt install wl-clipboard`；
  Debian/Ubuntu 建 venv 需 `sudo apt install python3-venv`
- **Windows / macOS**：无额外依赖

### 权限授权

| 平台 | 权限 | 授权位置 |
|---|---|---|
| macOS | 麦克风 | 系统设置 → 隐私与安全性 → 麦克风 |
| macOS | 辅助功能（粘贴） | 系统设置 → 隐私与安全性 → 辅助功能 |
| macOS | 输入监控（全局热键） | 系统设置 → 隐私与安全性 → 输入监控 |
| Windows | 麦克风 | 系统设置 → 隐私 → 麦克风 |
| Linux | 麦克风 | 桌面环境首次录音时授权；Wayland 下全局热键受限，建议用 X11 会话 |

macOS 一般给「终端」授权；双击 `启动.command` 则给「脚本编辑器/终端」授权。

## 使用

- **macOS**：按住 **右 Command** 说话，松开 → 识别 → 热词修正 → 粘贴（Cmd+V）到光标处
- **Windows / Linux**：按住 **右 Ctrl** 说话，松开 → 识别 → 热词修正 → 粘贴（Ctrl+V）到光标处
- **右 Option / 右 Alt** 说话，松开 → 同上，并强制调用 mimo-v2.6-flash 润色后上屏
- 识别结果同时进剪贴板，粘贴失败可直接手动粘贴

### 调试命令

```bash
./.venv/bin/python main.py --selftest     # 热词/文本逻辑自测（不联网）
./.venv/bin/python main.py --probe        # 测试 API 连通性
./.venv/bin/python main.py --cli a.wav    # 识别指定 WAV 文件（不粘贴）
```

## 配置（config.py）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `ApiConfig.base_url` | `https://token-plan-cn.xiaomimimo.com/v1` | 也可用环境变量 `MIMO_BASE_URL` 覆盖 |
| `ApiConfig.api_key` | 无（仓库不含密钥） | 优先环境变量 `MIMO_API_KEY`，其次 `config_local.py` |
| `ApiConfig.asr_model` | `mimo-v2.5-asr` | 识别模型 |
| `ApiConfig.polish_model` | `mimo-v2.6-flash` | 润色模型 |
| `shortcut_key` | macOS `cmd_r` / Win·Linux `ctrl_r` | 按住说话（pynput 键名，自动适配） |
| `force_polish_key` | `alt_r` | 松开后强制润色 |
| `language` | `auto` | 识别语言 auto/zh/en |
| `enable_polish` | `False` | `True` 时每句都自动润色 |
| `hotword_threshold` | `0.8` | 音素相似度阈值，越高越严格 |
| `enable_itn` / `enable_zhconv` | `True` | 文本后处理开关 |

## 热词

### hot.txt 词表

```
# 格式：规范写法 | 别名1 | 别名2 ...
MiMo | mimo | 米莫 | 迷莫 | 咪莫
CapsWriter | capswriter
```

匹配两步：
1. **精确匹配**：识别文本中出现任一别名（不区分大小写）→ 换成规范写法
2. **音素模糊匹配**：对漏网误写，取拼音（音素）相似度——zh/z、ch/c、sh/s、
   l/n、f/h、前后鼻音（an/ang、in/ing 等）视为相近音素——在文本滑窗中
   相似度 ≥ 阈值即替换（如「迷墨」→「MiMo」）

建议：遇到实际误识别的写法，直接追加为别名，这是最高效的修正方式。

### hot-rule.txt 正则规则

```
# 格式：正则查找 = 替换（支持 \2 反向引用）
(艾特)\s*(\w+)\s*点\s*(\w+) = @\2.\3
毫安时 = mAh
```

两个文件修改后**无需重启**，每句识别前自动热加载。

## 常见问题

- **说话没反应**：检查「输入监控」权限（macOS）；看终端是否有 `[录音] 开始 ...` 日志
- **识别了但没上屏**：检查「辅助功能」权限；文字已进剪贴板，手动粘贴即可
- **Linux 全局热键无效**：Wayland 不允许全局监听按键，请切换到 X11 会话使用
- **Linux 报剪贴板不可用**：安装 `xclip`（X11）或 `wl-clipboard`（Wayland）
- **Windows 双击闪退**：用 cmd 手动运行 `启动.bat` 查看报错；通常是 Python 未安装或未勾选 Add to PATH
- **接口报错/超时**：`--probe` 测试连通性；检查网络与 `config_local.py`（或环境变量）中的密钥
- **热词没生效**：`--selftest` 验证；调低 `hotword_threshold`（如 0.75）
- **中文数字误转换**：如「万一」被转成数字，可将 `enable_itn` 设为 `False`
- **音频过大**：单次说话控制在 1 分钟内（API 限制 base64 ≤ 10MB）

## 已验证

- 依赖安装（Python 3.10 venv）✔
- `--selftest` 热词/繁简/数字转换 ✔（迷墨→MiMo、三十二毫安时→32mAh）
- `--probe` mimo-v2.6-flash 连通 ✔
- 真实音频识别链路 ✔（`say` 生成测试语音 → mimo-v2.5-asr → 热词修正上屏）

> ⚠️ 以上均在 **macOS** 实测通过。**目前只测试了 macOS 版**；
> Windows / Linux 启动脚本按同一份源码提供，但未实测，欢迎反馈。
