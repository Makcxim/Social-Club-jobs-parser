from playwright.async_api import async_playwright
from config import data_folder, debug, email, password
from urllib.parse import parse_qs
from typing import Optional
from fake_useragent import UserAgent
import httpx
import json


def create_directories_if_not_exist():
    data_folder.mkdir(parents=True, exist_ok=True)

    files = [file.name for file in data_folder.iterdir() if file.is_file()]

    if "cookies.json" not in files:
        with open(data_folder / "cookies.json", "w") as f:
            f.write("[]")


create_directories_if_not_exist()
ua = UserAgent()


async def logining(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not debug)
        context = await browser.new_context(user_agent=ua.random)
        page = await context.new_page()
        try:
            await page.goto(url)
            await page.wait_for_selector('input[name="email"]')
            btn = await page.wait_for_selector(
                '.UI__Button-socialclub__btn, .UI__Button-socialclub__primary, .UI__Button-socialclub__medium, .loginform__submit__rf6YG')
            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await btn.click()

            try:
                await page.wait_for_selector('.loginform__submitActions__dWo_j > button', timeout=500000)
                await page.click('.loginform__submitActions__dWo_j > button')
            except Exception as e:
                print(type(e), e)

            # TODO write about captcha in README
            try:
                await page.wait_for_selector('.EmailVerificationForm__buttonRow__GnwKl', timeout=3000)
                code = input("Input your email verification code: ")
                await page.get_by_label("Verification code").fill(code)
                btn = page.get_by_role("button", name="Submit")
                await btn.click()
            except Exception as e:
                print("Verification not required")

            await page.pause()

            await page.wait_for_selector('.FeedPostMessage__postCard__1uu_B, .UI__Card__card, .UI__Card__shadow',
                                         timeout=5000)

            print("TEST")
            with open(data_folder / "cookies.json", "w") as f:
                print("govno")
                f.write(json.dumps(await context.cookies(), indent=4))

        except Exception as e:
            print(type(e), e)
            await page.close()
        finally:
            await page.close()


async def get_user_info(headers: dict, nickname: str = "Makcxim", max_friends: int = 3, first_try: bool = True):
    print(123)
    url = f"https://scapi.rockstargames.com/profile/getprofile?nickname={nickname}&maxFriends={max_friends}"
    params = {
        "nickname": nickname,
        "maxFriends": max_friends,
    }
    params = {key: value for key, value in params.items() if value is not None}
    print(headers)
    response = httpx.get("https://scapi.rockstargames.com/profile/getprofile/", params=params, headers=headers).json()
    print("ANTON", response)
    # print(httpx.get(url, headers=headers))
    # response = httpx.get(url, headers=headers).json()
    print(response)
    if not response['status'] and first_try:
        cookies = await refresh_access(open(data_folder / "cookies.json", "r").read())
        first_try = False
        cookies_data = {i['name']: i for i in json.loads(cookies)}
        headers['Authorization'] = f"Bearer {cookies_data['BearerToken']['value']}"
        return await get_user_info(headers, nickname, max_friends, first_try)
    print(response)
    return response


async def get_data(headers: dict, url: str, page_count: int = 1,
                   page_size: int = 15, page_offset: int = 0) -> dict[str, str]:

    url += "&pageIndex=0"
    url_part = 'https://scapi.rockstargames.com/search/mission'

    query_params = parse_qs(url[url.find("?") + 1:])
    query_params = {x: ' '.join(y) for x, y in query_params.items()}

    if url.find("member"):
        member_name = url[url.find("member") + 7:url.find("/jobs")]
        user_id = (await get_user_info(headers=headers, nickname=member_name))["accounts"][0]["rockstarAccount"]["rockstarId"]
        query_params['creatorRockstarId'] = user_id

    if not page_count:
        query_params['pageSize'] = str(1)
        page_count = httpx.get(url_part, params=query_params, headers=headers).json()['total'] // page_size

    query_params['pageSize'] = str(page_size)

    i = 0
    data = {}

    for i in range(page_offset, page_offset + page_count):
        query_params['pageIndex'] = str(i)

        r = httpx.get(url_part, params=query_params, headers=headers).json()
        if not r['status']:
            cookies = await refresh_access(open(data_folder / "cookies.json", "r").read())
            cookies_data = {i['name']: i for i in json.loads(cookies)}
            headers['Authorization'] = f"Bearer {cookies_data['BearerToken']['value']}"
            r = httpx.get(url_part, params=query_params, headers=headers).json()

        if not data:
            data = r
        else:
            data['content']['items'] += r['content']['items']
            data['content']['users'].update(r['content']['users'])
            data['content']['crews'].update(r['content']['crews'])

        i += 1

        has_more = r['hasMore']
        if not has_more:
            break

    data['currentPage'] = str(i - 1)
    data['hasMore'] = False
    return data


async def refresh_access(old_cookies):
    old_cookies_data = {i['name']: i for i in json.loads(old_cookies)}
    url = 'https://socialclub.rockstargames.com/connect/refreshaccess'
    headers = {
        'User-Agent': ua.random,
        'X-Requested-With': 'XMLHttpRequest',
    }
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQwMjFiOTUzLTFlYWItNGQ5ZC04YjJjLTllZTM0MDFjODRlZiIsInR5cCI6IkpXVCJ9.eyJuYW1laWQiOiIyNDIwMzM0MDAiLCJzY0F1dGguU2NBdXRoVG9rZW4iOiJBQUFBQXJFUVdZQ3owalVtVGRMYi9hSGFTVFFNdTBjQVZ6OXBtRHZuNlhSbVFnUTZSUkhZRFI4ekxVYVhqbHVvTTViTVV1RDZ6ejluU3dEZnNCaWUrSDlPQ294WE8rQVdDcWFXWjlxamsxMVcxN0JTMmVtWGVIUzV5cFF6WTkxdDZVMUhOQmZ4N3RGZUphQ0ZsbUIxNU5jQVFuTE5ZaEU9Iiwic2NBdXRoLklzQU1pbm9yIjoiRmFsc2UiLCJzY0F1dGguTmlja25hbWUiOiJhbnRvbm92X2FudG9uX2FuIiwic2NBdXRoLkF2YXRhclVybCI6Imh0dHBzOi8vcHJvZC1hdmF0YXJzLmFrYW1haXplZC5uZXQvc3RvY2stYXZhdGFycy9uL2RlZmF1bHQucG5nIiwic2NBdXRoLklzRW1haWxWZXJpZmllZCI6IlRydWUiLCJzY0F1dGguS2VlcE1lU2lnbmVkSW4iOiJGYWxzZSIsInNjQXV0aC5Ub2tlblN0b3JhZ2VUdGwiOiIwIiwic2NBdXRoLlJkcjJBY2Nlc3MiOiIiLCJuYmYiOjE3MDU1NDc2ODIsImF1ZCI6WyJodHRwczovL3NvY2lhbGNsdWIucm9ja3N0YXJnYW1lcy5jb20iLCJodHRwczovL3NjYXBpLnJvY2tzdGFyZ2FtZXMuY29tIl0sInNjb3BlIjoic2NhcGk6KiIsImV4cCI6MTcwNTU0Nzk4MiwiaWF0IjoxNzA1NTQ3NjgyLCJpc3MiOiJodHRwczovL3NpZ25pbi5yb2Nrc3RhcmdhbWVzLmNvbSJ9.d3pkvgfoSOYBh0Z6o2JUFT8Mcb3N6U85GxSLha9RKBX6yCW7M21-SJaXomF8uJIr56jsdT5WeH300dnF_foJ1kCryKJlY9hemtU1el18at0nPqxC9P_0itRe3dTAQLN06PJe-UgCymKAnStaMJTKtkj8g4npd7y7zp5miNj58xTYl8dxBj_ytT1iroi3iOXXe4TtGEMakEmJbKWxg9pcyW5nLHMzrb0jVseiSP63aZzALZwQ1BKlk6wRKOmczEEiKrUWHrbO_0wQXhUrtYyNLOwA8_apCff0mOxeF3ZWXHlXrRO7sZRRjVpcfXZZSjJHAHwy9NmDB7QxnhhMVgnq4Q"
    data = {
        'accessToken': old_cookies_data['BearerToken']['value'],
    }

    cookies = {
        "BearerToken": old_cookies_data["BearerToken"]["value"],
    # }

    print("REFRESHING")
    print(old_cookies_data['BearerToken']['value'])
    try:
        r = httpx.post(url=url, headers=headers, data=data, cookies=cookies)
        print(r)
        print(1)

        if r.status_code == 401:
            print("autism")
            await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
            new_cookies = open(data_folder / "cookies.json", "r").read()
        else:
            new_token = r.cookies.jar._cookies[list(r.cookies.jar._cookies.keys())[0]]["/"]["BearerToken"].value
            new_ts_token = r.cookies.jar._cookies[list(r.cookies.jar._cookies.keys())[0]]["/"]["TS011be943"].value

            old_cookies_data["BearerToken"]["value"] = new_token
            old_cookies_data["TS011be943"]["value"] = new_ts_token
            new_cookies = json.dumps([i for x, i in old_cookies_data.items()], indent=4)
            with open(data_folder / "cookies.json", "w") as f:
                print("govno")
                f.write(new_cookies)
        print("REFRESHING end")
        return new_cookies
    except Exception as e:
        print('ERROR', type(e), e)


async def parse_link(url: str, page_count: int = 1, page_size: int = 15, page_offset: int = 0) -> dict[str, str]:
    """
    Retrieves a list of jobs based on url.
    Url example: https://socialclub.rockstargames.com/jobs/?dateRange=any&platform=pc&sort=plays&title=gtav
    :param url: str, url to parse
    :param page_count: int, number of pages to retrieve (default is 1)
    :param page_size: int, number of items per page (default is 15)
    :param page_offset: int, page offset (default is 0)
    :return: On success, returns a dictionary of Rockstar jobs.
    """

    cookies = open(data_folder / "cookies.json", "r").read()
    names = [i['name'] for i in json.loads(cookies)]
    print("GAY", cookies)

    if 'BearerToken' not in names:
        await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
        cookies = open(data_folder / "cookies.json", "r").read()

    print("GAY", cookies)
    cookies_data = {i['name']: i for i in json.loads(cookies)}
    headers = {
        "Authorization": f"Bearer {cookies_data['BearerToken']['value']}",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "scapi.rockstargames.com",
        "Origin": "https://socialclub.rockstargames.com",
        "Referer": "https://socialclub.rockstargames.com/",
        'User-Agent': ua.random,
        "X-Requested-With": "XMLHttpRequest"
    }

    data = await get_data(headers, url, page_count=page_count, page_size=page_size, page_offset=page_offset)
    return data


async def parse_filters(mission_type: Optional[str | None] = "",
                        subtype: Optional[str | None] = "",
                        platform: str = "pc",
                        player_count: Optional[str | None] = "",
                        date: str = "last7",
                        sort_method: str = "likes",
                        author: Optional[str | None] = "",
                        page_count: int = 1,
                        page_size: int = 15,
                        page_offset: int = 0) -> dict[str, str]:
    """
    Retrieves a list of jobs based on specified filters.

    :param mission_type: The main mission type. Possible values:
        - 'mission'
        - 'deathmatch'
        - 'kingofthehill'
        - 'race'
        - 'survival'
        - 'capture'
        - 'lastteamstanding'
        - 'parachuting'

    :param subtype: An optional subtype that relates to the mission type. Subtypes vary depending on the mission type.
        - For 'mission': ['versus', 'adversary']
        - For 'deathmatch': ['deathmatch', 'teamdeathmatch', 'vehicledeathmatch', 'arenadeathmatch']
        - For 'kingofthehill': ['kingofthehill', 'teamkingofthehill']
        - For 'race': ['pursuitrace', 'streetrace', 'openwheelrace', 'arenawar', 'transformrace', 'specialrace',
           'stuntrace', 'targetrace', 'airrace', 'bikerace', 'landrace', 'waterrace']

    :param platform: The platform for the job. Possible values: 'ps5', 'xboxsx', 'ps4', 'xboxone', 'pc'
    :param player_count: The desired player count for the job. Possible values: '', '1', '2', '4', '8', '16', '30'
    :param date: The date range for the job. Possible values: 'any', 'today', 'last7', 'lastmonth', 'lastyear'
    :param sort_method: The sorting method for the job list. Possible values: 'likes', 'plays', 'date'
    :param author: An optional parameter to specify the author's nickname.
    :param page_count: The number of pages to retrieve (default is 1).
    :param page_size: The number of items per page (default is 15).
    :param page_offset: The page offset (default is 0).

    :return: On success, returns a dictionary of Rockstar jobs.
    """

    cookies = open(data_folder / "cookies.json", "r").read()
    names = [i['name'] for i in json.loads(cookies)]

    if 'BearerToken' not in names:
        await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
        cookies = open(data_folder / "cookies.json", "r").read()

    cookies_data = {i['name']: i for i in json.loads(cookies)}
    headers = {
        "Authorization": f"Bearer {cookies_data['BearerToken']['value']}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    url = "https://socialclub.rockstargames.com/"
    if author:
        url += f"member/{author}/"
    url += f"jobs?dateRange={date}&missiontype={mission_type}&subtype={subtype}&platform={platform}" \
           f"&players={player_count}&sort={sort_method}&title=gtav"

    data = await get_data(headers, url, page_count=page_count, page_size=page_size, page_offset=page_offset)
    return data
