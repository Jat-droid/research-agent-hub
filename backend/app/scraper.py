import sys
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def scrape_url_content(url: str) -> str:
    """
    Scrapes a URL using a headless Chromium browser.
    Uses an isolated Proactor event loop to completely bypass Windows/Uvicorn conflicts.
    Memory-optimized for Free Tier Cloud Deployments.
    """
    
    # 1. Force the correct Windows policy for this specific isolated thread
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    # 2. Create a brand new, quarantined event loop just for Playwright
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 3. Define the actual async scraping logic
    async def _do_scrape():
        try:
            async with async_playwright() as p:
                # UPDATED: Cloud-ready memory optimization arguments injected here
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-gpu", 
                        "--no-sandbox", 
                        "--disable-dev-shm-usage",
                        "--disable-setuid-sandbox",
                        "--single-process" 
                    ]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000) # Hydration pause
                
                html = await page.content()
                await browser.close()
                return html
        except Exception as e:
            return f"Content could not be retrieved. Error: {str(e)}"
            
    # 4. Execute the scrape inside our quarantined loop, then shut the loop down
    html_content = loop.run_until_complete(_do_scrape())
    loop.close()
    
    # 5. Clean the raw HTML into pure text with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    for junk in soup(["script", "style", "nav", "footer", "aside", "header", "noscript"]):
        junk.decompose()
        
    text = soup.get_text(separator="\n", strip=True)
    
    return text[:10000]