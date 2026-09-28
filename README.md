# qinglong-JDLogin

京东 Cookie（`pt_key`/`pt_pin`）获取与维护方案：**手机网页版短信验证码登录**，自动写入青龙面板。

> 背景：2026 年起 PC 扫码登录（passport.jd.com 的 appid=133 流程）完成换票后
> 只下发 pin/thor 等会话 cookie，**不再签发 `pt_key`**，无法用于脚本；
> 而手机版网页（m.jd.com）短信验证码登录仍会签发 `pt_key`，实测有效期约 365 天。

## 文件说明

| 文件 | 运行位置 | 作用 |
|---|---|---|
| `jd_browser_login.py` | Windows 电脑（需 Edge） | 弹出 Edge 手机视图打开 m.jd.com，手机号登录后自动提取 pt_key/pt_pin、校验并写入青龙 `JD_COOKIE` |
| `jd_cookie_check.py` | 青龙面板 | 每日校验 `JD_COOKIE` 有效性（me-api），失效时日志输出告警与续期方法 |

## 使用步骤

### 1. 订阅到青龙

青龙面板 → 系统设置 → **订阅管理** → 新建订阅：

- 订阅地址：`https://github.com/908468180/qinglong-JDLogin`
- 分支：`main`

拉取后脚本目录中会出现上述两个文件。

### 2. 定时任务（拉取时自动创建）

开启「自动添加定时任务」时，首次拉取会自动创建两个任务：

| 任务 | 命令 | 处理方式 |
|---|---|---|
| `jd_cookie_check.py` | `task 908468180_qinglong-JDLogin_main/jd_cookie_check.py` | **保留**，默认每天 06:06 检查 |
| `jd_browser_login.py` | `task 908468180_qinglong-JDLogin_main/jd_browser_login.py` | **停用**（青龙容器无浏览器，只能在电脑上运行；保留任务可防止下次拉取被重复添加） |

如未自动创建，也可手动新建：命令 `task 908468180_qinglong-JDLogin_main/jd_cookie_check.py`，
定时规则 `0 0 9 * * *`（每天 9:00）。

### 3. 电脑端登录（获取 / 续期 Cookie）

青龙容器无图形界面，登录脚本需在 Windows 电脑上运行（先从本仓库下载
`jd_browser_login.py`）：

```powershell
pip install playwright

# 配置青龙地址与账号（一次设置，长期有效；新开的终端窗口生效）
setx JD_QL_URL "http://<青龙IP>:5700"
setx JD_QL_USERNAME "<用户名>"
setx JD_QL_PASSWORD "<密码>"
# 可选：Edge 登录态目录，默认 %LOCALAPPDATA%\JDLogin\edge_profile
setx JD_EDGE_PROFILE "<profile目录>"

python jd_browser_login.py
```

弹出的 Edge 窗口中用 **手机号 + 短信验证码** 登录，脚本会：

1. 轮询浏览器 cookie，捕获 `pt_key`/`pt_pin`
2. 通过 me-api 校验有效性
3. 写入青龙环境变量 `JD_COOKIE` 并回读确认

登录态保存在 profile 目录中，续期时通常无需再次登录，脚本几秒内自动完成；
只有 cookie 失效时窗口才会停留等待你重新登录（最长 15 分钟）。

## 注意事项

- `pt_key` 等同账号密码，**不要公开分享**；本仓库不含任何账号凭据，
  全部通过本机环境变量注入。
- 多账号：青龙 `JD_COOKIE` 中多段以 `&` 分隔，`jd_cookie_check.py` 会逐个检查。
- 换电脑：只需拷贝脚本并 `pip install playwright`（电脑需装有 Edge、能访问青龙），
  新电脑首次运行时登录一次即可。
