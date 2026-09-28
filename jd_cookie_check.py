# -*- coding: utf-8 -*-
"""青龙定时检查京东 JD_COOKIE 有效性（纯标准库）

在青龙中新建定时任务：
    名称: 京东Cookie检查
    命令: task jd_cookie_check.py
    定时: 0 0 9 * * *   （每天 9:00）

支持单账号或多账号（JD_COOKIE 中多段以 & 或换行分隔）。
失效时日志输出 [失效] 提示，续期：电脑上运行 jd_browser_login.py
重新用手机号+短信验证码登录即可。
"""
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA_PC = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
ME_API = "https://me-api.jd.com/user_new/info/GetJDUserInfoUnion"


def check(pt_key, pt_pin):
    ck = "pt_key=%s;pt_pin=%s;" % (pt_key, pt_pin)
    req = urllib.request.Request(ME_API, headers={
        "Cookie": ck, "User-Agent": UA_PC, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            j = json.loads(resp.read())
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)
    if str(j.get("retcode")) == "0":
        return True, "ok"
    return False, j.get("msg") or ("retcode=%s" % j.get("retcode"))


def main():
    print("[JD-Cookie检查] %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    raw = os.environ.get("JD_COOKIE", "").strip()
    if not raw:
        print("[!] 未找到环境变量 JD_COOKIE")
        return
    accounts = [p for p in re.split(r"[&\n]", raw) if "pt_key" in p]
    if not accounts:
        print("[!] JD_COOKIE 中未找到 pt_key")
        return
    bad = 0
    for i, acc in enumerate(accounts, 1):
        mk = re.search(r"pt_key=([^;\s]+)", acc)
        mp = re.search(r"pt_pin=([^;\s]+)", acc)
        if not mk or not mp:
            print("[?] 第%d段缺少 pt_key 或 pt_pin" % i)
            bad += 1
            continue
        pin = urllib.parse.unquote(mp.group(1))
        ok, msg = check(mk.group(1), mp.group(1))
        if ok is True:
            print("[OK ] pt_pin=%s" % pin)
        elif ok is False:
            bad += 1
            print("[失效] pt_pin=%s (%s)" % (pin, msg))
        else:
            print("[?] pt_pin=%s 检查失败(网络): %s" % (pin, msg))
    if bad:
        print("[!] 有 %d 个账号需要处理：在电脑上运行 jd_browser_login.py，"
              "用手机号+短信验证码重新登录即可更新 JD_COOKIE。" % bad)


if __name__ == "__main__":
    main()
