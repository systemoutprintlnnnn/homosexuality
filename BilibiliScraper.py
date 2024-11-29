import asyncio
import datetime
import random
from pprint import pprint
from time import sleep

import requests
from typing import Dict, List, Any, Optional
from bilibili_api import Credential, comment, search, sync, ResponseCodeException
from bilibili_api.comment import OrderType
from bilibili_api.search import SearchObjectType, OrderVideo
from pymongo import MongoClient

from utils.credential_manager import CredentialManager
from snowflake import SnowflakeGenerator

# SESSIONDATA = "df18be41%2C1748400382%2Cf8a4e%2Ab2CjDauk3D8zpQxgKS15MCUkzYBSVYI71pOCPRCT8uIDbaVbezSaRJhmmOdm1NjbPca5wSVko2LTRaYnFSdU9QMVN2VTVWcTRyM19taS0xN2Z5SU41MXhYNzBMRnhwZ0ZGZmpEY0FUWnVONFA5YVBqRmRXZjBvQkNQWWdmZ1h5bXZjVVdCOVQ3SlVRIIEC"
# BILI_JCT = "f5091aeb77b118cea0695950cb5d8c45"
# BUVID3 = "A2D4DF5D-8110-2AD2-712E-CB70E86E460D66077infoc"
# DEDEUSERID = "35556285"
# AC_TIME_VALUE = "90c77ffbe73718c3027943bb866b2bb2"

SESSIONDATA = "5c6212a6%2C1748369428%2C0447a%2Ab1CjB_fxfOr4CgIz7d9sUI8GO3Ut41Esv4a_T4Kva3QDmWZLaqFbko9lBk4d0RojQC9eISVnN1U1V4MHVwYWloZ1VoSVRXZnNCZWF1V3QwTm1SQlhaOFczVkNRSkVhME1FYmhDMGhzTEs4a1RZUlgxbFlQcmd5YTkxd0VQNmNrMWFhT09sRkxrajZ3IIEC"
BILI_JCT = "1dd1c9707667a29b784aa4b9813093ac"
BUVID3 = "511C591E-F1B2-96DD-F144-C09AB3AB450C91088infoc"
DEDEUSERID = "3546810735921249"
AC_TIME_VALUE = "240dcbc7d62168efdcc9739e461a9db1"

GAY_KEYWORDS = ["男同", "Gay", "gay", "夫夫"]
LES_KEYWORDS = ["女同", "Les", "les", "拉拉", "百合", "橘", "姬"]
HOMO_KEYWORDS = ["同性", "性别", "性取向"]

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
        # credential = Credential(SESSIONDATA, BILI_JCT, BUVID3, DEDEUSERID)
        credential = Credential(SESSIONDATA, BILI_JCT, BUVID3, DEDEUSERID, AC_TIME_VALUE)
        self.credential = credential
        print(sync(credential.check_refresh()))
        if sync(credential.check_refresh()):
            sync(credential.refresh())
        self.__uid = DEDEUSERID
        self.gay_keywords = GAY_KEYWORDS
        self.les_keywords = LES_KEYWORDS
        self.homo_keywords = HOMO_KEYWORDS

        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['bilibili']
        self.video_comments_collection = self.db['video_comments_v4']
        self.filted_video_collection = self.db['filted_video']
        self.snowflake = SnowflakeGenerator(instance=1)

    """
    根据oid（资源id）获取视频评论

    """

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
        target_count = 0
        while True or count < 100000:
            sleep(random.randint(10, 30))
            # 获取评论

            while True:
                try:
                    t = random.randint(1800, 3000)
                    c = await comment.get_comments(oid, comment.CommentResourceType.VIDEO, page, OrderType.LIKE,
                                                   credential)
                    break
                except Exception as e:
                    if e.status != 200:
                        print(f"Request failed with status {e.status}, retrying in {t} seconds...")
                        await asyncio.sleep(t)
                    else:
                        raise e

            # c = await comment.get_comments(oid, comment.CommentResourceType.VIDEO, page, OrderType.LIKE, credential)
            # pprint(c)
            # target_count = c['page']['count']

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

            if count >= target_count:
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

    """
    根据oid（资源id）获取视频评论，【并分片存储】
   
    """

    async def get_all_comments_by_video_v2(self, oid: str, credential: Credential, title: str, video_info: Any,
                                           keyword: str,
                                           OrderType: Optional[OrderType] = OrderType.LIKE) -> Any:

        # 页码
        page = 1
        # 当前已获取数量
        count = 0
        # res = {}
        target_count = 0
        while True or count < 100000:
            # 如果已存在不更新直接跳过
            if self.video_comments_collection.find_one({'aid': oid, 'page': page}):
                print(f"视频   {title}   第{page}页    已存在，跳过")
                page += 1
                continue
            sleep(random.randint(10, 30))
            comments = []
            commentsInfo = []
            # 获取评论
            while True:
                try:
                    t = random.randint(1800, 3000)
                    c = await comment.get_comments(oid, comment.CommentResourceType.VIDEO, page, OrderType.LIKE,
                                                   credential)
                    break
                except ResponseCodeException as e:
                    if e.code != 200:
                        print(f"Request failed with status {e.code}, retrying in {t} seconds...")
                        await asyncio.sleep(t)
                    else:
                        raise e

                except Exception as e:
                    if e.status != 200:
                        print(f"Request failed with status {e.status}, retrying in {t} seconds...")
                        await asyncio.sleep(t)
                    else:
                        raise e

            # c = await comment.get_comments(oid, comment.CommentResourceType.VIDEO, page, OrderType.LIKE, credential)
            # pprint(c)
            target_count = c['page']['count']

            replies = c['replies']
            if replies is None:
                # 未登陆时只能获取到前20条评论
                # 此时增加页码会导致c为空字典
                break

            # 存储评论
            comments.extend(replies)
            # 增加已获取数量
            count += len(replies)

            if count >= target_count:
                # 当前已获取数量已达到评论总数，跳出循环
                break

            # 存储评论
            for cmt in comments:
                uname = cmt['member']['uname']
                usex = cmt['member']['sex']
                content = cmt['content']['message']
                commentsInfo.append({'uname': uname, 'usex': usex, 'content': content})

                # print(f"{uname}({usex}): {content}")
                # print(f"{cmt['member']['uname']}: {cmt['content']['message']}")

            # 打印评论总数
            # print(f"\n\n共有 {count} 条评论（不含子评论）")
            # res['oid'] = oid
            # res['commentsInfo'] = commentsInfo

            id = next(self.snowflake)
            insert_value = {
                '_id': id,
                'aid': oid,
                'title': title,
                'video_info': video_info,
                'commentsInfo': commentsInfo,
                'keyword': keyword,
                'page': page,
            }

            self.video_comments_collection.insert_one(insert_value)
            print(f"【第{page}页】：视频 {title} 评论已存入数据库")
            # 增加页码
            page += 1
            # return res

    """
    根据oid（资源id）获取视频评论，【并分片存储】【使用懒加载新接口】
   
    """

    async def get_all_comments_by_video_v3(self, oid: str, credential: Credential, title: str, video_info: Any,
                                           keyword: str,
                                           OrderType: Optional[OrderType] = OrderType.LIKE) -> Any:

        # 页码
        page = 1
        # 当前已获取数量
        count = 0
        # res = {}
        # target_count = 0
        offset = ''
        is_end = False
        while not is_end or count < 100000:
            # 如果已存在不更新直接跳过
            query_res = self.video_comments_collection.find_one({'aid': oid, 'page': page})
            if query_res:
                print(f"视频   {title}   第{page}页    已存在，跳过")
                page += 1
                count += query_res.get('page_count')
                offset = query_res.get('offset')
                continue
            sleep(random.randint(1, 3))
            comments = []
            commentsInfo = []
            # 获取评论
            while True:
                try:
                    t = random.randint(1800, 3000)
                    c = await comment.get_comments_lazy(oid, comment.CommentResourceType.VIDEO, offset, OrderType.LIKE,
                                                        credential)
                    break
                # except ResponseCodeException as e:
                #     if e.code != 200:
                #         print(f"Request failed with status {e.code}, retrying in {t} seconds...")
                #         await asyncio.sleep(t)
                #     else:
                #         raise e

                except Exception as e:
                    if e.status != 200:
                        print(f"Request failed with status {e.status}, retrying in {t} seconds...")
                        await asyncio.sleep(t)
                    else:
                        raise e

            # c = await comment.get_comments(oid, comment.CommentResourceType.VIDEO, page, OrderType.LIKE, credential)
            # pprint(c)
            # target_count = c['page']['count']
            is_end = c['cursor']['is_end']
            if is_end:
                # 当前已获取数量已达到评论总数，跳出循环
                break
            replies = c['replies']
            if replies is None:
                # 未登陆时只能获取到前20条评论
                # 此时增加页码会导致c为空字典
                break
            try:
                offset = c['cursor']['pagination_reply']['next_offset']
            except:
                print(c)
            # 存储评论
            comments.extend(replies)
            # 增加已获取数量
            page_count = len(replies)
            count += page_count

            # 存储评论
            for cmt in comments:
                uname = cmt['member']['uname']
                usex = cmt['member']['sex']
                content = cmt['content']['message']
                commentsInfo.append({'uname': uname, 'usex': usex, 'content': content})

                # print(f"{uname}({usex}): {content}")
                # print(f"{cmt['member']['uname']}: {cmt['content']['message']}")

            # 打印评论总数
            # print(f"\n\n共有 {count} 条评论（不含子评论）")
            # res['oid'] = oid
            # res['commentsInfo'] = commentsInfo

            id = next(self.snowflake)
            insert_value = {
                '_id': id,
                'aid': oid,
                'title': title,
                'video_info': video_info,
                'commentsInfo': commentsInfo,
                'keyword': keyword,
                'page': page,
                'page_count': page_count,
                'offset': offset
            }

            self.video_comments_collection.insert_one(insert_value)
            print(f"第 {page} 页 {page_count} 条评论已存入数据库   视频title： {title} ")
            # 增加页码
            page += 1

    async def get_video_comments_by_keyword(self, keyword: str, page: int = 1):
        # 搜索视频
        # search_result = await search.search(keyword, page)
        search_result = await search.search_by_type(keyword, SearchObjectType.VIDEO, order_type=OrderVideo.CLICK)
        results = search_result.get('result', [])
        # for temp in results:
        # if (temp.get('result_type') in 'video'):
        #     data = temp.get('data')
        # 获取视频信息
        video_response = []
        for video in results:
            video_info = {}
            tag = video.get('tag')
            aid = video.get('aid')
            bvid = video.get('bvid')
            title = video.get('title')
            category = "unknown"

            # is_gay = any(keyword in tag for keyword in self.gay_keywords) or any(
            #     keyword in title for keyword in self.gay_keywords)
            # is_les = any(keyword in tag for keyword in self.les_keywords) or any(
            #     keyword in title for keyword in self.les_keywords)

            # if is_gay and is_les:
            #     category = "uncertain"
            # elif is_gay:
            #     category = "gay"
            # elif is_les:
            #     category = "les"

            video_info['tag'] = tag
            video_info['aid'] = aid
            video_info['bvid'] = bvid
            video_info['title'] = title

            # 这里加强了筛选条件，只考虑视频标题
            # 没有标签的直接筛掉
            is_gay = any(keyword in title for keyword in self.gay_keywords)
            is_les = any(keyword in title for keyword in self.les_keywords)
            is_homo = any(keyword in title for keyword in self.homo_keywords)

            if is_gay:
                category = "gay"
                video_info['category'] = category
            elif is_les:
                category = "les"
                video_info['category'] = category
            elif is_homo:
                category = "homo"
                video_info['category'] = category
            else:
                self.filted_video_collection.update_one(
                    {'_id': aid},
                    {
                        '$set': {
                            'title': title,
                            'video_info': video_info,
                            'keyword': keyword,
                            'update_time': datetime.datetime.now().timestamp(),
                            'source': "bilibili"
                        }
                    },
                    upsert=True
                )
                continue

            # print(video_info)
            video_response.append(video_info)

            # 获取对应所有评论
            commentsList = []
            aid = video.get('aid')

            # # 如果已存在不更新直接跳过
            # if self.collection.find_one({'_id': aid}):
            #     print(f"视频 {title} 已存在，跳过")
            #     continue

            # aid = 113527025045380

            # while True:
            #     try:
            #         r = await self.get_all_comments_by_video(aid, self.credential, OrderType.LIKE)
            #         break
            #     except Exception as e:
            #         if e.status != 200:
            #             print(f"Request failed with status 400, retrying in 5 seconds...")
            #             await asyncio.sleep(5)
            #         else:
            #             raise e

            # r = await self.get_all_comments_by_video_v2(aid, self.credential, title, video_info, keyword, OrderType.LIKE)
            await self.get_all_comments_by_video_v3(aid, self.credential, title, video_info, keyword, OrderType.LIKE)
            # pprint(r)

            # commentsInfo = r.get('commentsInfo')

            # 存入MongoDB
            # self.collection.insert_one({
            #     '_id': aid,
            #     'title': title,
            #     'video_info': video_info,
            #     'commentsInfo': commentsInfo
            # })

            # id = next(self.snowflake)
            # self.collection.insert_many([{
            #     '_id': id,
            #     'aid': aid,
            #     'title': title,
            #     'video_info': video_info,
            #     'commentsInfo': commentsInfo,
            #     'keyword': keyword,
            #     # 'update_time': datetime.datetime.now().timestamp()
            # }])

            # self.collection.update_one(
            #     {'_id': id},
            #     {
            #         '$set': {
            #             'aid': aid,
            #             'title': title,
            #             'video_info': video_info,
            #             'commentsInfo': commentsInfo,
            #             'keyword': keyword,
            #             # 'update_time': datetime.datetime.now().timestamp()
            #         }
            #     },
            #     upsert=True
            # )
            print(f"视频 {title} 评论已全部存入数据库")

# # 将大文档拆分成较小的文档
# def split_large_json(large_json, chunk_size=100):
#     comments = large_json.pop('commentsInfo')
#     for i in range(0, len(comments), chunk_size):
#         chunk = comments[i:i + chunk_size]
#         small_doc = large_json.copy()
#         small_doc['commentsInfo'] = chunk
#         yield small_doc
#
# # 存储拆分后的文档
# for small_doc in split_large_json(large_json):
#     collection.insert_one(small_doc)
