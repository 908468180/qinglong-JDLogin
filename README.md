# qinglong-JDLogin

京东 Cookie（`pt_key`/`pt_pin`）获取方案：**手机网页版短信验证码登录**，运行即弹出登录窗口，登录后自动写入青龙面板。

> 背景：2026 年起 PC 扫码登录（passport.jd.com 的 appid=133 流程）完成换票后
> 只下发 pin/thor 等会话 cookie，**不再签发 `pt_key`**；手机版网页（m.jd.com）
> 短信验证码登录仍会签发 `pt_key`，实测有效期约 365 天。

## 文件说明

| 文件 | 运行位置 | 作用 |
|---|---|---|
| `jd_browser_login.py` | Windows 电脑（需 Edge） | 运行即弹出 Edge 手机视图登录页，手机号+短信验证码登录后自动提取 pt_key/pt_pin 写入青龙 `JD_COOKIE` |

## 使用步骤

### 1. 订阅到青龙

青龙面板 → 系统设置 → **订阅管理** → 新建订阅：

- 订阅地址：`https://github.com/908468180/qinglong-JDLogin`
- 分支：`main`

拉取后脚本目录中会出现 `jd_browser_login.py`。
注意：该脚本是**电脑端工具**，青龙容器内没有浏览器无法运行（如自动创建了
对应定时任务，请停用或删除）；cookie 失效时由青龙里的京东脚本库自行提示。

### 2. 电脑端登录（获取 / 续期 Cookie）

先从本仓库下载 `jd_browser_login.py` 到电脑：

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

运行即弹出 Edge 窗口（m.jd.com 登录页）：

1. 点击「登录」（脚本会自动尝试点击）
2. 手机号 + 短信验证码登录
3. 脚本自动捕获 `pt_key`/`pt_pin` → 写入青龙环境变量 `JD_COOKIE` 并回读确认

每次运行都会清除旧登录态重新登录，无需任何"检测"——登录成功即写入。

## 注意事项

- `pt_key` 等同账号密码，**不要公开分享**；本仓库不含任何账号凭据，
  全部通过本机环境变量注入。
- 多账号：在电脑上重复运行，脚本会用最后一次登录覆盖 `JD_COOKIE`；
  多段账号可在青龙中自行以 `&` 分隔拼接。
- 换电脑：拷贝脚本 + `pip install playwright`（需装有 Edge、能访问青龙）。
