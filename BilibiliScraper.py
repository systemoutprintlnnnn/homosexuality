from pprint import pprint

import requests
from typing import Dict, List, Any, Optional
from bilibili_api import Credential, comment, search
from bilibili_api.comment import OrderType
from pymongo import MongoClient

from utils.credentialManager import CredentialManager



SESSIONDATA = "2dda6db0%2C1747841787%2C1440f%2Ab2CjCGSc9TITGmERi_x5pSMr0eGGiNnHH6IEYzRGJ_eeqQgLDY8jC7DvwB8jRKnHdYeIkSVjhVcFhxcWpaRk1ENHN4Q2duRGVIVWZKMUNrbHRPNFUyT2xlMm5EOVlEUEhaSm5sV3lrQ1hjbm4ydTdWbHZ5SzRlRFpFSWZGelY2SF9yd3A5bjlrQUZBIIEC"
BILI_JCT = "e2fb58c0c3a26de11c64f73a882b4e65"
BUVID3 = "A2D4DF5D-8110-2AD2-712E-CB70E86E460D66077infoc"
DEDEUSERID = "35556285"
GAY_KEYWORDS = ["男", "Gay", "gay", "夫夫"]
LES_KEYWORDS = ["女", "Les", "les", "拉拉", "百合", "橘"]

"""
根据oid（资源id）获取视频评论
参数:
    oid (str): 视频的 oid
    credential (Credential): 登录凭证
    OrderType (OrderType, 可选): 评论排序方式，默认为 OrderType.LIKE
返回:
    Any: 评论列表

"""
class BilibiliScraper:
    def __init__(self):
        credential = Credential(SESSIONDATA, BILI_JCT, BUVID3, DEDEUSERID)
        self.credential = credential
        self.__uid = DEDEUSERID
        self.gay_keywords = GAY_KEYWORDS
        self.les_keywords = LES_KEYWORDS

        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['bilibili']
        self.collection = self.db['videos']


    async def get_all_comments_by_video(self, oid: str, credential: Credential,
                                        OrderType: Optional[OrderType] = OrderType.LIKE) -> Any:
        # 存储评论
        comments = []
        # 页码
        page = 1
        # 当前已获取数量
        count = 0
        res = {}
        commentsInfo = []
        while True or count < 1000:
            # 获取评论
            c = await comment.get_comments(oid, comment.CommentResourceType.VIDEO, page, OrderType.LIKE,
                                           credential)

            replies = c['replies']
            if replies is None:
                # 未登陆时只能获取到前20条评论
                # 此时增加页码会导致c为空字典
                break

            # 存储评论
            comments.extend(replies)
            # 增加已获取数量
            count += c['page']['size']
            # 增加页码
            page += 1

            if count >= c['page']['count']:
                # 当前已获取数量已达到评论总数，跳出循环
                break

        # 打印评论
        for cmt in comments:
            uname = cmt['member']['uname']
            usex = cmt['member']['sex']
            content = cmt['content']['message']
            commentsInfo.append({'uname': uname, 'usex': usex, 'content': content})
            # print(f"{uname}({usex}): {content}")
            # print(f"{cmt['member']['uname']}: {cmt['content']['message']}")

        # 打印评论总数
        # print(f"\n\n共有 {count} 条评论（不含子评论）")
        res['oid'] = oid
        res['commentsInfo'] = commentsInfo
        return res

    async def get_video_comments_by_keyword(self, keyword: str, page: int = 1):
        # 搜索视频
        search_result = await search.search(keyword, page)
        results = search_result.get('result', [])
        for temp in results:
            if (temp.get('result_type') in 'video'):
                data = temp.get('data')
        # 获取视频信息
        video_response = []
        for video in data:
            video_info = {}
            tag = video.get('tag')
            aid = video.get('aid')
            bvid = video.get('bvid')
            title = video.get('title')
            category = "unknown"
            if any(keyword in tag for keyword in self.gay_keywords) or any(
                    keyword in title for keyword in self.gay_keywords):
                category = "gay"

            if any(keyword in tag for keyword in self.les_keywords) or any(
                    keyword in title for keyword in self.les_keywords):
                if category == "gay":
                    category = "uncertain"
                category = "les"

            video_info['tag'] = tag
            video_info['aid'] = aid
            video_info['bvid'] = bvid
            video_info['title'] = title
            video_info['category'] = category
            print(video_info)
            video_response.append(video_info)

            # 获取对应所有评论
            commentsList = []
            aid = video.get('aid')
            # aid = 113527025045380
            r = await self.get_all_comments_by_video(aid, self.credential, OrderType.LIKE)
            pprint(r)
            commentsInfo = r.get('commentsInfo')

            # 存入MongoDB
            # self.collection.insert_one({
            #     '_id': aid,
            #     'title': title,
            #     'video_info': video_info,
            #     'commentsInfo': commentsInfo
            # })

            self.collection.update_one(
                {'_id': aid},
                {
                    '$set': {
                        'title': title,
                        'video_info': video_info,
                        'commentsInfo': commentsInfo
                    }
                },
                upsert=True
            )
