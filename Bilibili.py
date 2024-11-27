import asyncio
import json
from pprint import pprint
from pymongo import MongoClient

from bilibili_api.comment import OrderType

from BilibiliScraper import BilibiliScraper
from bilibili_api import Credential, search, topic



class Bilibili:

    def __init__(self):
        # ac_time_value = "4a478ebc8540615b1bd81d534ca5dda2"
        # credential = Credential(sessionData, bili_jct, buvid3, dedeuserid, ac_time_value)
        pass

    # async def main(self) -> None:
    #     u = user.User(self.__uid, self.credential)
    #     res0 = await u.get_dynamics_new(940233543259258887)
    #
    #     print(res0)
    #     # res = await u.get_all_followings()
    #     # print(res)

    async def main(self) -> None:
        b = BilibiliScraper()
        keyword = "同性恋 vlog"
        for i in range(1, 10):
            await b.get_video_comments_by_keyword(keyword,i)


if __name__ == "__main__":
    # 获取视频对应评论区
    bilibili = Bilibili()
    asyncio.run(bilibili.main())
