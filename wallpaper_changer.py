"""
图床壁纸随机更换脚本
从配置的图床链接列表中随机选择一张图片，下载并设置为 Windows 桌面壁纸。
"""

import os
import sys
import ssl
import random
import ctypes
import tempfile
import argparse
import urllib.request
import urllib.error

# ============ 图床链接配置 ============
# 在此列表中添加你喜欢的图床图片链接
WALLPAPER_URLS = [
    #"http://139.155.134.241:8455/i/c3241f64-98b8-484a-bb8a-c7913704aa31.jpg",
    #"http://139.155.153.92:9080/i/2026/07/16/6a5878a920cd1.png"，
    #"https://139.155.153.92:9080/i/2026/07/16/6a58fda02d99b.jpg",
    #"https://www.bing.com/th?id=OHR.ShanghaiClouds_ZH-CN1234567890_1920x1080.jpg",
    "https://139.155.153.92:9080/i/2026/08/25/6a8db3b4d7293.jpg"
]
# =====================================

# Windows API 常量
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02


def download_image(url: str, save_dir: str = None) -> str | None:
    """
    从指定 URL 下载图片到本地临时目录。

    Args:
        url: 图片的 URL 地址
        save_dir: 保存目录，默认为系统临时目录

    Returns:
        下载后的本地文件路径，失败返回 None
    """
    if save_dir is None:
        save_dir = tempfile.gettempdir()

    # 从 URL 中提取文件扩展名，默认 .jpg
    ext = ".jpg"
    for candidate in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        if candidate in url.lower():
            ext = candidate
            break

    filename = f"wallpaper_{random.randint(10000, 99999)}{ext}"
    filepath = os.path.join(save_dir, filename)

    # 创建 SSL 上下文，允许自签名证书（图床服务器可能使用自签名证书）
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    # 尝试下载：若 HTTP 返回 400 则自动重试 HTTPS
    urls_to_try = [url]
    if url.startswith("http://"):
        urls_to_try.append(url.replace("http://", "https://", 1))

    for try_url in urls_to_try:
        print(f"正在下载图片: {try_url}")
        try:
            req = urllib.request.Request(try_url, headers=headers)
            use_ctx = try_url.startswith("https://")
            opener_args = {"timeout": 30}
            if use_ctx:
                opener_args["context"] = ctx
            with urllib.request.urlopen(req, **opener_args) as response:
                data = response.read()
            with open(filepath, "wb") as f:
                f.write(data)
            print(f"图片已保存至: {filepath} ({len(data)} bytes)")
            return filepath
        except urllib.error.HTTPError as e:
            if e.code == 400 and try_url == urls_to_try[0] and len(urls_to_try) > 1:
                print(f"  HTTP 400，自动重试 HTTPS...")
                continue
            print(f"下载失败: {e}")
            return None
        except urllib.error.URLError as e:
            print(f"下载失败: {e}")
            return None

    return None


def set_wallpaper(image_path: str) -> bool:
    """
    设置 Windows 桌面壁纸。

    Args:
        image_path: 图片的本地路径

    Returns:
        是否设置成功
    """
    if not os.path.exists(image_path):
        print(f"文件不存在: {image_path}")
        return False

    abs_path = os.path.abspath(image_path)
    print(f"设置壁纸路径: {abs_path}")

    # 正确设置函数签名，确保字符串参数以宽字符传递
    # use_last_error=True 确保 ctypes.get_last_error() 能正确获取 Windows 错误码
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SystemParametersInfoW.argtypes = [
        ctypes.c_uint,       # uiAction
        ctypes.c_uint,       # uiParam
        ctypes.c_wchar_p,    # pvParam (宽字符串)
        ctypes.c_uint,       # fWinIni
    ]
    user32.SystemParametersInfoW.restype = ctypes.c_int

    result = user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        abs_path,
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )

    if result:
        print("壁纸设置成功！")
    else:
        error = ctypes.get_last_error()
        print(f"壁纸设置失败，错误码: {error}")

    return bool(result)


def load_urls_from_file(filepath: str) -> list:
    """
    从文本文件加载图床链接列表（每行一个链接）。

    Args:
        filepath: 文本文件路径

    Returns:
        URL 列表
    """
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def main():
    parser = argparse.ArgumentParser(description="图床壁纸随机更换脚本")
    parser.add_argument("-f", "--file", help="从文件加载图床链接列表（每行一个链接）")
    parser.add_argument("-u", "--url", help="直接指定单个图床链接")
    parser.add_argument("-n", "--no-change", action="store_true", help="仅下载不更换壁纸")
    args = parser.parse_args()

    # 确定可用的 URL 列表
    urls = WALLPAPER_URLS[:]

    if args.file:
        file_urls = load_urls_from_file(args.file)
        if file_urls:
            urls = file_urls
        else:
            print(f"文件 {args.file} 中未找到有效链接")
            sys.exit(1)

    if args.url:
        urls = [args.url]

    if not urls:
        print("没有可用的图床链接，请在脚本中配置 WALLPAPER_URLS 或使用 -f 参数指定链接文件")
        sys.exit(1)

    # 随机选择一个链接
    chosen_url = random.choice(urls)
    print(f"随机选中: {chosen_url}")

    # 下载图片
    image_path = download_image(chosen_url)
    if not image_path:
        sys.exit(1)

    # 设置壁纸
    if not args.no_change:
        success = set_wallpaper(image_path)
        if not success:
            sys.exit(1)
    else:
        print("已跳过壁纸设置（--no-change 模式）")

    print("完成！")


if __name__ == "__main__":
    main()