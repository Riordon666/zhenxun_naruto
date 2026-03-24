"""
火影攻略插件本地配置

此文件用于存放当前实例的真实 API 配置与作者配置。
"""

GETONEAPI_BASE = "https://api.getoneapi.com"
GETONEAPI_TOKEN = "在这里填写你的 Key"

JUSTONEAPI_BASES = [
    "http://47.117.133.51:30015",
    "https://api.justoneapi.com",
]
JUSTONEAPI_TOKEN = "在这里填写你的 Key"

MUYE_NEWS_TEXT = "木叶快报自动更新链接\nuv.qq.com/2MXYwaKD\n每周快报更新后链接点开查看"
ACCESSORY_SIMULATOR_TEXT = "饰品模拟器链接：\nhttp://vip.nevercannot.com/naruto/sp.php\n来源：南宫诺奇"

AUTHORS = {
    "南宫的嘟嘟": "MS4wLjABAAAAVoBbnKiN2-9t8Lz69lYklrqAL-_-t-2rJ8pyIjEDxlk",
    "南宫诺奇": "MS4wLjABAAAA8LqKXclwOw-EBMvRvEBTnw9N_ibnaenOV3JIY8u5e2Y",
    "火影子时": "MS4wLjABAAAA2ugLHsGsSNx5Be58ACWL7hNf8qiKOMi3ASea4JB18seP3-vm65TzJimuxvM_wL5n",
    "火影忍者萝卜": "MS4wLjABAAAAK0VgLWfiB1Cm7tYXFcfWPHF3CGmiCfq5YXvz8IjL-rP8WzLjbfIl0_jVMPB9k5Th",
    "许仙火影忍者手游": "MS4wLjABAAAAKmzQ6GRoQvDmS3344JpPmhG-ZQs-k4tASjmbq_iXNIszX11DRe3B_CmiBkyYEG7i",
    "无氪玩家": "MS4wLjABAAAAwrcv0FskSzKscFa1mfBanConRbqSKtk_bTcIhq3mmWs",
}

AUTHOR_ALIASES = {
    "子时": "火影子时",
    "萝卜": "火影忍者萝卜",
    "许仙": "许仙火影忍者手游",
    "无氪": "无氪玩家",
}

HTTP_TIMEOUT = 30
DEBUG = False
