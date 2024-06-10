from typing import Optional

from RCSParser.api.auth import Auth
from RCSParser.utils.client import AiohttpClient, ABCHTTPClient


class API:
    SCAPI_URL = "https://scapi.rockstargames.com"
    SC_URL = "https://socialclub.rockstargames.com"

    def __init__(
            self,
            token: str = None,
            credentials: dict = None,
            auth: Auth = Auth(),
            http_client: ABCHTTPClient = AiohttpClient(),
    ):
        if not token and not credentials and not auth:
            raise ValueError("You must specify token or credentials or auth")

        self.auth = Auth(token=token) if token else Auth(credentials=credentials) if credentials else auth
        self.http_client = http_client

    async def request(self, API_URL: str, method: str, params: dict, data: dict = None) -> dict:
        if not self.auth.token:
            print("First login")
            await self.auth.login()

        if not params:
            params = {}
        if not data:
            data = {}
        params = {key: value for key, value in params.items() if value is not None}
        data = {key: value for key, value in data.items() if value is not None}

        print(f"123123 {API_URL}{method}")
        response = await self.http_client.request_raw(
            f"{API_URL}{method}",
            method="GET",
            params=params,
            data=data,
            headers=self.auth.headers,
        )

        url1 = "https://scapi.rockstargames.com/search/mission?dateRange=any&sort=likes&platform=pc&title=gtav&missiontype=race&subtype=streetrace&players=4&includeCommentCount=true&pageSize=1"
        response = await self.http_client.request_raw(
            f"https://socialclub.rockstargames.com/jobs/?dateRange=lastmonth&missiontype=race&platform=pc&players=4&sort=likes&subtype=streetrace&title=gtav",
            method="GET",
            headers=self.auth.headers,
        )

        if response.status == 401:
            # logger.warning("AUTH EXPIRED, REFRESHING VIA REFRESH_TOKEN...")
            print("AUTH EXPIRED")
            await self.auth.refresh_auth_data(self.http_client)
            return await self.request(API_URL, method, params, data)

        try:
            response_json = await response.json(
                encoding="utf-8", content_type=None
            )
        except ValueError:
            response_json = {}

        if response.status // 100 != 2:
            raise Exception("Unknown error")

        return response_json

    async def get_user_info(self, nickname: str = "Makcxim", *, max_friends: int = 3):
        response = await self.request(
            self.SCAPI_URL,
            f"/profile/getprofile",
            params={"nickname": nickname,
                    "maxFriends": max_friends},
        )
        print(123)
        return response

    async def parse_link(self, url: str, page_count: int = 1,
                         page_size: int = 15, page_offset: int = 0):
        """
        Retrieves a list of jobs based on url.
        Url example: https://socialclub.rockstargames.com/jobs/?dateRange=any&platform=pc&sort=plays&title=gtav
        :param url: str, url to parse
        :param page_count: int, number of pages to retrieve (default is 1)
        :param page_size: int, number of items per page (default is 15)
        :param page_offset: int, page offset (default is 0)
        :return: On success, returns a dictionary of Rockstar jobs.
        """
        params = dict((itm.split('=')[0], itm.split('=')[1]) for itm in url.split('&')[1:])
        params["pageIndex"] = 0

        print(params)
        print(self.SC_URL, f"/jobs", params)
        print(f"{self.SC_URL}/jobs")

        response = await self.request(
            self.SC_URL,
            f"/jobs",
            params=params,
        )

        # cookies = open(data_folder / "cookies.json", "r").read()
        # names = [i['name'] for i in json.loads(cookies)]
        # print("GAY", cookies)
        #
        # cookies_data = {i['name']: i for i in json.loads(cookies)}
        # headers = {
        #     "Authorization": f"Bearer {cookies_data['BearerToken']['value']}",
        #     "Cache-Control": "no-cache",
        #     "Connection": "keep-alive",
        #     "Host": "scapi.rockstargames.com",
        #     "Origin": "https://socialclub.rockstargames.com",
        #     "Referer": "https://socialclub.rockstargames.com/",
        #     'User-Agent': ua.random,
        #     "X-Requested-With": "XMLHttpRequest"
        # }

        # data = await get_data(headers, url, page_count=page_count, page_size=page_size, page_offset=page_offset)
        # return data

    async def parse_filters(self,
                            mission_type: Optional[str | None] = "",
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


        response = await self.request(
            self.SC_URL,
            f"/jobs",
            params={"missiontype": mission_type,
                    "subtype": subtype,
                    "platform": platform,
                    "players": player_count,
                    "dateRange": date,
                    "sort": sort_method,
                    "author": author,
                    "pageCount": page_count,
                    "pageSize": page_size,
                    "pageOffset": page_offset},
        )

        return response

        # cookies = open(data_folder / "cookies.json", "r").read()
        # names = [i['name'] for i in json.loads(cookies)]
        #
        # if 'BearerToken' not in names:
        #     await logining('https://signin.rockstargames.com/signin/user-form?cid=socialclub')
        #     cookies = open(data_folder / "cookies.json", "r").read()
        #
        # cookies_data = {i['name']: i for i in json.loads(cookies)}
        # headers = {
        #     "Authorization": f"Bearer {cookies_data['BearerToken']['value']}",
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        #     "X-Requested-With": "XMLHttpRequest"
        # }
        #
        # url = "https://socialclub.rockstargames.com/"
        # if author:
        #     url += f"member/{author}/"
        # url += f"jobs?dateRange={date}&missiontype={mission_type}&subtype={subtype}&platform={platform}" \
        #        f"&players={player_count}&sort={sort_method}&title=gtav"
        #
        # data = await get_data(headers, url, page_count=page_count, page_size=page_size, page_offset=page_offset)
        # return data

    async def get_data(self, headers: dict, url: str, page_count: int = 1,
                       page_size: int = 15, page_offset: int = 0) -> dict[str, str]:

        url += "&pageIndex=0"
        url_part = 'https://scapi.rockstargames.com/search/mission'

        query_params = parse_qs(url[url.find("?") + 1:])
        query_params = {x: ' '.join(y) for x, y in query_params.items()}

        if url.find("member"):
            member_name = url[url.find("member") + 7:url.find("/jobs")]
            user_id = (await get_user_info(headers=headers, nickname=member_name))["accounts"][0]["rockstarAccount"][
                "rockstarId"]
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


