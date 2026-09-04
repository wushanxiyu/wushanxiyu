"""
Foxmail 企业微信邮箱 - 按发件人筛选收件人信息
根据指定的发件人条件，筛选邮件并列出所有收件人的详细信息。

使用方式:
  双击运行 → 进入交互模式，逐步引导操作
  命令行运行:
    python foxmail_sender_filter.py --email user@company.com --password PASS --from-filter boss@company.com

依赖: 无额外依赖（仅使用Python标准库）
"""

import os
import sys
import csv
import re
import time
import json
import argparse
import datetime
import email
import email.header
import imaplib
from collections import OrderedDict

# ============ 常见IMAP服务器 ============
IMAP_SERVERS = {
    "1": ("腾讯企业邮 (QQ企业微信邮箱)", "imap.exmail.qq.com"),
    "2": ("网易企业邮 (163)", "imap.qiye.163.com"),
    "3": ("阿里企业邮", "imap.qiye.aliyun.com"),
    "4": ("Outlook / Office 365", "outlook.office365.com"),
    "5": ("Gmail", "imap.gmail.com"),
}

CONFIG_FILE = "foxmail_config.json"

# 常见 IMAP 文件夹名 → 中文名称映射
FOLDER_NAME_MAP = {
    "INBOX": "收件箱",
    "Sent Messages": "已发送",
    "Sent": "已发送",
    "Drafts": "草稿箱",
    "Trash": "已删除",
    "Deleted Messages": "已删除",
    "Junk": "垃圾邮件",
    "Spam": "垃圾邮件",
    "Archive": "归档",
    "Archives": "归档",
    "Flagged": "星标邮件",
    "Important": "重要邮件",
    "Starred": "星标邮件",
    "All Mail": "全部邮件",
    "All": "全部邮件",
    "Outbox": "发件箱",
    "Templates": "模板",
    "Notes": "备忘",
    "Junk Email": "垃圾邮件",
    "Chat": "聊天",
}


# ============================================================
#  Foxmail 自动检测
# ============================================================

def find_foxmail_install():
    """自动检测 Foxmail 安装路径"""
    # 常见安装路径
    common_paths = [
        os.path.join(os.environ.get("ProgramFiles", ""), "Foxmail 7.2"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Foxmail 7.2"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Foxmail"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Foxmail"),
        r"D:\Program Files\Foxmail 7.2",
        r"D:\Program Files (x86)\Foxmail 7.2",
        r"C:\Program Files\Foxmail 7.2",
        r"C:\Program Files (x86)\Foxmail 7.2",
    ]

    # 检查常见路径
    for path in common_paths:
        foxmail_exe = os.path.join(path, "Foxmail.exe")
        if os.path.isfile(foxmail_exe):
            return path

    # 通过注册表查找
    try:
        import winreg
        for hive_key in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
            for sub_key in [r"Software\Foxmail", r"Software\Tencent\Foxmail"]:
                try:
                    key = winreg.OpenKey(hive_key, sub_key, 0, winreg.KEY_READ)
                    install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    winreg.CloseKey(key)
                    if install_path and os.path.isfile(os.path.join(install_path, "Foxmail.exe")):
                        return install_path
                except (OSError, FileNotFoundError):
                    pass
    except ImportError:
        pass

    return None


def detect_foxmail_accounts(foxmail_path):
    """从 Foxmail Storage 目录检测已配置的邮箱账户"""
    storage_path = os.path.join(foxmail_path, "Storage")
    if not os.path.isdir(storage_path):
        return []

    accounts = []
    for entry in os.listdir(storage_path):
        entry_path = os.path.join(storage_path, entry)
        if os.path.isdir(entry_path) and "@" in entry:
            # 文件夹名就是邮箱地址
            email_addr = entry.strip()
            # 检查是否有邮件数据（Accounts 或 Mails 子目录）
            has_data = (
                os.path.isdir(os.path.join(entry_path, "Accounts")) or
                os.path.isdir(os.path.join(entry_path, "Mails"))
            )
            if has_data:
                accounts.append(email_addr)

    return accounts


def get_imap_server_for_email(email_addr):
    """根据邮箱地址自动推断 IMAP 服务器"""
    domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""

    # 常见邮箱域名 → IMAP 服务器映射
    domain_map = {
        # 腾讯企业邮 / QQ企业微信邮箱
        "exmail.qq.com": "imap.exmail.qq.com",
        # QQ 邮箱
        "qq.com": "imap.qq.com",
        # 网易企业邮
        "qiye.163.com": "imap.qiye.163.com",
        "qiye.126.com": "imap.qiye.163.com",
        # 网易个人邮箱
        "163.com": "imap.163.com",
        "126.com": "imap.126.com",
        "yeah.net": "imap.yeah.net",
        # 阿里企业邮
        "qiye.aliyun.com": "imap.qiye.aliyun.com",
        # 阿里个人邮箱
        "aliyun.com": "imap.aliyun.com",
        # Outlook / Office 365
        "outlook.com": "outlook.office365.com",
        "hotmail.com": "outlook.office365.com",
        "office365.com": "outlook.office365.com",
        # Gmail
        "gmail.com": "imap.gmail.com",
        # 新浪
        "sina.com": "imap.sina.com",
        "sina.cn": "imap.sina.cn",
        # 搜狐
        "sohu.com": "imap.sohu.com",
        # 139 邮箱
        "139.com": "imap.139.com",
        # 21CN
        "21cn.com": "imap.21cn.com",
    }

    if domain in domain_map:
        return domain_map[domain]

    # 企业域名可能使用腾讯/网易/阿里企业邮
    # 尝试常见的企业邮 IMAP 服务器
    # 用户可以手动修改
    return None


# ============================================================
#  邮件解析工具
# ============================================================

def decode_header_value(value):
    """解码邮件头部字段"""
    if value is None:
        return ""
    decoded_parts = email.header.decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def parse_email_addresses(header_value):
    """解析邮件地址字段，返回 [(显示名, 邮箱地址), ...]"""
    if not header_value:
        return []
    raw_value = decode_header_value(header_value)
    results = []
    # 匹配 "Name" <email> 或 Name <email> 或 纯邮箱
    addr_pattern = r'(?:"?([^"]+)"?\s*)?<([^>]+)>|([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})'
    for match in re.finditer(addr_pattern, raw_value):
        name = match.group(1) or ""
        addr = match.group(2) or match.group(3) or ""
        if addr:
            results.append((name.strip(), addr.strip().lower()))
    return results


# ============================================================
#  IMAP 邮件读取器
# ============================================================

class FoxmailImapReader:
    """通过IMAP读取Foxmail企业邮箱"""

    def __init__(self, imap_host, email_addr, password, imap_port=993):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.email_addr = email_addr
        self.password = password
        self.conn = None

    def connect(self):
        """连接并登录IMAP服务器"""
        print(f"[信息] 正在连接 {self.imap_host}:{self.imap_port} ...")
        try:
            self.conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        except Exception as e:
            print(f"[错误] 连接失败: {e}")
            sys.exit(1)

        try:
            self.conn.login(self.email_addr, self.password)
            print("[信息] 登录成功")
        except imaplib.IMAP4.error as e:
            print(f"[错误] 登录失败: {e}")
            print("  提示: 请检查邮箱地址和密码")
            print("  Foxmail企业微信邮箱可能需要使用授权码，可在邮箱设置中开启")
            sys.exit(1)

    def disconnect(self):
        """断开连接"""
        if self.conn:
            try:
                self.conn.logout()
            except Exception:
                pass

    def list_folders(self):
        """列出所有邮件文件夹"""
        status, folders = self.conn.list()
        if status != "OK":
            return []
        result = []
        for folder in folders:
            parts = folder.decode().split(' "/" ')
            if len(parts) >= 2:
                result.append(parts[-1].strip('"'))
            elif len(parts) >= 1:
                # 尝试按空格分割取最后一段
                segs = folder.decode().split()
                if segs:
                    result.append(segs[-1].strip('"'))
        return result

    def fetch_emails_from_folder(self, folder="INBOX", search_criteria="ALL", max_emails=0):
        """
        从指定文件夹获取邮件的头部信息

        返回: list[dict] 每封邮件的发件人、收件人、主题、日期等
        """
        status, data = self.conn.select(folder, readonly=True)
        if status != "OK":
            print(f"[警告] 无法打开文件夹: {folder}")
            return []

        mail_count = int(data[0])
        print(f"[信息] 文件夹 '{folder}' 共 {mail_count} 封邮件")

        status, msg_ids = self.conn.search(None, search_criteria)
        if status != "OK" or not msg_ids[0]:
            print(f"[信息] 文件夹 '{folder}' 中无匹配邮件")
            return []

        id_list = msg_ids[0].split()
        if max_emails > 0:
            id_list = id_list[-max_emails:]

        print(f"[信息] 正在读取 {len(id_list)} 封邮件 ...")

        results = []
        total = len(id_list)

        for idx, msg_id in enumerate(id_list):
            status, msg_data = self.conn.fetch(
                msg_id,
                "(BODY.PEEK[HEADER.FIELDS (FROM TO CC BCC SUBJECT DATE MESSAGE-ID)])"
            )
            if status != "OK":
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    raw_header = response_part[1]
                    msg = email.message_from_bytes(raw_header)

                    from_raw = msg.get("From", "")
                    to_raw = msg.get("To", "")
                    cc_raw = msg.get("Cc", "")
                    bcc_raw = msg.get("Bcc", "")
                    subject = decode_header_value(msg.get("Subject", ""))
                    date_str = msg.get("Date", "")
                    msg_id_str = msg.get("Message-ID", "")

                    from_addrs = parse_email_addresses(from_raw)
                    to_addrs = parse_email_addresses(to_raw)
                    cc_addrs = parse_email_addresses(cc_raw)
                    bcc_addrs = parse_email_addresses(bcc_raw)

                    results.append({
                        "from": from_addrs,
                        "to": to_addrs,
                        "cc": cc_addrs,
                        "bcc": bcc_addrs,
                        "subject": subject,
                        "date": date_str,
                        "message_id": msg_id_str,
                        "folder": folder,
                    })

            if (idx + 1) % 100 == 0 or idx + 1 == total:
                print(f"  读取进度: {idx + 1}/{total}")

        return results

    def get_all_senders(self, folders=None, search_criteria="ALL", max_emails=0):
        """获取所有发件人列表（用于交互选择）"""
        all_senders = OrderedDict()

        if folders is None:
            folders = ["INBOX"]

        for folder in folders:
            print(f"[信息] 扫描文件夹: {folder}")
            emails = self.fetch_emails_from_folder(folder, search_criteria, max_emails)
            for mail in emails:
                for name, addr in mail["from"]:
                    if addr and addr not in all_senders:
                        all_senders[addr] = name
            time.sleep(0.1)

        return all_senders


# ============================================================
#  发件人筛选 → 收件人信息提取
# ============================================================

def filter_by_sender(emails_data, from_filter):
    """
    按发件人筛选邮件，提取收件人信息

    参数:
        emails_data: 邮件列表
        from_filter: 发件人筛选条件（字符串或列表），支持邮箱、域名、关键词

    返回:
        (matched_emails, recipient_list)
    """
    # 标准化筛选条件
    if isinstance(from_filter, str):
        filters = [f.strip().lower() for f in from_filter.split(",") if f.strip()]
    elif isinstance(from_filter, list):
        filters = [f.strip().lower() for f in from_filter if f.strip()]
    else:
        filters = []

    if not filters:
        return [], []

    def matches_filter(addr, name):
        addr_l = addr.lower()
        name_l = name.lower()
        for f in filters:
            if f in addr_l or f in name_l:
                return True
            if f.startswith("@") and addr_l.endswith(f):
                return True
        return False

    # 筛选匹配的邮件
    matched = []
    for mail in emails_data:
        if any(matches_filter(addr, name) for name, addr in mail["from"]):
            matched.append(mail)

    # 提取收件人信息
    recipients = []
    seen = set()

    for mail in matched:
        sender_str = ", ".join(f"{n} <{a}>" for n, a in mail["from"])

        # 收件人 (To)
        for name, addr in mail["to"]:
            key = (addr, mail["message_id"], "To")
            if key not in seen:
                seen.add(key)
                recipients.append(OrderedDict([
                    ("收件人邮箱", addr),
                    ("收件人姓名", name),
                    ("收件类型", "收件人(To)"),
                    ("发件人", sender_str),
                    ("邮件主题", mail["subject"]),
                    ("邮件日期", mail["date"]),
                    ("所在文件夹", mail["folder"]),
                ]))

        # 抄送 (Cc)
        for name, addr in mail["cc"]:
            key = (addr, mail["message_id"], "Cc")
            if key not in seen:
                seen.add(key)
                recipients.append(OrderedDict([
                    ("收件人邮箱", addr),
                    ("收件人姓名", name),
                    ("收件类型", "抄送(Cc)"),
                    ("发件人", sender_str),
                    ("邮件主题", mail["subject"]),
                    ("邮件日期", mail["date"]),
                    ("所在文件夹", mail["folder"]),
                ]))

        # 密送 (Bcc)
        for name, addr in mail["bcc"]:
            key = (addr, mail["message_id"], "Bcc")
            if key not in seen:
                seen.add(key)
                recipients.append(OrderedDict([
                    ("收件人邮箱", addr),
                    ("收件人姓名", name),
                    ("收件类型", "密送(Bcc)"),
                    ("发件人", sender_str),
                    ("邮件主题", mail["subject"]),
                    ("邮件日期", mail["date"]),
                    ("所在文件夹", mail["folder"]),
                ]))

    return matched, recipients


def get_unique_recipients(recipient_list):
    """从收件人列表中提取去重的收件人"""
    unique = OrderedDict()
    for r in recipient_list:
        addr = r["收件人邮箱"]
        if addr not in unique:
            unique[addr] = OrderedDict([
                ("收件人邮箱", addr),
                ("收件人姓名", r["收件人姓名"]),
                ("出现次数", 1),
                ("收件类型", r["收件类型"]),
            ])
        else:
            unique[addr]["出现次数"] += 1
            # 优先保留"收件人"类型
            if "抄送" in unique[addr]["收件类型"] and "收件人" in r["收件类型"]:
                unique[addr]["收件类型"] = r["收件类型"]
    return list(unique.values())


# ============================================================
#  导出
# ============================================================

def export_to_csv(data, filepath):
    if not data:
        print("[警告] 没有数据可导出")
        return
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"[信息] 已导出 CSV: {filepath} ({len(data)} 条)")


def export_to_txt(data, filepath):
    if not data:
        print("[警告] 没有数据可导出")
        return
    emails = [item["收件人邮箱"] for item in data if item.get("收件人邮箱")]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(emails))
    print(f"[信息] 已导出邮箱列表: {filepath} ({len(emails)} 个)")


# ============================================================
#  配置文件
# ============================================================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config_template():
    template = {
        "imap_host": "imap.exmail.qq.com",
        "email": "your@company.com",
        "password": "邮箱密码或授权码",
        "folders": ["INBOX"],
        "from_filter": "@partner.com"
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    print(f"[信息] 已生成配置模板: {CONFIG_FILE}")


# ============================================================
#  交互模式
# ============================================================

def interactive_mode():
    print()
    print("=" * 62)
    print("    Foxmail 企业微信邮箱 - 按发件人筛选收件人信息")
    print("=" * 62)
    print()

    # ---- 自动检测 Foxmail ----
    foxmail_path = find_foxmail_install()
    foxmail_accounts = []
    detected_imap = None
    detected_email = None

    if foxmail_path:
        print(f"[检测] 发现 Foxmail 安装: {foxmail_path}")
        foxmail_accounts = detect_foxmail_accounts(foxmail_path)
        if foxmail_accounts:
            print(f"[检测] 发现 {len(foxmail_accounts)} 个邮箱账户:")
            for i, acc in enumerate(foxmail_accounts):
                server = get_imap_server_for_email(acc)
                server_hint = f" → {server}" if server else ""
                print(f"  {i+1}. {acc}{server_hint}")
        else:
            print("[检测] 未在 Storage 目录中发现邮箱账户")
    else:
        print("[检测] 未检测到 Foxmail 安装")

    # ---- 选择邮箱账户 ----
    if foxmail_accounts:
        print()
        print("请选择邮箱账户:")
        for i, acc in enumerate(foxmail_accounts):
            print(f"  {i+1}. {acc}")
        print(f"  0. 手动输入邮箱地址")

        acc_choice = input(f"\n请选择 (0-{len(foxmail_accounts)}): ").strip()

        if acc_choice.isdigit() and 1 <= int(acc_choice) <= len(foxmail_accounts):
            detected_email = foxmail_accounts[int(acc_choice) - 1]
            detected_imap = get_imap_server_for_email(detected_email)
            print(f"  → 已选择: {detected_email}")
            if detected_imap:
                print(f"  → 自动匹配IMAP: {detected_imap}")
        elif acc_choice == "0" or not acc_choice:
            pass  # 手动输入
        else:
            # 可能直接输入了邮箱地址
            if "@" in acc_choice:
                detected_email = acc_choice
                detected_imap = get_imap_server_for_email(detected_email)

    # ---- IMAP 服务器 ----
    if detected_imap:
        print(f"\n[自动] IMAP服务器: {detected_imap}")
        print("  按回车确认，或输入其他服务器地址修改:")
        custom_imap = input(f"  IMAP服务器 [{detected_imap}]: ").strip()
        imap_host = custom_imap if custom_imap else detected_imap
    else:
        print("\n请选择邮箱类型:")
        for k, (desc, host) in IMAP_SERVERS.items():
            print(f"  {k}. {desc} ({host})")
        print("  0. 手动输入IMAP地址")

        preset = input("\n请选择 (0-5): ").strip()
        imap_host = None
        if preset in IMAP_SERVERS:
            imap_host = IMAP_SERVERS[preset][1]
            print(f"  → {IMAP_SERVERS[preset][0]}")
        else:
            imap_host = input("请输入IMAP服务器地址: ").strip()

    if not imap_host:
        print("[错误] 未输入IMAP服务器")
        return

    # ---- 邮箱和密码 ----
    print()
    if detected_email:
        print(f"[自动] 邮箱地址: {detected_email}")
        custom_email = input(f"  邮箱地址 [{detected_email}]: ").strip()
        email_addr = custom_email if custom_email else detected_email
    else:
        email_addr = input("请输入邮箱地址: ").strip()

    password = input("请输入密码或授权码: ").strip()

    if not email_addr or not password:
        print("[错误] 邮箱和密码不能为空")
        return

    # ---- 连接 ----
    reader = FoxmailImapReader(imap_host, email_addr, password)

    try:
        reader.connect()
    except SystemExit:
        return

    try:
        # ---- 选择文件夹 ----
        print()
        print("[信息] 正在获取邮件文件夹列表...")
        folders = reader.list_folders()
        print(f"\n可用文件夹:")
        for i, f in enumerate(folders):
            cn_name = FOLDER_NAME_MAP.get(f, "")
            display = f"{f} ({cn_name})" if cn_name else f
            print(f"  {i+1}. {display}")
        print(f"  0. 自定义输入")

        folder_input = input(f"\n选择文件夹 (多选用逗号分隔，默认1=收件箱): ").strip()

        if not folder_input:
            selected_folders = ["INBOX"]
        elif folder_input == "0":
            custom = input("请输入文件夹名称: ").strip()
            selected_folders = [custom] if custom else ["INBOX"]
        else:
            selected_folders = []
            for part in folder_input.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(folders):
                        selected_folders.append(folders[idx])
                else:
                    selected_folders.append(part)
            if not selected_folders:
                selected_folders = ["INBOX"]

        print(f"  → 已选文件夹: {', '.join(selected_folders)}")

        # ---- 发件人筛选条件 ----
        print()
        print("发件人筛选条件:")
        print("  支持格式:")
        print("    - 完整邮箱: boss@company.com")
        print("    - 域名: @company.com (匹配该域名下所有发件人)")
        print("    - 关键词: 张三 (匹配发件人姓名包含该词的)")
        print("    - 多个条件用逗号分隔: @a.com,@b.com")

        from_filter = input("\n请输入发件人筛选条件: ").strip()
        if not from_filter:
            print("[错误] 必须输入发件人筛选条件")
            return

        # ---- 读取邮件 ----
        print()
        all_emails = []
        for folder in selected_folders:
            emails = reader.fetch_emails_from_folder(folder)
            all_emails.extend(emails)
            time.sleep(0.1)

        print(f"\n[信息] 共读取 {len(all_emails)} 封邮件")

        if not all_emails:
            print("[信息] 没有读取到邮件")
            return

        # ---- 筛选 ----
        matched, recipients = filter_by_sender(all_emails, from_filter)

        print(f"[信息] 匹配发件人条件的邮件: {len(matched)} 封")
        print(f"[信息] 提取到收件人记录: {len(recipients)} 条")

        if not recipients:
            print("[信息] 未找到匹配的收件人")
            return

        # 去重收件人
        unique_recipients = get_unique_recipients(recipients)
        print(f"[信息] 去重后收件人: {len(unique_recipients)} 个")

        # ---- 显示结果 ----
        print()
        print("-" * 62)
        print(f"  发件人筛选: {from_filter}")
        print(f"  匹配邮件数: {len(matched)} 封")
        print(f"  收件人总数: {len(unique_recipients)} 个 (去重)")
        print("-" * 62)
        print()

        # 显示前20个收件人
        show_count = min(20, len(unique_recipients))
        print(f"收件人列表 (显示前 {show_count} 个):")
        print()
        for i, r in enumerate(unique_recipients[:show_count]):
            name_part = f" ({r['收件人姓名']})" if r["收件人姓名"] else ""
            print(f"  {i+1:3d}. {r['收件人邮箱']}{name_part}  [{r['收件类型']}]  出现{r['出现次数']}次")

        if len(unique_recipients) > show_count:
            print(f"  ... 还有 {len(unique_recipients) - show_count} 个，请查看导出文件")

        # ---- 导出 ----
        print()
        print("是否导出结果?")
        print("  1. 导出详细记录 (每封邮件的收件人信息)")
        print("  2. 导出收件人汇总 (去重列表)")
        print("  3. 两者都导出")
        print("  0. 不导出")

        export_choice = input("\n请选择 (0-3): ").strip()

        if export_choice in ("1", "2", "3"):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "foxmail_output"
            os.makedirs(output_dir, exist_ok=True)

            if export_choice in ("1", "3"):
                filepath = os.path.join(output_dir, f"收件人详细_{timestamp}.csv")
                export_to_csv(recipients, filepath)

            if export_choice in ("2", "3"):
                filepath = os.path.join(output_dir, f"收件人汇总_{timestamp}.csv")
                export_to_csv(unique_recipients, filepath)
                # 同时导出纯邮箱列表
                txt_path = os.path.join(output_dir, f"收件人邮箱列表_{timestamp}.txt")
                export_to_txt(unique_recipients, txt_path)

            print(f"\n[完成] 文件已保存到 {output_dir} 目录")

    finally:
        reader.disconnect()


# ============================================================
#  命令行模式
# ============================================================

def cli_mode():
    parser = argparse.ArgumentParser(
        description="Foxmail 企业微信邮箱 - 按发件人筛选收件人信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 按发件人域名筛选
  python foxmail_sender_filter.py --email user@company.com --password PASS --from-filter @partner.com

  # 按完整邮箱筛选
  python foxmail_sender_filter.py --email user@company.com --password PASS --from-filter boss@company.com

  # 按姓名关键词筛选
  python foxmail_sender_filter.py --email user@company.com --password PASS --from-filter 张三

  # 指定文件夹（默认INBOX）
  python foxmail_sender_filter.py --email user@company.com --password PASS --from-filter @partner.com --folders INBOX,"Sent Messages"

  # 使用IMAP预设
  python foxmail_sender_filter.py --imap-preset qq --email user@company.com --password PASS --from-filter @partner.com
        """
    )

    parser.add_argument("--imap-host", help="IMAP服务器地址")
    parser.add_argument("--imap-preset", choices=["qq", "163", "aliyun", "outlook", "gmail"],
                        help="IMAP预设: qq=腾讯企业邮, 163=网易, aliyun=阿里, outlook, gmail")
    parser.add_argument("--email", help="邮箱地址")
    parser.add_argument("--password", help="密码或授权码")
    parser.add_argument("--from-filter", help="发件人筛选条件（邮箱/域名/关键词，逗号分隔多个）")
    parser.add_argument("--folders", default="INBOX",
                        help="邮件文件夹，多选用逗号分隔 (默认: INBOX)")
    parser.add_argument("--search", default="ALL", help="IMAP搜索条件 (默认: ALL)")
    parser.add_argument("--max-emails", type=int, default=0, help="最大读取邮件数 (0=不限)")
    parser.add_argument("--output", "-o", help="输出文件路径前缀 (默认自动生成)")
    parser.add_argument("--config", default=CONFIG_FILE, help=f"配置文件 (默认: {CONFIG_FILE})")
    parser.add_argument("--init-config", action="store_true", help="生成配置文件模板")

    args = parser.parse_args()

    if args.init_config:
        save_config_template()
        return

    # 加载配置
    config = load_config()

    # IMAP 服务器
    imap_host = args.imap_host
    if not imap_host and args.imap_preset:
        preset_map = {"qq": "imap.exmail.qq.com", "163": "imap.qiye.163.com",
                      "aliyun": "imap.qiye.aliyun.com", "outlook": "outlook.office365.com",
                      "gmail": "imap.gmail.com"}
        imap_host = preset_map.get(args.imap_preset)
    if not imap_host:
        imap_host = config.get("imap_host")
    if not imap_host:
        print("[错误] 请指定IMAP服务器 (--imap-host 或 --imap-preset)")
        sys.exit(1)

    email_addr = args.email or config.get("email")
    password = args.password or config.get("password")
    from_filter = args.from_filter or config.get("from_filter")

    if not email_addr or not password:
        print("[错误] 请指定邮箱地址和密码 (--email, --password)")
        sys.exit(1)
    if not from_filter:
        print("[错误] 请指定发件人筛选条件 (--from-filter)")
        sys.exit(1)

    folders = [f.strip() for f in args.folders.split(",") if f.strip()]

    # 连接
    reader = FoxmailImapReader(imap_host, email_addr, password)
    reader.connect()

    try:
        all_emails = []
        for folder in folders:
            emails = reader.fetch_emails_from_folder(folder, args.search, args.max_emails)
            all_emails.extend(emails)
            time.sleep(0.1)

        print(f"[信息] 共读取 {len(all_emails)} 封邮件")

        matched, recipients = filter_by_sender(all_emails, from_filter)
        print(f"[信息] 匹配邮件: {len(matched)} 封，收件人记录: {len(recipients)} 条")

        if not recipients:
            print("[信息] 未找到匹配的收件人")
            return

        unique_recipients = get_unique_recipients(recipients)
        print(f"[信息] 去重后收件人: {len(unique_recipients)} 个")

        # 显示
        print()
        print(f"  发件人筛选: {from_filter}")
        print(f"  匹配邮件数: {len(matched)} 封")
        print(f"  收件人总数: {len(unique_recipients)} 个")
        print()

        for i, r in enumerate(unique_recipients[:30]):
            name_part = f" ({r['收件人姓名']})" if r["收件人姓名"] else ""
            print(f"  {i+1:3d}. {r['收件人邮箱']}{name_part}  [{r['收件类型']}]  x{r['出现次数']}")
        if len(unique_recipients) > 30:
            print(f"  ... 共 {len(unique_recipients)} 个")

        # 导出
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "foxmail_output"
        os.makedirs(output_dir, exist_ok=True)

        if args.output:
            base = args.output
        else:
            base = os.path.join(output_dir, f"收件人筛选_{timestamp}")

        export_to_csv(recipients, base + "_详细.csv")
        export_to_csv(unique_recipients, base + "_汇总.csv")
        export_to_txt(unique_recipients, base + "_邮箱列表.txt")

        print(f"\n[完成] 结果已保存到 {output_dir} 目录")

    finally:
        reader.disconnect()


# ============================================================
#  入口
# ============================================================

def main():
    if len(sys.argv) <= 1:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\n\n[信息] 用户中断操作")
        except Exception as e:
            print(f"\n[错误] 运行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print()
            input("按回车键退出...")
    else:
        cli_mode()


if __name__ == "__main__":
    main()