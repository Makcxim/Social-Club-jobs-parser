import json
from playwright.async_api import async_playwright
from RCSParser.config import debug, data_folder


async def pw():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not debug)
        context = await browser.new_context()
        with open(data_folder / "cookies.json", "rb") as f:
            await context.add_cookies(json.loads(f.read()))
        await context.route('**/*', lambda route: route.continue_())
        while True:
            yield context

context_gen = pw()
