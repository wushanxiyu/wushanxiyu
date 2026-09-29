# 实用脚本工具箱

> 一些平时用得上、写完就丢不掉的小工具 —— Windows 右键菜单、桌面壁纸、小说取名、邮箱筛选、安全中心开关。
>
> 全部零依赖（只用 Python 标准库 / 系统自带命令），拷过去就能跑。

[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows)](#环境要求)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](#环境要求)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 功能总览

| 工具 | 类型 | 一句话说明 |
| --- | --- | --- |
| [`win11右键菜单管理.bat`](#1-windows-右键菜单切换) | 批处理 | 一键在 Win11 新版 / Win10 旧版右键菜单之间切换 |
| [`wallpaper_changer.py`](#2-图床壁纸随机更换) | Python | 从图床链接随机拉一张图，自动设为桌面壁纸 |
| [`novel_name_generator.py`](#3-小说角色取名神器) | Python | 8 类角色、上百个姓名素材，随机 / 批量造名字 |
| [`foxmail_sender_filter.py`](#4-foxmail-邮件收件人筛选) | Python | 按发件人条件筛选邮件，去重导出收件人清单 |
| [`关闭windows安全中心.bat`](#5-windows-安全中心开关) / [`开启windows安全中心.bat`](#5-windows-安全中心开关) | 批处理 | 通过注册表策略关闭 / 恢复 Windows Defender |

---

## 1. Windows 右键菜单切换

**文件：** `win11右键菜单管理.bat`

Win11 的右键菜单默认是"折叠"的新版样式，很多人还是习惯 Win10 的完整菜单。这个脚本通过修改注册表在两种样式间切换。

**使用方法：**

1. 双击运行，脚本会自动申请管理员权限（UAC 提权）；
2. 按提示选择：
   - `1` → 切换到 **Win10 旧版**右键菜单；
   - `2` → 恢复 **Win11 新版**右键菜单；
3. 脚本会自动重启 `explorer.exe` 使修改生效。

**原理：** 新增 / 删除当前用户注册表项
`HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32`
（只改 `HKCU`，不影响系统其他用户）。

---

## 2. 图床壁纸随机更换

**文件：** `wallpaper_changer.py`

从配置好的图床链接列表里随机挑一张图片，下载到本地并设置为 Windows 桌面壁纸。适合把喜欢的图床上传链接攒起来，每次运行换一张。

**环境：** Windows + Python 3.8+（仅标准库，无需 `pip install`）。

**使用方法：**

```bash
# 随机选一张设为壁纸（先编辑脚本顶部的 WALLPAPER_URLS 列表）
python wallpaper_changer.py

# 从文件读取链接（每行一个，# 开头为注释）
python wallpaper_changer.py -f urls.txt

# 直接指定单个链接
python wallpaper_changer.py -u "https://example.com/a.jpg"

# 只下载不换壁纸
python wallpaper_changer.py -n
```

**参数说明：**

| 参数 | 说明 |
| --- | --- |
| `-f, --file` | 从文本文件加载图床链接列表 |
| `-u, --url` | 直接指定单个图床链接 |
| `-n, --no-change` | 仅下载，不修改壁纸 |

**小细节：** 内置了浏览器 `User-Agent`、跳过自签名证书校验、遇到 HTTP 400 自动改用 HTTPS 重试，对付常见的图床防盗链比较省心。

---

## 3. 小说角色取名神器

**文件：** `novel_name_generator.py`

写小说卡名字时的救急工具。内置单/复姓库与分风格名字库，按角色定位出名字，支持男 / 女 / 随机。

**角色类别：**

`主角` · `配角` · `路人` · `搞笑` · `普通` · `平庸` · `寓意` · `意境`

（其中 `搞笑`、`平庸` 两类不带姓氏，用于谐音梗与龙套名。）

**功能菜单：**

| 选项 | 功能 |
| --- | --- |
| 1 | 随机取名 |
| 2 | 按类别取名 |
| 3 | 批量取名（1–100 个） |
| 4 | 全类别展示 |
| 5 | 指定姓氏取名 |
| 6 | 选姓取名（先挑姓，再挑名） |
| 7 | 导出上次结果（`txt` / `csv`） |

**环境：** 任意平台 + Python 3.8+，直接运行：

```bash
python novel_name_generator.py
```

---

## 4. Foxmail 邮件收件人筛选

**文件：** `foxmail_sender_filter.py`

通过 IMAP 连接邮箱，按 **发件人** 条件筛选邮件，把命中的收件人（含姓名、收件类型、出现次数）提取出来，去重后导出，适合做客户名单整理、群发对象统计。

**环境：** Python 3.8+（仅标准库，无需安装依赖）。

**两种用法：**

```bash
# 双击 / 直接运行 → 交互模式，逐步引导操作
python foxmail_sender_filter.py

# 命令行模式
python foxmail_sender_filter.py \
  --email you@company.com \
  --password "授权码" \
  --from-filter boss@company.com \
  --imap-preset qq
```

**常用参数：**

| 参数 | 说明 |
| --- | --- |
| `--imap-preset` | 预设服务器：`qq` / `163` / `aliyun` / `outlook` / `gmail` |
| `--imap-host` | 自定义 IMAP 服务器地址 |
| `--email` / `--password` | 邮箱账号与密码（企业邮通常填授权码） |
| `--from-filter` | 发件人筛选条件（邮箱 / 域名 / 关键词，逗号分隔多个） |
| `--folders` | 邮件文件夹，多选用逗号分隔（默认 `INBOX`） |
| `--search` | IMAP 搜索条件（默认 `ALL`） |
| `--max-emails` | 最大读取邮件数（`0` = 不限） |
| `--output, -o` | 输出文件路径前缀 |
| `--config` | 配置文件（默认 `foxmail_config.json`） |
| `--init-config` | 生成配置文件模板 |

**输出：** 结果保存在 `foxmail_output/` 目录下，包含三个文件 ——

- `收件人筛选_<时间>_详细.csv`：逐条收件人记录；
- `收件人筛选_<时间>_汇总.csv`：去重后的收件人清单；
- `收件人筛选_<时间>_邮箱列表.txt`：纯邮箱地址，方便直接粘贴。

**附加能力：** 可自动检测本机 Foxmail 安装路径与已配置的邮箱账户。

---

## 5. Windows 安全中心开关

**文件：** `关闭windows安全中心.bat` / `开启windows安全中心.bat`

在装有第三方杀毒软件、与 Windows Defender 冲突的场景下，可通过修改系统策略注册表来关闭 / 恢复 Defender。

**使用方法：** 双击运行，脚本自动 UAC 提权，执行后按提示重启电脑生效。

**做了什么：** 修改 `HKLM\SOFTWARE\Policies\Microsoft\Windows Defender`（含 `Real-Time Protection`、`Signature Updates`、`Spynet` 等子键）下的策略值，例如 `DisableAntiSpyware`、`DisableRealtimeMonitoring`、`DisableBehaviorMonitoring`、`DisableIOAVProtection` 等。

> [!WARNING]
> 关闭安全中心会降低系统防护能力。**请在已安装并可正常工作的第三方杀毒软件时再使用**，用完建议及时用 `开启windows安全中心.bat` 恢复。脚本需要管理员权限、会写入系统级注册表，请确认自己了解后果后再运行。

---

## 目录结构

```
.
├── win11右键菜单管理.bat        # 右键菜单样式切换
├── wallpaper_changer.py         # 图床壁纸随机更换
├── novel_name_generator.py      # 小说角色取名
├── foxmail_sender_filter.py     # 邮件收件人筛选
├── 关闭windows安全中心.bat       # 关闭 Defender
└── 开启windows安全中心.bat       # 恢复 Defender
```

## 环境要求

- **Python 脚本**：Python 3.8+，仅使用标准库，无需安装第三方依赖；
- **批处理脚本**：Windows 10 / 11，需要管理员权限（脚本会自动提权）；
- 壁纸脚本仅支持 Windows（依赖 `user32.dll`），取名与邮件脚本跨平台可用。

## 免责声明

本仓库脚本主要用于个人学习与日常效率提升，其中涉及注册表修改的功能请自行评估风险并做好备份。因使用本仓库脚本造成的任何系统问题，由使用者自行承担。

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源，你可以自由使用、修改和分发。

---

如果这些小工具帮到了你，欢迎 Star ⭐
