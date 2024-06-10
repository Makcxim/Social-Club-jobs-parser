import asyncio
from pathlib import Path

import httpx
from playwright.async_api import async_playwright, expect

from RCSParser.utils.client import ABCHTTPClient

try:
    from orjson import json

    module = "orjson"
except ImportError:
    import json

    module = "json"


def dict_to_file(data: dict, filename: Path | str):
    to_dump = json.dumps(data, indent=4)
    with open(filename, "wb" if module == "orjson" else "w") as f:
        f.write(to_dump)


def file_to_dict(filename: Path | str) -> dict:
    with open(filename, "rb" if module == "orjson" else "r") as f:
        return json.loads(f.read())


class Auth:
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"  # noqa
    """https://techblog.willshouse.com/2012/01/03/most-common-user-agents/"""

    def __init__(
            self,
            token: str = None,
            credentials: dict = None,
            auth_file: str = "auth.json",
            user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.token = token
        self.auth_file = auth_file
        self.user_agent = user_agent
        self.credentials = credentials

        self.MAX_RETRIES = 3
        self.SLEEP_TIME = 5 * 60  # 5 minutes

        self.load_auth_data()

    async def login(self):
        """Login to social club via email and password"""
        if not self.credentials:
            raise ValueError("You must specify credentials")

        email = self.credentials.get("email")
        password = self.credentials.get("password")
        debug = self.credentials.get("debug", True)  # TODO FALSE

        if not email or not password:
            raise ValueError("You must specify email and password")

        login_url = "https://signin.rockstargames.com/signin/user-form?cid=socialclub"
        async with (async_playwright() as p):

            browser = await p.chromium.launch(headless=not debug)
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()

            try:
                await page.goto(login_url)
                await page.wait_for_selector('input[name="email"]')
                btn = await page.wait_for_selector(
                    '.UI__Button-socialclub__btn, .UI__Button-socialclub__primary, .UI__Button-socialclub__medium, .loginform__submit__rf6YG')
                await page.fill('input[name="email"]', email)
                await page.fill('input[name="password"]', password)
                await btn.click()

                try:
                    await page.wait_for_selector('.loginform__submitActions__dWo_j > button', timeout=1_000)
                    await page.click('.loginform__submitActions__dWo_j > button')
                except Exception as e:
                    print(type(e), e)

                # TODO write about verification in README
                # checking for email verification
                try:
                    # await page.pause()
                    await page.wait_for_selector('.EmailVerificationForm__buttonRow__GnwKl', timeout=5_000)
                    code = input("Input your email verification code: ")
                    await page.get_by_label("Verification code").fill(code)
                    btn = page.get_by_role("button", name="Submit")
                    await btn.click()
                    await page.pause()
                except Exception as e:
                    print("Verification not required")

                # TODO write about captcha in README
                # checking for captcha
                try:
                    await page.locator('iframe[title="Verification challenge"]').first.wait_for(timeout=5_000)
                    if debug:
                        print("Captcha detected, please solve it manually or disable debug mode")
                        await page.pause()
                except TimeoutError as e:
                    print(e, "Captcha not detected")
                except Exception as e:
                    print(type(e), e)
                else:
                    if not debug:
                        raise RuntimeError("Captcha detected, please use another verification "
                                           "method or solve captcha manually in debug mode")

                # waiting for page to load
                await page.wait_for_selector('.FeedPostMessage__postCard__1uu_B, .UI__Card__card, .UI__Card__shadow',
                                             timeout=5_000)

                anton = await context.cookies()
                self.token = [i['value'] for i in anton if i["name"] == "BearerToken"][0]

                self.save_auth_data()
                self.load_auth_data()

            except Exception as e:
                print(type(e), e)
                await page.close()
            finally:
                await page.close()

    # TODO refresh access function

    async def refresh_auth_data(self, session: ABCHTTPClient):
        self.load_auth_data()
        if not self.token:
            raise ValueError("No refresh token was found to refresh auth data")

        url = 'https://socialclub.rockstargames.com/connect/refreshaccess'

        rockstar_meme = {
            "cookies": {"BearerToken": self.token},
            "data": {"accessToken": self.token}
        }

        response_data = await session.request_raw(
            url,
            method="POST",
            data=rockstar_meme["data"],
            headers=self.headers,
            cookies=rockstar_meme["cookies"])

        # TODO if token too old, than relogin
        try:
            self.token = response_data.cookies["BearerToken"].value
        except (KeyError, TypeError) as e:
            # raise KeyError(f"Failed to refresh auth data: {response_data}") from e
            # raise TypeError(f"Failed to refresh auth data. "
            #                 f"Try to delete current token.\n"
            #                 f"{response_data}") from e
            print(f"Failed to refresh auth data. "
                  f"Trying to re-login.\n"
                  f"{response_data}")
            await self.login()

        self.save_auth_data()
        self.load_auth_data()

    def load_auth_data(self):
        try:
            auth_dict = file_to_dict(self.auth_file)
        except FileNotFoundError:
            print(f"No auth file ({self.auth_file}) was found, using blank values (anonymous access mode)")
            # logger.info(f"No auth file ({self.auth_file}) was found, using blank values (anonymous access mode)")
            auth_dict = {}

        self.token = auth_dict.get("access_token")
        self.headers = {"User-Agent": self.user_agent,
                        'X-Requested-With': 'XMLHttpRequest'}
        if self.token:
            self.headers |= {"Authorization": f"Bearer {self.token}"}

    def save_auth_data(self):
        auth_data = {
            "access_token": self.token,
        }
        dict_to_file(auth_data, self.auth_file)
