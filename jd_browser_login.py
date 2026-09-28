# -*- coding: utf-8 -*-
"""京东手机网页版登录 → 自动写入青龙 JD_COOKIE

在 Windows 电脑运行（需要 Edge 浏览器）：
    pip install playwright
    setx JD_QL_URL "http://<青龙地址>:5700"
    setx JD_QL_USERNAME "<用户名>"
    setx JD_QL_PASSWORD "<密码>"
    python jd_browser_login.py

弹出的 Edge 窗口中用手机号+短信验证码登录 m.jd.com，脚本自动提取
pt_key/pt_pin、校验有效性并写入青龙环境变量 JD_COOKIE。

登录态保存在 JD_EDGE_PROFILE 目录（默认 %LOCALAPPDATA%\\JDLogin\\edge_profile），
实测 pt_key 有效期约一年；续期时通常无需重新登录，脚本几秒内自动完成。
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QL = os.environ.get("JD_QL_URL", "").rstrip("/")
QL_USER = os.environ.get("JD_QL_USERNAME", "")
QL_PASS = os.environ.get("JD_QL_PASSWORD", "")
PROFILE = os.environ.get("JD_EDGE_PROFILE") or os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
    "JDLogin", "edge_profile")

UA_M = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
UA_PC = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
ME_API = "https://me-api.jd.com/user_new/info/GetJDUserInfoUnion"


def require_config():
    missing = [k for k, v in (("JD_QL_URL", QL), ("JD_QL_USERNAME", QL_USER),
                              ("JD_QL_PASSWORD", QL_PASS)) if not v]
    if missing:
        print("[!] 缺少环境变量: " + ", ".join(missing))
        print("[!] 先在终端执行（新窗口生效）：")
        print('    setx JD_QL_URL "http://<青龙IP>:5700"')
        print('    setx JD_QL_USERNAME "<用户名>"')
        print('    setx JD_QL_PASSWORD "<密码>"')
        return False
    return True


def req(method, url, payload=None, token=None, timeout=30):
    h = {}
    data = None
    if token:
        h["Authorization"] = "Bearer " + token
    if payload is not None:
        data = json.dumps(payload).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def ql_login():
    return req("POST", QL + "/api/user/login",
               {"username": QL_USER, "password": QL_PASS})["data"]["token"]


def verify_pt(pt_key, pt_pin):
    ck = "pt_key=%s;pt_pin=%s;" % (pt_key, pt_pin)
    try:
        r = urllib.request.Request(ME_API, headers={
            "Cookie": ck, "User-Agent": UA_PC, "Accept": "application/json"})
        with urllib.request.urlopen(r, timeout=15) as resp:
            j = json.loads(resp.read())
        if str(j.get("retcode")) == "0":
            return True, "ok"
        return False, j.get("msg") or ("retcode=%s" % j.get("retcode"))
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def write_ql(ck):
    token = ql_login()
    envs = req("GET", QL + "/api/envs?searchValue=JD_COOKIE", token=token)["data"]
    env = next((e for e in envs if e.get("name") == "JD_COOKIE"), None)
    if env:
        body = {"id": env["id"], "name": "JD_COOKIE", "value": ck}
        req("PUT", QL + "/api/envs", body, token=token)
    else:
        req("POST", QL + "/api/envs", {"name": "JD_COOKIE", "value": ck},
            token=token)
    stored = req("GET", QL + "/api/envs?searchValue=JD_COOKIE",
                 token=token)["data"]
    val = next((e["value"] for e in stored if e.get("name") == "JD_COOKIE"), "")
    return val == ck


def extract_pair(cookies):
    best = {}
    for c in cookies:
        if c.get("name") in ("pt_key", "pt_pin") and "jd.com" in (c.get("domain") or ""):
            dom = c.get("domain") or ""
            rank = 0 if dom in (".jd.com", "jd.com") else 1
            key = (c["name"], rank)
            if key not in best or rank < best[key][0]:
                best[key] = (rank, c.get("value") or "")
    tk = next((v[1] for k, v in best.items() if k[0] == "pt_key"), "")
    tp = next((v[1] for k, v in best.items() if k[0] == "pt_pin"), "")
    if tp:
        tp = urllib.parse.unquote(tp)
    return (tk, tp) if tk and tp else None


def main():
    if not require_config():
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] 未安装 playwright（pip install playwright）。")
        print("[!] 本脚本需在 Windows 电脑上运行；青龙容器内没有浏览器，")
        print("[!] 请勿在青龙中运行此脚本，容器内请使用 jd_cookie_check.py。")
        return 3

    print("[*] 启动 Edge（手机视图）... 打开 https://m.jd.com")
    print("[*] profile: %s" % PROFILE)
    with sync_playwright() as p:
        try:
            ctx = p.chromium.launch_persistent_context(
                PROFILE, channel="msedge", headless=False,
                viewport={"width": 414, "height": 896}, user_agent=UA_M,
                is_mobile=True, has_touch=True, locale="zh-CN",
                device_scale_factor=3,
                args=["--disable-blink-features=AutomationControlled"])
        except Exception as e:
            print("[!] 启动 Edge 失败: %s" % e)
            print("[!] 请确认本机已安装 Microsoft Edge。")
            return 4
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto("https://m.jd.com", wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            print("[!] 打开页面:", e)

        print("[!] 如需登录，请在窗口中用手机号+短信验证码登录 m.jd.com。")
        print("[*] 脚本轮询 pt_key/pt_pin，有效则自动写入青龙。超时 15 分钟。")
        deadline = time.time() + 900
        seen = None
        while time.time() < deadline:
            if ctx.is_closed():
                print("[!] 浏览器已关闭，未拿到 cookie。")
                return 1
            pair = extract_pair(ctx.cookies())
            if pair and pair != seen:
                ok, msg = verify_pt(*pair)
                if ok:
                    if write_ql("pt_key=%s;pt_pin=%s;" % pair):
                        print("[+] 已写入青龙 JD_COOKIE 并回读确认。")
                        print("[+] pt_pin=%s  pt_key=%s..." % (pair[1], pair[0][:24]))
                        time.sleep(3)
                        ctx.close()
                        return 0
                    print("[!] 青龙写入失败，请检查 JD_QL_* 配置。")
                elif ok is False:
                    print("[!] 捕获到 cookie 但无效(%s)，请在窗口中重新登录..." % msg)
                else:
                    print("[!] 校验失败(网络): %s，重试中..." % msg)
                seen = pair
            time.sleep(2)
        print("[!] 超时未完成登录。")
        ctx.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
