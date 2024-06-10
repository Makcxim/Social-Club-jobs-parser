import asyncio
from RCSParser.api import API, Auth


async def main():
    # govno = Auth(auth_file="data/govno2.json")
    # govno.access_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQwMjFiOTUzLTFlYWItNGQ5ZC04YjJjLTllZTM0MDFjODRlZiIsInR5cCI6IkpXVCJ9.eyJuYW1laWQiOiI4MDM0NTMxNSIsInNjQXV0aC5TY0F1dGhUb2tlbiI6IkFBQUFBcFlRQUo5ZTVqcTBRNHdsOFdwVUx6S0NZVWNBeEZTdXR3TlV5cFFTMllEZ1prM2k1bDJLZW1aUCtlRXdSYVBQTmIwNFVBNUN0bTZkZVJYcGRHbWhOUXVteWpKZ3BTY2RlSDhTQVlOQVNHb09XcHZsMHJHd3pBa0lidFplNm9LbmFzb3dVamNnVGhuQTNzUmUzYm5UOENWeldKOD0iLCJzY0F1dGguSXNBTWlub3IiOiJGYWxzZSIsInNjQXV0aC5OaWNrbmFtZSI6Ik1ha2N4aW0iLCJzY0F1dGguQXZhdGFyVXJsIjoiaHR0cHM6Ly9wcm9kLWF2YXRhcnMuYWthbWFpemVkLm5ldC9zdG9jay1hdmF0YXJzL24vR1RBVi9ndGF2MTYucG5nIiwic2NBdXRoLklzRW1haWxWZXJpZmllZCI6IlRydWUiLCJzY0F1dGguS2VlcE1lU2lnbmVkSW4iOiJGYWxzZSIsInNjQXV0aC5Ub2tlblN0b3JhZ2VUdGwiOiIwIiwic2NBdXRoLlJkcjJBY2Nlc3MiOiIiLCJuYmYiOjE3MDI4MTc4ODgsImF1ZCI6WyJodHRwczovL3NvY2lhbGNsdWIucm9ja3N0YXJnYW1lcy5jb20iLCJodHRwczovL3NjYXBpLnJvY2tzdGFyZ2FtZXMuY29tIl0sInNjb3BlIjoic2NhcGk6KiIsImV4cCI6MTcwMjgxODE4OCwiaWF0IjoxNzAyODE3ODg4LCJpc3MiOiJodHRwczovL3NpZ25pbi5yb2Nrc3RhcmdhbWVzLmNvbSJ9.d2oL4XxqGRio66kQJF2_gmQRpvu_Yl_MeLYKikLtNrDQUFGbIFbiDmnLgGvV5217e4vBHrUFLZsvwR7j38vT4Ds_G1ZN0ZZN2j6GCSX3rLCb1YklGWRdfLWwB2d2RRp0gZBbdV8BpubxMqpKAILxn3ZxK5TiQsTCy2ePzlf04oE3p-1scWWWMDD69OznaDvkOqV0QDBcF4vy0v1lNAiMZvKYNzc4xKihSn5eWgqYlCOAWjK18Sitmhlnaz9CdBO_iZIuBYQ0PB8gDT5Ibv6ctGj8Ooi9lPm1yQCqmuD9cy7rUKq6QGsdQTCIrkEfjBS9wjmp-ISRhqz3C1chUYa1GA"

    api = API(credentials={
        "email": 'frenkyssyknerf@gmail.com',
        "password": 'cBGXW9g7aPNkRJHQfKEMne',
        "debug": True,
    })

    response = await api.get_user_info("Makcxim")
    print("ANSWER: ", response)

    url = "https://socialclub.rockstargames.com/member/-SIIIB-/jobs?dateRange=any&missiontype=race&platform=pc&sort=date&title=gtav"
    response = await api.parse_link(url=url,
                                    page_count=3, page_size=15, page_offset=0)
    print("ANSWER: ", response)


asyncio.run(main())

