"""
火影忍者手游攻略数据源
优先使用 GetOneAPI 的抖音接口获取作品列表与详情，JustOneAPI 仅一次兜底。
"""
import json
import time
import sys
import asyncio
import httpx
import aiofiles
from pathlib import Path
from typing import Optional, Dict, List

from zhenxun.services.log import logger
from zhenxun.configs.path_config import TEMP_PATH

from .config import (
    GETONEAPI_BASE,
    GETONEAPI_TOKEN,
    JUSTONEAPI_BASES,
    JUSTONEAPI_TOKEN,
    MUYE_NEWS_TEXT,
    ACCESSORY_SIMULATOR_TEXT,
    AUTHORS,
    AUTHOR_ALIASES,
    HTTP_TIMEOUT,
)


class NarutoService:
    """火影攻略服务类"""

    GETONEAPI_BASE = GETONEAPI_BASE
    GETONEAPI_TOKEN = GETONEAPI_TOKEN

    JUSTONEAPI_BASES = JUSTONEAPI_BASES
    JUSTONEAPI_TOKEN = JUSTONEAPI_TOKEN

    MUYE_NEWS_TEXT = MUYE_NEWS_TEXT
    ACCESSORY_SIMULATOR_TEXT = ACCESSORY_SIMULATOR_TEXT
    
    # 缓存目录
    CACHE_DIR = Path(TEMP_PATH) / "naruto 攻略"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 作者配置
    AUTHORS = AUTHORS

    # 作者简写
    AUTHOR_ALIASES = AUTHOR_ALIASES
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=float(HTTP_TIMEOUT),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
            }
        )
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
    
    def get_author_cache_dir(self, author_name: str) -> Path:
        """获取作者的缓存目录"""
        author_dir = self.CACHE_DIR / author_name
        author_dir.mkdir(parents=True, exist_ok=True)
        return author_dir
    
    def get_cache_info_path(self, author_name: str) -> Path:
        """获取缓存信息文件路径"""
        return self.get_author_cache_dir(author_name) / "cache_info.json"
    
    def load_cache_info(self, author_name: str) -> Optional[Dict]:
        """加载缓存信息"""
        cache_path = self.get_cache_info_path(author_name)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取缓存信息失败：{e}")
        return None
    
    def save_cache_info(self, author_name: str, info: Dict):
        """保存缓存信息"""
        cache_path = self.get_cache_info_path(author_name)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {author_name} 的缓存信息")
        except Exception as e:
            logger.error(f"保存缓存信息失败：{e}")
    
    def clean_old_cache(self, author_name: str, keep_files: List[str]):
        """清理旧的缓存文件，只保留指定的文件"""
        cache_dir = self.get_author_cache_dir(author_name)
        try:
            for file in cache_dir.iterdir():
                if file.name != "cache_info.json" and file.name not in keep_files:
                    file.unlink()
                    logger.debug(f"清理旧缓存文件：{file.name}")
        except Exception as e:
            logger.error(f"清理缓存文件失败：{e}")
    
    async def get_douyin_user_videos(self, user_id: str) -> Optional[List[Dict]]:
        """获取抖音用户作品列表（主走 GetOneAPI，JustOneAPI 仅一次兜底）"""
        try:
            logger.info(f"获取抖音用户作品：{user_id}")
            videos = await self._fetch_douyin_getoneapi(user_id)
            if not videos:
                logger.warning("GetOneAPI 获取失败，尝试 JustOneAPI 单次兜底")
                videos = await self._fetch_douyin_justoneapi_v1(user_id)
            if videos:
                logger.info(f"成功获取 {len(videos)} 个作品")
                return videos
            logger.warning("未获取到真实作品，返回 None")
            return None
        except Exception as e:
            logger.error(f"获取抖音作品失败：{e}")
            return None

    async def _fetch_douyin_getoneapi(self, user_id: str) -> Optional[List[Dict]]:
        """使用 GetOneAPI 获取用户主页视频列表，再用详情接口补全。"""
        try:
            headers = {
                "Authorization": f"Bearer {self.GETONEAPI_TOKEN}",
                "Content-Type": "application/json",
            }
            resp = await self.client.post(
                f"{self.GETONEAPI_BASE}/api/douyin/fetch_user_video_list",
                headers=headers,
                json={
                    "sec_user_id": user_id,
                    "cursor": 0,
                    "count": 4,
                },
                timeout=60.0,
            )
            data = resp.json()
            if resp.status_code != 200 or data.get("code") != 200:
                logger.warning(f"GetOneAPI 列表返回异常: status={resp.status_code} body={data}")
                return None

            aweme_list = (data.get("data") or {}).get("aweme_list") or []
            if not aweme_list:
                logger.warning("GetOneAPI 未返回 aweme_list")
                return None

            candidate_awemes = [aweme for aweme in aweme_list[:4] if aweme.get("aweme_id")]

            videos: List[Dict] = []
            for idx, aweme in enumerate(candidate_awemes, start=1):
                normalized = self._normalize_aweme_detail(aweme)
                if not normalized:
                    continue
                logger.info(
                    f"作品候选[{idx}]: id={normalized.get('video_id')} create_time={normalized.get('create_time')} type={normalized.get('type')} is_top={normalized.get('is_top', 0)} desc={(normalized.get('desc') or '')[:30]}"
                )
                videos.append(normalized)

            if not videos:
                return None
            non_top_videos = [item for item in videos if not item.get("is_top")]
            if non_top_videos:
                videos = non_top_videos
            videos.sort(key=lambda x: (int(x.get("create_time", 0)), str(x.get("video_id", ""))), reverse=True)
            logger.info(
                "按 create_time 排序后前3条: " + " | ".join(
                    [f"id={item.get('video_id')} time={item.get('create_time')} type={item.get('type')}" for item in videos[:3]]
                )
            )
            return videos
        except Exception as e:
            logger.error(f"_fetch_douyin_getoneapi 失败：{e}")
            return None

    async def _fetch_douyin_getoneapi_detail(self, video_id: str) -> Optional[Dict]:
        """使用 GetOneAPI 获取单条作品详情。"""
        try:
            headers = {
                "Authorization": f"Bearer {self.GETONEAPI_TOKEN}",
                "Content-Type": "application/json",
            }
            resp = await self.client.post(
                f"{self.GETONEAPI_BASE}/api/douyin/fetch_video_detail",
                headers=headers,
                json={"aweme_id": video_id},
                timeout=60.0,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("code") == 200:
                detail = data.get("data") or {}
                return detail.get("aweme_detail") or detail
            logger.warning(f"GetOneAPI 详情返回异常: video_id={video_id} status={resp.status_code} body={data}")
            return None
        except Exception as e:
            logger.warning(f"GetOneAPI 详情失败 {video_id}: {e}")
            return None

    async def _fetch_douyin_page_cards(self, user_id: str) -> Optional[List[Dict]]:
        """按抖音主页作品卡片实际顺序抓取，跳过置顶，必要时再用 V2 补详情。"""
        try:
            script_path = Path(__file__).parent / "fetch_cards.py"
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                user_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
            if stderr:
                logger.warning(f"主页卡片脚本 stderr: {stderr.decode('utf-8', errors='ignore')[:500]}")
            if proc.returncode != 0:
                logger.warning(f"主页卡片脚本退出异常: code={proc.returncode}")
                return None
            raw = stdout.decode("utf-8", errors="ignore").strip()
            cards = json.loads(raw) if raw else []
            logger.info(f"主页卡片抓取数量: {len(cards)}")
            for card in cards[:5]:
                logger.info(f"主页卡片原始: idx={card.get('idx')} href={card.get('href')} text={(card.get('text') or '')[:50]}")

            if not cards:
                logger.warning("主页未抓到作品卡片")
                return None

            videos: List[Dict] = []
            for card in cards:
                href = card.get("href") or ""
                text = card.get("text") or ""
                video_id = href.rstrip("/").split("/")[-1].split("?")[0]
                if not video_id:
                    continue
                is_top = 1 if "置顶" in text else 0
                detail = await self._fetch_douyin_video_detail_v2(video_id)
                normalized = self._normalize_aweme_detail(detail)
                if not normalized:
                    normalized = {
                        "type": "image" if "/note/" in href else "video",
                        "url": "",
                        "desc": text[:120] or "无标题",
                        "create_time": 0,
                        "video_id": video_id,
                        "images": [],
                        "is_top": is_top,
                    }
                normalized["is_top"] = is_top
                logger.info(
                    f"作品候选[{card.get('idx')}]: id={normalized.get('video_id')} create_time={normalized.get('create_time')} type={normalized.get('type')} is_top={normalized.get('is_top', 0)} desc={(normalized.get('desc') or '')[:30]}"
                )
                videos.append(normalized)

            logger.info(f"主页卡片有效候选数: {len(videos)}")
            non_top_videos = [item for item in videos if not item.get("is_top")]
            if non_top_videos:
                first_non_top = non_top_videos[0]
                logger.info(
                    f"主页顺序选中首个非置顶: id={first_non_top.get('video_id')} type={first_non_top.get('type')} desc={(first_non_top.get('desc') or '')[:40]}"
                )
                return non_top_videos
            logger.warning("当前抓到的卡片全部被识别为置顶，返回原始候选")
            return videos
        except Exception as e:
            logger.error(f"_fetch_douyin_page_cards 失败：{e}")
            return None

    async def _fetch_douyin_justoneapi_v1(self, user_id: str) -> Optional[List[Dict]]:
        """使用 JustOneAPI 的 V1 列表接口获取候选，再用 V2 详情接口补全。"""
        try:
            data = None
            last_error = None
            for base in self.JUSTONEAPI_BASES:
                url = f"{base}/api/douyin/get-user-video-list/v1"
                for attempt in range(1):
                    try:
                        resp = await self.client.get(
                            url,
                            params={
                                "token": self.JUSTONEAPI_TOKEN,
                                "secUid": user_id,
                                "maxCursor": 0,
                            },
                        )
                        data = resp.json()
                        if resp.status_code == 200 and data.get("code") == 0:
                            break
                        last_error = f"base={base} attempt={attempt + 1} status={resp.status_code} body={data}"
                        logger.warning(f"JustOneAPI V1 返回异常: {last_error}")
                    except Exception as e:
                        last_error = f"base={base} attempt={attempt + 1} error={e}"
                        logger.warning(f"JustOneAPI V1 请求失败: {last_error}")
                    await asyncio.sleep(1.2 * (attempt + 1))
                if data and data.get("code") == 0:
                    break
            if not data or data.get("code") != 0:
                logger.warning(f"JustOneAPI V1 最终失败: {last_error}")
                return None

            payload = data.get("data") or {}
            aweme_list = payload.get("aweme_list") or []
            if not aweme_list:
                logger.warning("JustOneAPI V1 未返回 aweme_list")
                return None

            videos: List[Dict] = []
            for idx, aweme in enumerate(aweme_list[:8], start=1):
                video_id = str(aweme.get("aweme_id") or "")
                if not video_id:
                    continue
                detail = await self._fetch_douyin_video_detail_v2(video_id)
                normalized = self._normalize_aweme_detail(detail or aweme)
                if not normalized:
                    continue
                logger.info(
                    f"作品候选[{idx}]: id={normalized.get('video_id')} create_time={normalized.get('create_time')} type={normalized.get('type')} is_top={normalized.get('is_top', 0)} desc={(normalized.get('desc') or '')[:30]}"
                )
                videos.append(normalized)

            if not videos:
                return None

            non_top_videos = [item for item in videos if not item.get("is_top")]
            if non_top_videos:
                videos = non_top_videos
            videos.sort(key=lambda x: (int(x.get("create_time", 0)), str(x.get("video_id", ""))), reverse=True)
            return videos
        except Exception as e:
            logger.error(f"_fetch_douyin_justoneapi_v1 失败：{e}")
            return None

    async def _fetch_douyin_video_detail_v2(self, video_id: str) -> Optional[Dict]:
        """使用 JustOneAPI V2 获取单条作品详情。"""
        try:
            for base in self.JUSTONEAPI_BASES:
                url = f"{base}/api/douyin/get-video-detail/v2"
                try:
                    resp = await self.client.get(
                        url,
                        params={
                            "token": self.JUSTONEAPI_TOKEN,
                            "videoId": video_id,
                        },
                    )
                    data = resp.json()
                    if resp.status_code == 200 and data.get("code") == 0:
                        return (data.get("data") or {}).get("aweme_detail")
                    logger.warning(f"JustOneAPI V2 返回异常: base={base} video_id={video_id} status={resp.status_code} body={data}")
                except Exception as inner_e:
                    logger.warning(f"JustOneAPI V2 请求失败: base={base} video_id={video_id} error={inner_e}")
            return None
        except Exception as e:
            logger.warning(f"获取作品详情失败 {video_id}: {e}")
            return None

    def _normalize_aweme_detail(self, aweme: Dict) -> Optional[Dict]:
        """把 V1/V2 返回统一整理成插件内部结构。"""
        try:
            if not aweme:
                return None

            image_urls: List[str] = []
            for img in (aweme.get("images") or aweme.get("image_list") or []):
                if not isinstance(img, dict):
                    continue
                for key in ["url_list", "download_url_list"]:
                    url_list = img.get(key) or []
                    if url_list:
                        image_urls.append(url_list[0])
                        break
                if not image_urls:
                    display = img.get("display_image") or {}
                    url_list = display.get("url_list") or []
                    if url_list:
                        image_urls.append(url_list[0])

            if image_urls:
                return {
                    "type": "image",
                    "url": "",
                    "desc": aweme.get("desc") or aweme.get("item_title") or "无标题",
                    "create_time": int(aweme.get("create_time") or 0),
                    "video_id": str(aweme.get("aweme_id") or ""),
                    "images": image_urls,
                    "is_top": aweme.get("is_top") or aweme.get("is_pinned") or 0,
                }

            video_info = aweme.get("video") or {}
            video_url = ""
            for key in ["download_addr", "download_suffix_logo_addr", "play_addr_h264", "play_addr", "play_addr_265"]:
                addr = video_info.get(key) or {}
                for u in addr.get("url_list", []) or []:
                    if isinstance(u, str) and u.startswith("http"):
                        video_url = u
                        break
                if video_url:
                    break

            if not video_url:
                return None

            return {
                "type": "video",
                "url": video_url,
                "desc": aweme.get("desc") or aweme.get("item_title") or "无标题",
                "create_time": int(aweme.get("create_time") or 0),
                "video_id": str(aweme.get("aweme_id") or ""),
                "images": [],
                "is_top": aweme.get("is_top") or aweme.get("is_pinned") or 0,
            }
        except Exception as e:
            logger.warning(f"标准化作品失败：{e}")
            return None
    
    async def _fetch_mock_data(self, user_id: str) -> List[Dict]:
        """
        测试数据（当真实爬虫失败时使用）
        """
        logger.warning("使用测试数据")
        return [
            {
                "type": "video",
                "url": "https://www.w3school.com.cn/example/html5/mov_bbb.mp4",
                "desc": "火影忍者手游本周攻略（测试）",
                "create_time": int(time.time()),
                "video_id": "test_fixed_demo",
                "images": []
            }
        ]
    
    async def download_file(self, url: str, save_path: Path) -> bool:
        """下载文件"""
        try:
            # 如果文件已存在，直接返回
            if save_path.exists():
                logger.info(f"文件已存在：{save_path.name}")
                return True
            
            async with self.client.stream("GET", url, follow_redirects=True) as response:
                if response.status_code != 200:
                    logger.error(f"下载失败，状态码：{response.status_code}")
                    return False

                content_type = response.headers.get("content-type", "")
                if save_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and "image" not in content_type.lower():
                    logger.error(f"图片响应类型异常：{content_type} url={url}")
                    return False
                
                async with aiofiles.open(save_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await f.write(chunk)
                
                logger.info(f"下载成功：{save_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"下载文件失败：{e}")
            return False
    
    async def get_latest_work(self, author_name: str) -> Optional[Dict]:
        """获取作者的最新作品"""
        if author_name not in self.AUTHORS:
            logger.error(f"未知作者：{author_name}")
            return None
        
        user_id = self.AUTHORS[author_name]
        
        # 检查缓存
        cache_info = self.load_cache_info(author_name)
        
        # 获取最新作品
        videos = await self.get_douyin_user_videos(user_id)
        if not videos or len(videos) == 0:
            logger.error("未获取到作品")
            return None
        
        latest_video = videos[0]  # 获取最新作品（已按 create_time 倒序）
        detail = await self._fetch_douyin_getoneapi_detail(str(latest_video.get("video_id")))
        if detail:
            normalized_detail = self._normalize_aweme_detail(detail)
            if normalized_detail:
                normalized_detail["is_top"] = latest_video.get("is_top", 0)
                latest_video = normalized_detail
        logger.info(
            f"最新作品候选: id={latest_video.get('video_id')} create_time={latest_video.get('create_time')} type={latest_video.get('type')}"
        )
        
        # 检查是否有更新
        if cache_info and cache_info.get("latest_video_id") == latest_video.get("video_id"):
            # 使用缓存
            logger.info(f"使用缓存：{author_name} 的作品无更新")
            return {
                "type": cache_info.get("type"),
                "file_path": cache_info.get("file_path"),
                "desc": cache_info.get("desc"),
                "create_time": cache_info.get("create_time"),
                "is_cached": True
            }
        
        # 下载新作品
        logger.info(f"下载新作品：{latest_video.get('video_id')}")
        
        cache_dir = self.get_author_cache_dir(author_name)
        file_paths = []
        
        if latest_video.get("type") == "video":
            # 下载视频
            video_url = latest_video.get("url")
            file_name = f"video_{latest_video.get('video_id')}.mp4"
            save_path = cache_dir / file_name
            
            if await self.download_file(video_url, save_path):
                file_paths.append(str(save_path))
            else:
                logger.error("视频下载失败")
                return None
                
        elif latest_video.get("type") == "image":
            # 下载图片
            images = latest_video.get("images", [])
            for i, img_url in enumerate(images):
                file_name = f"image_{latest_video.get('video_id')}_{i}.jpg"
                save_path = cache_dir / file_name
                
                if await self.download_file(img_url, save_path):
                    file_paths.append(str(save_path))
                else:
                    logger.warning(f"图片下载失败：{img_url}")
        
        if not file_paths:
            logger.error("文件下载失败")
            return None
        
        # 保存缓存信息
        cache_data = {
            "latest_video_id": latest_video.get("video_id"),
            "type": latest_video.get("type"),
            "file_path": file_paths,
            "desc": latest_video.get("desc"),
            "create_time": latest_video.get("create_time"),
            "update_time": int(time.time())
        }
        self.save_cache_info(author_name, cache_data)
        
        # 清理旧缓存
        self.clean_old_cache(author_name, [Path(p).name for p in file_paths])
        
        return {
            "type": latest_video.get("type"),
            "file_path": file_paths,
            "desc": latest_video.get("desc"),
            "create_time": latest_video.get("create_time"),
            "is_cached": False
        }
