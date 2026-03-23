"""
火影忍者手游每周攻略插件
从抖音获取火影忍者手游最新攻略视频/图片
"""
from datetime import datetime
from pathlib import Path
from nonebot import on_regex
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot_plugin_session import EventSession
from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import Video

from zhenxun.configs.config import BotConfig
from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils
from zhenxun.utils.platform import PlatformUtils

from .data_source import NarutoService

__plugin_meta__ = PluginMetadata(
    name="火影忍者手游攻略",
    description="获取火影忍者手游抖音博主最新作品攻略，并提供木叶快报与饰品模拟器快捷入口",
    usage="""
    火影最新攻略 作者名 - 获取指定作者最新攻略
    木叶快报 - 获取木叶快报链接
    饰品模拟器 - 获取饰品模拟器链接

    已接入作者：
    - 南宫的嘟嘟
    - 南宫诺奇
    - 火影子时（支持简写为“子时”）
    - 火影忍者萝卜（支持简写为“萝卜”）
    - 许仙火影忍者手游（支持简写为“许仙”）
    - 无氪玩家（支持简写为“无氪”）
    """.strip(),
    extra=PluginExtraData(
        author="Riordon",
        version="0.3",
    ).to_dict(),
)

# 创建服务实例
naruto_service = NarutoService()

# 匹配“火影最新攻略”命令
naruto_matcher = on_regex(r"^火影最新攻略(?:\s+(.+))?$", priority=5, block=True)

# 匹配“木叶快报”关键词
muye_matcher = on_regex(r"^木叶快报$", priority=5, block=True)

# 匹配“饰品模拟器”关键词
simulator_matcher = on_regex(r"^饰品模拟器$", priority=5, block=True)


@muye_matcher.handle()
async def handle_muye(session: EventSession):
    """处理木叶快报请求"""
    await MessageUtils.build_message(naruto_service.MUYE_NEWS_TEXT).send()
    logger.info("触发木叶快报", "木叶快报", session=session)


@simulator_matcher.handle()
async def handle_simulator(session: EventSession):
    """处理饰品模拟器请求"""
    await MessageUtils.build_message(naruto_service.ACCESSORY_SIMULATOR_TEXT).send()
    logger.info("触发饰品模拟器", "饰品模拟器", session=session)


@naruto_matcher.handle()
async def handle_naruto(bot: Bot, event: Event, session: EventSession, uninfo: Uninfo):
    """处理火影攻略请求"""
    try:
        plain_text = event.get_plaintext().strip()
        prefix = "火影最新攻略"
        author_name = plain_text[len(prefix):].strip() if plain_text.startswith(prefix) else ""

        alias_map = getattr(naruto_service, "AUTHOR_ALIASES", {})
        alias_tip = "；简写：" + "、".join([f"{k}→{v}" for k, v in alias_map.items()]) if alias_map else ""

        if not author_name:
            author_list = "、".join(naruto_service.AUTHORS.keys())
            await MessageUtils.build_message(
                f"正确格式：火影最新攻略 作者名\n目前已接入作者：{author_list}{alias_tip}"
            ).send()
            return

        author_name = alias_map.get(author_name, author_name)

        if author_name not in naruto_service.AUTHORS:
            author_list = "、".join(naruto_service.AUTHORS.keys())
            await MessageUtils.build_message(
                f"未找到作者：{author_name}\n目前已接入作者：{author_list}{alias_tip}"
            ).send()
            return

        # 1. 发送提示消息
        await MessageUtils.build_message("正在搜索最新攻略...").send()
        
        # 2. 获取指定作者的最新作品
        work = await naruto_service.get_latest_work(author_name)
        
        if not work:
            await MessageUtils.build_message("获取攻略失败，请稍后再试...").send()
            logger.warning("火影攻略获取失败", session=session)
            return
        
        # 3. 生成公共文本
        create_time = work.get("create_time", 0)
        date_str = "未知日期"
        if create_time:
            try:
                date_str = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
        
        title = work.get("desc") or "无标题"
        intro_msg = f"📺 作者：{author_name}\n📝 标题：{title}\n📅 发布日期：{date_str}"
        footer_msg = "💡 攻略来源于抖音，若有侵权请联系删除"
        
        # 4. 根据类型发送
        if work.get("type") == "video":
            # 视频作品：尝试使用聊天记录发送（Video(path=...)）
            msg_list = [[intro_msg]]
            video_path = work.get("file_path", [])[0] if work.get("file_path") else None
            if video_path:
                msg_list.append([Video(path=Path(video_path))])
                logger.info(f"发送视频攻略：{video_path}", session=session)
            else:
                msg_list.append(["视频文件获取失败..."])
            msg_list.append([footer_msg])

            if len(msg_list) > 3 and PlatformUtils.is_forward_merge_supported(uninfo):
                await MessageUtils.alc_forward_msg(
                    msg_list, event.self_id, BotConfig.self_nickname
                ).send()
            else:
                await MessageUtils.build_message(intro_msg).send()
                if video_path:
                    await MessageUtils.build_message(Video(path=Path(video_path))).send()
                else:
                    await MessageUtils.build_message("视频文件获取失败...").send()
                await MessageUtils.build_message(footer_msg).send()
        
        elif work.get("type") == "image":
            # 图文作品：继续使用聊天记录发送
            msg_list = [[intro_msg]]
            image_paths = work.get("file_path", [])
            if image_paths:
                for img_path in image_paths:
                    msg_list.append([Path(img_path)])
                logger.info(f"发送图文攻略，共{len(image_paths)}张图片", session=session)
            else:
                msg_list.append(["图片文件获取失败..."])
            msg_list.append([footer_msg])
        
            if len(msg_list) > 3 and PlatformUtils.is_forward_merge_supported(uninfo):
                await MessageUtils.alc_forward_msg(
                    msg_list, event.self_id, BotConfig.self_nickname
                ).send()
            else:
                await MessageUtils.build_message(intro_msg).send()
                for img_path in image_paths:
                    await MessageUtils.build_message(Path(img_path)).send()
                await MessageUtils.build_message(footer_msg).send()
        
        cache_status = "缓存" if work.get("is_cached") else "最新"
        logger.info(f"发送{cache_status}火影攻略：{author_name}", session=session)
        
    except Exception as e:
        logger.error(f"火影攻略插件出错：{e}", session=session)
        await MessageUtils.build_message("获取攻略失败，请稍后再试...").send()

