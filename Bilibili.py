import asyncio
import json
from pprint import pprint
from pymongo import MongoClient

from bilibili_api.comment import OrderType

from BilibiliScraper import BilibiliScraper
from bilibili_api import Credential, search, topic, sync, comment

SESSIONDATA = "5c6212a6%2C1748369428%2C0447a%2Ab1CjB_fxfOr4CgIz7d9sUI8GO3Ut41Esv4a_T4Kva3QDmWZLaqFbko9lBk4d0RojQC9eISVnN1U1V4MHVwYWloZ1VoSVRXZnNCZWF1V3QwTm1SQlhaOFczVkNRSkVhME1FYmhDMGhzTEs4a1RZUlgxbFlQcmd5YTkxd0VQNmNrMWFhT09sRkxrajZ3IIEC"
BILI_JCT = "1dd1c9707667a29b784aa4b9813093ac"
BUVID3 = "511C591E-F1B2-96DD-F144-C09AB3AB450C91088infoc"
DEDEUSERID = "3546810735921249"
AC_TIME_VALUE = "240dcbc7d62168efdcc9739e461a9db1"


class Bilibili:

    def __init__(self):
        credential = Credential(SESSIONDATA, BILI_JCT, BUVID3, DEDEUSERID, AC_TIME_VALUE)
        self.credential = credential
        print(sync(credential.check_refresh()))
        if sync(credential.check_refresh()):
            sync(credential.refresh())
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
        keyword = "同性恋"

        # test
        # c = await comment.get_comments_lazy(113564136249182, comment.CommentResourceType.VIDEO, '',OrderType.LIKE, self.credential)
        # replies = c['replies']
        # print(replies)



        for i in range(1, 10):
            await b.get_video_comments_by_keyword(keyword,i)

        # 获取指定视频
        # await b.get_all_comments_by_video("337044251", self.credential, OrderType.LIKE)


if __name__ == "__main__":
    # 获取视频对应评论区
    bilibili = Bilibili()
    asyncio.run(bilibili.main())
