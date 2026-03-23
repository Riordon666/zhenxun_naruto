<div align="center">

# Zhenxun-Naruto-Plugin

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Zhenxun%20Bot-orange)
![License](https://img.shields.io/badge/License-MIT-green)

一个用于QQ群 **火影忍者手游** 攻略查询的 [真寻 Bot](https://github.com/zhenxun-org/zhenxun_bot) 插件。

</div>

## 当前功能

- 获取指定抖音博主最新攻略
- 支持视频与图文作品发送
- 自动缓存资源
- 提供木叶快报快捷入口
- 提供饰品模拟器快捷入口

---

## 功能介绍

### 1. 最新攻略

插件会根据你配置好的作者列表，获取对应抖音博主的最新作品，并发送到聊天中。

支持：
- 视频作品
- 图文作品
- 作者简写
- 本地缓存

### 2. 木叶快报

提供固定链接快捷发送。来源：叶子官方链接。

### 3. 饰品模拟器

提供固定链接快捷发送。来源：南宫诺奇。

---

## 安装教程

### Linux

1. 将 `naruto` 文件夹放入真寻 Bot 插件目录
2. 安装依赖
3. 修改 `naruto/config.py`
4. 重启真寻 Bot

示例：

```bash
pip install -r naruto/requirements.txt
```

如果你使用 systemd，可以这样重启：

```bash
systemctl restart zhenxun
```

如果你使用其他方式启动真寻 Bot，请按自己的环境处理。

### Windows

1. 将 `naruto` 文件夹放入真寻 Bot 插件目录
2. 打开终端进入项目目录
3. 安装依赖
4. 修改 `naruto/config.py`
5. 重启真寻 Bot

示例：

```powershell
pip install -r naruto\requirements.txt
```

如果你是面板、bat、PowerShell 或 IDE 启动，请按自己的方式重启。

---

## 指令

### 1. 获取最新攻略

```text
火影最新攻略 作者名
```

示例：

```text
火影最新攻略 火影子时
火影最新攻略 子时
火影最新攻略 萝卜
火影最新攻略 许仙
火影最新攻略 无氪
```

### 2. 木叶快报

```text
木叶快报
```

### 3. 饰品模拟器

```text
饰品模拟器
```

---

## 当前已接入作者

<div align="center">

| 博主 | 平台 | 简写 |
| :--: | :--: | :--: |
| 南宫的嘟嘟 | 抖音 | 南宫的嘟嘟 |
| 南宫诺奇 | 抖音 | 南宫诺奇 |
| 火影子时 | 抖音 | 子时 |
| 火影忍者萝卜 | 抖音 | 萝卜 |
| 许仙火影忍者手游 | 抖音 | 许仙 |
| 无氪玩家 | 抖音 | 无氪 |

</div>

---

## 项目结构

```text
naruto/
├─ __init__.py
├─ data_source.py
├─ config.py
├─ requirements.txt
├─ README.md
└─ fetch_cards.py
```

> 当前默认使用 API 方案，`fetch_cards.py` 可按需忽略。

---

## API 说明

本插件当前使用两组第三方 API。GetOneAPI 首选，当出故障时转为 JustOneAPI 兜底。

### 1.GetOneAPI

用途：
- 获取用户作品列表
- 获取单条作品详情

代码位置：

```text
naruto/data_source.py
naruto/config.py
```

配置项：

```python
GETONEAPI_BASE = "https://api.getoneapi.com"
GETONEAPI_TOKEN = "在这里填写你的 Key"
```

接口路径：

```text
/api/douyin/fetch_user_video_list
/api/douyin/fetch_video_detail
```

### 2.JustOneAPI

用途：
- 用户作品列表兜底
- 作品详情兜底

代码位置：

```text
naruto/data_source.py
naruto/config.py
```

配置项：

```python
JUSTONEAPI_BASES = [
  "https://your-api-host.example.com",
  "https://api.justoneapi.com"
]
JUSTONEAPI_TOKEN = "在这里填写你的 Key"
```

接口路径：

```text
/api/douyin/get-user-video-list/v1
/api/douyin/get-video-detail/v2
```

### 3.如何获取 API KEY？

GetOneAPI 与 JustOneAPI 为付费 API，具体价格与试用策略请自行前往官方查看。

```text
直达注册页面
GetOneAPI 官网：https://api.getoneapi.com/register
JustOneAPI 官网：https://dashboard.justoneapi.com/zh/register
```

>注册时是使用邮箱注册，然后API提供商会将key直接发送至邮箱，每个新用户都有免费试用的次数

>如果你用完次数，可以联系我（可以提供无限次数的方法）,QQ:`2717831140`(备注来意)

---

## 如何新增作者

编辑：

```text
naruto/config.py
```

找到：

```python
AUTHORS = {
  "作者名": "抖音 sec_user_id"
}
```

### 抖音 sec_user_id 如何获取？

```text
找到目标博主主页链接，其中 user/ 之后的部分即为 id。
例如：
南宫诺奇主页链接为：
https://www.douyin.com/user/MS4wLjABAAAA8LqKXclwOw-EBMvRvEBTnw9N_ibnaenOV3JIY8u5e2Y?from_tab_name=main
则其 id 为：
MS4wLjABAAAA8LqKXclwOw-EBMvRvEBTnw9N_ibnaenOV3JIY8u5e2Y
```

如果要支持简写，再修改：

```python
AUTHOR_ALIASES = {
  "简写": "完整作者名"
}
```

示例：

```python
AUTHORS = {
  "火影子时": "MS4wLjABAAAAxxxxxx",
  "新作者": "MS4wLjABAAAAyyyyyy",
}

AUTHOR_ALIASES = {
  "子时": "火影子时",
  "简写": "新作者",
}
```

---

## 缓存说明

插件会自动缓存下载后的资源，避免重复下载。

缓存内容通常包括：
- 视频文件
- 图文图片文件
- `cache_info.json`

缓存路径由运行环境决定，因此 README 中不写死系统绝对路径。

---

## 使用示例

<details>
<summary>点击展开查看图片</summary>
<br>
<img width="45%" src="https://github.com/user-attachments/assets/afdb4a75-5795-4ee6-afae-3bd945a95703"/>
<img width="45%" src="https://github.com/user-attachments/assets/7d1e9561-b0c7-45d2-a277-48e198277212"/>
</details>

---
## 更新日志

### 2026/03/23 v0.3
- 新增木叶快报快捷入口
- 新增饰品模拟器快捷入口
- 支持通过 `config.py` 统一管理 API 配置与作者配置

### 2026/03/18 v0.2
- 新增作者：`火影忍者萝卜`、`许仙火影忍者手游`、`无氪玩家`
- 支持作者简写：`子时`、`萝卜`、`许仙`、`无氪`
- 作品介绍展示顺序调整为：作者、标题、发布日期

### 2026/03/15 v0.1
- 初始版本
- 首批支持作者：`火影子时`、`南宫的嘟嘟`、`南宫诺奇`
- 支持获取抖音博主最新攻略
- 支持视频与图文作品发送
- 支持本地缓存

---

## 关于
如果你喜欢这个插件项目，记得点个star，所有攻略来自于网络，若有侵权，请联系我删除

如果你有任何问题、想法或改进建议，欢迎提交 [Issue](https://github.com/Riordon666/zhenxun_naruto/issues) 或直接发起 [Pull Request](https://github.com/Riordon666/zhenxun_naruto/pulls)。我非常乐意听到你的声音！

### 联系我
QQ：2717831140（备注来意）

### 开源协议
本项目使用MIT作为开源协议

