import asyncio
import json
import platform
import re
from pathlib import Path
from typing import List, Dict
from urllib.parse import quote_plus

from markitdown import MarkItDown  # 把 HTML 转为 Markdown
from playwright.async_api import async_playwright, BrowserContext, Page

# 1. 更新后的搜索引擎 URL 模板
SEARCH_ENGINE_URLS = {
    "google": "https://www.google.com/search?q={query}",
    "bing": "https://www.bing.com/search?q={query}",
    "yahoo": "https://search.yahoo.com/search?p={query}",
    "duckduckgo": "https://duckduckgo.com/?q={query}",
    "startpage": "https://www.startpage.com/do/dsearch?query={query}",
    "brave": "https://search.brave.com/search?q={query}",
    "ecosia": "https://www.ecosia.org/search?q={query}",
    "qwant": "https://www.qwant.com/?q={query}",
    "yandex": "https://yandex.com/search/?text={query}",
    "baidu": "https://www.baidu.com/s?wd={query}",
    "sogou": "https://www.sogou.com/web?query={query}",
    "360": "https://www.so.com/s?q={query}",
}

# 2. 修正后的 CSS 选择器映射
ENGINE_SELECTORS = {
    "google": "h3",  # Google 搜索结果中 <h3>，通过 h3.closest('a').href 提取链接 :contentReference[oaicite:12]{index=12}
    "bing": "li.b_algo h2 > a",  # Bing SERP 中 <li class='b_algo'><h2><a> :contentReference[oaicite:13]{index=13}
    "yahoo": "h3.title > a",  # Yahoo SERP 中 <h3 class='title'><a> :contentReference[oaicite:14]{index=14}
    "duckduckgo": "a.result__a",  # DuckDuckGo <a class='result__a'> :contentReference[oaicite:15]{index=15}
    "startpage": "a.w-gl__result-title",
    # Startpage/Ixquick <a class='w-gl__result-title'> :contentReference[oaicite:16]{index=16}
    "brave": "a.result__a",
    # Brave Search 与 DuckDuckGo 类似 <a class='result__a'> :contentReference[oaicite:17]{index=17}
    "ecosia": "a.result__a",  # Ecosia SERP <a class='result__a'> :contentReference[oaicite:18]{index=18}
    "qwant": "div.result--web a",  # Qwant SERP <div class='result--web'><a> :contentReference[oaicite:19]{index=19}
    "yandex": "a.Link.Link_theme_normal",
    # Yandex SERP <a class='Link Link_theme_normal'> :contentReference[oaicite:20]{index=20}
    "baidu": "h3.t > a",  # Baidu <h3 class='t'><a> :contentReference[oaicite:21]{index=21}
    "sogou": "h3.vrTitle > a, h3.pt > a",
    # Sogou <h3 class='vrTitle'><a> 或 <h3 class='pt'><a> :contentReference[oaicite:22]{index=22}
    "360": "h3.res-title > a, div.res-intro > a",
    # 360 SERP <h3 class='res-title'><a> 或 <div class='res-intro'><a> :contentReference[oaicite:23]{index=23}
}


def get_chrome_user_profiles() -> List[Path]:
    """
    找到本地机器上 Chrome/Chromium（及 Edge）用户配置目录，返回列表 [profile_path, ...]
    如在 Windows，路径类似 %LOCALAPPDATA%/Google/Chrome/User Data/Default 及 Profile X
    """
    system = platform.system()
    candidates: List[Path] = []
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            candidates += [
                Path(local) / "Google" / "Chrome" / "User Data",
                Path(local) / "Microsoft" / "Edge" / "User Data",
            ]
    elif system == "Darwin":
        home = Path.home()
        candidates += [
            home / "Library" / "Application Support" / "Google" / "Chrome",
            home / "Library" / "Application Support" / "Microsoft Edge",
        ]
    else:
        home = Path.home()
        candidates += [
            home / ".config" / "google-chrome",
            home / ".config" / "chromium",
            home / ".config" / "microsoft-edge",
        ]

    profiles: List[Path] = []
    for base in candidates:
        if base.exists():
            for entry in base.iterdir():
                if entry.is_dir() and (entry.name == "Default" or entry.name.startswith("Profile ")):
                    profiles.append(entry)
    return profiles


async def is_blocked_by_search_engine(page: Page, engine: str) -> bool:
    """
    检测是否触发了反爬措施，例如验证码或访问受限提示
    """
    url = page.url.lower()
    title = (await page.title()).lower()
    html = (await page.content()).lower()
    rules = {
        "google": ["/sorry/", "unusual traffic", '<form action="/sorry/'],
        # Google Captcha 页面特征 :contentReference[oaicite:24]{index=24}
        "bing": ["help.bing.microsoft.com", "please verify", "automated queries"],
        # Bing 验证提示 :contentReference[oaicite:25]{index=25}
        "duckduckgo": ["ddg_blocked", "request forbidden"],
        # DuckDuckGo 可能的封禁提示 :contentReference[oaicite:26]{index=26}
        "startpage": ["403 forbidden", "access denied"],  # Startpage 403 提示 :contentReference[oaicite:27]{index=27}
        "brave": ["403 forbidden", "service unavailable"],
        # Brave Search 403 或服务不可用 :contentReference[oaicite:28]{index=28}
        "yahoo": ["please verify you are a human", "unusual traffic"],
        # Yahoo 验证提示 :contentReference[oaicite:29]{index=29}
        "baidu": ["verify.baidu.com", "百度安全验证", "无法处理"],  # Baidu 验证页面 :contentReference[oaicite:30]{index=30}
        "sogou": ["访问行为存在异常", "验证中心"],  # Sogou 验证提示 :contentReference[oaicite:31]{index=31}
        "360": ["访问过于频繁", "请开启 javascript"],  # 360 验证提示 :contentReference[oaicite:32]{index=32}
        "yandex": ["attention required", "/showcaptcha"],  # Yandex 验证 :contentReference[oaicite:33]{index=33}
        "qwant": ["403 forbidden", "access to this page has been denied"],
        # Qwant 403 :contentReference[oaicite:34]{index=34}
        "ecosia": ["access denied", "403 forbidden"],  # Ecosia 403 :contentReference[oaicite:35]{index=35}
    }
    for kw in rules.get(engine.lower(), []):
        if kw in url or kw in title or kw in html:
            return True
    return False


class SearchEngine:
    """
    生成搜索 URL 并异步提取前 max_results 条结果链接及标题
    """

    def __init__(self, engine: str, query: str, max_results: int = 5):
        self.engine = engine.lower()
        self.query = query
        self.max_results = max_results
        if self.engine not in SEARCH_ENGINE_URLS:
            raise ValueError(f"Unsupported search engine: {engine}")

    def _build_url(self) -> str:
        # 对 query 进行 URL 编码
        encoded = quote_plus(self.query)
        return SEARCH_ENGINE_URLS[self.engine].format(query=encoded)

    async def fetch_urls(self, context: BrowserContext) -> List[Dict[str, str]]:
        """
        打开一个新页面，访问搜索结果页面，检测是否封禁，并提取前 max_results 条链接和标题
        返回一个列表，列表中的每个 dict 包含 title、url 两个字段
        """
        page: Page = await context.new_page()
        try:
            await page.goto(self._build_url(), timeout=60000)
            # 检测并手动验证码
            if await is_blocked_by_search_engine(page, self.engine):
                print(f"[Warning] {self.engine} triggered anti-bot measures. Please verify manually.")
                await page.screenshot(path="blocked.png")
                input("After manual verification, press Enter to continue...")

            # 等待结果加载，至少存在一个匹配选择器
            selector = ENGINE_SELECTORS.get(self.engine)
            await page.wait_for_selector(selector, timeout=10000)

            results: List[Dict[str, str]] = []
            elements = await page.query_selector_all(selector)
            for el in elements:
                # ## 尝试获取标题文本
                title = await page.evaluate("el => el.textContent", el) or ""
                # ## 获取包含标题的最近父级 <a> 标签的 href
                href = await el.get_attribute("href")
                if not href:
                    href = await page.evaluate("el => el.closest('a')?.href", el)
                if href and href.startswith("http"):
                    results.append({"title": title.strip(), "url": href.strip()})
                if len(results) >= self.max_results:
                    break

            if not results:
                print(f"[Warning] No URLs found for {self.engine}.")
            return results
        finally:
            await page.close()


def sanitize(name: str) -> str:
    """
    Remove any character that is not a letter, number, underscore, or hyphen.
    That prevents invalid filename characters (< > : " / \\ | ? * etc.).
    """
    # Keep only ASCII letters, digits, underscore, and hyphen
    return re.sub(r'[^A-Za-z0-9_-]', '', name)


class PageArchiver:
    """
    Concurrently visit a list of URLs, save each page’s HTML,
    convert it to Markdown, and return the Markdown content.
    The output directory is always 'output' in the same folder as this script.
    """

    def __init__(self, output_dir: str = "output"):
        # Determine the directory of the current script file
        script_directory = os.path.dirname(os.path.abspath(__file__))
        # Create (or reuse) an 'output' folder next to this script
        output_directory = os.path.join(script_directory, output_dir)
        os.makedirs(output_directory, exist_ok=True)

        self.output_dir = output_directory

    async def _archive_single(
            self,
            context: BrowserContext,
            url: str,
            prefix: str,
            index: int
    ) -> str:
        """
        1. Wait for a brief delay before opening a new page to fetch the URL.
        2. Save the raw HTML to a file and convert it to Markdown.
        3. Return the Markdown content as a string.
        """
        # Stagger requests by half a second per index to limit simultaneous load
        await asyncio.sleep(index * 0.5)
        page: Page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            raw_html = await page.content()

            prefix = sanitize(prefix)

            html_filename = f"{prefix}_page_{index + 1}.html"
            md_filename = f"{prefix}_page_{index + 1}.md"

            html_path = os.path.join(self.output_dir, html_filename)
            with open(html_path, "w", encoding="utf-8") as html_file:
                html_file.write(raw_html)

            converter = MarkItDown(enable_plugins=False)
            conversion_result = converter.convert(html_path)
            markdown_text = conversion_result.text_content

            md_path = os.path.join(self.output_dir, md_filename)
            with open(md_path, "w", encoding="utf-8") as md_file:
                md_file.write(markdown_text)

            print(f"[Info] Saved Markdown: {md_path}")
            return markdown_text

        except Exception as error:
            print(f"[Error] Failed to archive {url}: {error}")
            return ""

        finally:
            await page.close()

    async def archive(
            self,
            context: BrowserContext,
            results: List[Dict[str, str]],
            prefix: str
    ) -> List[str]:
        """
        For each item in 'results', run _archive_single concurrently.
        Collect and return a list of Markdown contents.
        """
        tasks = [
            self._archive_single(context, item["url"], prefix, idx)
            for idx, item in enumerate(results)
        ]
        return await asyncio.gather(*tasks)


async def search_local(
        keywords: str,
        engine: str = "google",
        max_results: int = 5
) -> List[Dict[str, str]]:
    """
    核心函数：根据 keywords、engine、max_results，并返回一个 List[Dict[str, str]]，
    每个 dict 包含 title、url、content（Markdown 文本），符合预定义的 Outputs 格式
    """
    # 1. 获取本地 Chrome/Edge 用户配置文件
    profiles = get_chrome_user_profiles()
    if not profiles:
        raise RuntimeError("No Chrome/Edge user profiles found.")
    profile_path = profiles[0]  # 默认使用第一个找到的 profile

    # 2. 启动 Playwright，并创建持久化上下文
    async with async_playwright() as p:
        context: BrowserContext = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # 3. 添加一些反自动化检测的脚本
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        """)

        # 4. 实例化 SearchEngine 并获取前 max_results 条结果
        searcher = SearchEngine(engine, keywords, max_results)
        search_results = await searcher.fetch_urls(context)

        # 5. 并发访问每个结果链接，将页面转换为 Markdown 文本
        archiver = PageArchiver(output_dir="output")
        contents = await archiver.archive(context, search_results, prefix=keywords.replace(" ", "_") + f"_{engine}")

        # 6. 组装最终输出，包含 title、url、content
        outputs: List[Dict[str, str]] = []
        for item, content_md in zip(search_results, contents):
            outputs.append({
                "title": item["title"],
                "url": item["url"],
                "content": content_md
            })

        await context.close()
        return outputs


import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.Service import Service
from core.Context import Context


class LocalWebSearchService(Service):
    """
    本地搜索服务，继承自 Service 类
    实现核心的 search_local 方法，供外部调用
    """

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config = json.loads(open(config_path).read())
        super().__init__(config["service_id"])

    def initialize(self):
        pass

    def compute(self, keywords, engine="google", max_results=5):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(search_local(keywords, engine, max_results))


# 示例调用
if __name__ == "__main__":
    with Context():
        service = LocalWebSearchService()
        service.run()
