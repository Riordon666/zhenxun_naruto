import sys
import json
import asyncio
from playwright.async_api import async_playwright


KEYWORDS = [
    "火影子时", "木叶快报", "火影忍者手游", "火影手游", "丁次烤肉",
    "木叶村广播站", "子时小周报", "饰品", "火影"
]


async def main():
    user_id = sys.argv[1]
    page_url = f"https://www.douyin.com/user/{user_id}?from_tab_name=main&showTab=post"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 2200})
        await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)
        for _ in range(3):
            await page.mouse.wheel(0, 1800)
            await page.wait_for_timeout(1500)

        cards = await page.eval_on_selector_all(
            'a[href*="/note/"], a[href*="/video/"]',
            '''els => els.map((a, i) => ({
                idx: i + 1,
                href: a.href || '',
                text: (a.innerText || (a.parentElement && a.parentElement.innerText) || '').replace(/\s+/g, ' ').trim().slice(0, 300)
            }))'''
        )
        await browser.close()

    result = []
    seen = set()
    for card in cards:
        href = card.get("href") or ""
        text = card.get("text") or ""
        if not href or href in seen:
            continue
        if "source=Baiduspider" in href:
            continue
        if "/video/" not in href and "/note/" not in href:
            continue
        if not text:
            continue
        if not any(k in text for k in KEYWORDS) and "置顶" not in text:
            continue
        seen.add(href)
        result.append(card)
        if len(result) >= 12:
            break

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
