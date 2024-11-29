import random
from asyncio import sleep
from datetime import datetime

import requests
from pymongo import MongoClient
from snowflake import SnowflakeGenerator

BEARER_TOKEN = "46YFUnNzzlkevA4PzmeLsn0TiCcHmIP1v6JN2hn47lVdrGsvR+VT3Q6tJg=="
BASE_URL = "https://api.tikhub.io"

GAY_KEYWORDS = ["男同", "Gay", "gay", "夫夫"]
LES_KEYWORDS = ["女同", "Les", "les", "拉拉", "百合", "橘", "姬", "le", "LE"]
HOMO_KEYWORDS = ["同性", "性别", "性取向", "彩虹"]


class DouyinScraper:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}"
        }
        self.search_url = f"{BASE_URL}/api/v1/douyin/web/fetch_general_search_result"
        self.video_comments_url = f"{BASE_URL}/api/v1/douyin/app/v1/fetch_video_comments"

        self.gay_keywords = GAY_KEYWORDS
        self.les_keywords = LES_KEYWORDS
        self.homo_keywords = HOMO_KEYWORDS

        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['douyin']
        self.video_comments_collection = self.db['video_comments_v4']
        self.filted_video_collection = self.db['filted_video_v2']
        self.snowflake = SnowflakeGenerator(instance=1)

    def get_video_comments_by_keyword(self, keyword, offset=0):
        # sort_type: 0:综合排序 1:最多点赞 2:最新发布
        sort_type = 1
        # content_type: 0:不限 1:视频 2:图片 3:文章
        content_type = 1
        data = self.search_video(content_type, offset, sort_type, keyword)
        for item in data:
            aweme_info = item.get('aweme_info')
            aweme_id = aweme_info.get('aweme_id')
            title = aweme_info.get('desc')
            category = "unknown"
            print(f"正在处理视频title: {title}, aweme_id: {aweme_id}")
            video_info = {
                'aweme_id': aweme_id,
                'title': title,
                'category': category
            }

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
                    {'_id': aweme_id},
                    {
                        '$set': {
                            'title': title,
                            'video_info': video_info,
                            'keyword': keyword,
                            'update_time': datetime.now().timestamp(),
                            'source': "douyin",
                            'category': category
                        }
                    },
                    upsert=True
                )
                print(f"视频分类不明确,存入filted_video  [title: {title}], [aweme_id: {aweme_id}]")
                continue

            author_name = aweme_info.get('author').get('nickname')

            # 根据aweme_id获取评论
            cursor = 0
            has_more = 1
            page = 1
            while has_more == 1:
                if self.video_comments_collection.find_one({'aweme_id': aweme_id, 'page': page}):
                    print(f"视频   [{title}]   [第{page}页]    已存在，跳过")
                    page += 1
                    continue

                while True:
                    try:
                        comments_data = self.get_comments(aweme_id, cursor)
                        break
                    except Exception as e:
                        if e.status != 200:
                            t = random.randint(1800, 3000)
                            print(f"Request failed with status {e.status}, retrying in {t} seconds...")
                            sleep(t)
                        else:
                            raise e

                comments = comments_data.get('comments', [])
                cursor = comments_data.get('cursor')
                has_more = comments_data.get('has_more')
                if (has_more == 0) and (comments is None):
                    break
                comments_info = []
                for comment in comments:
                    comment_text = comment.get('text')
                    user = {
                        # 用户昵称
                        'nickname': comment.get('user').get('nickname'),
                        # 抖音号  两个都有可能是，规则未知
                        'short_id': comment.get('user').get('short_id'),
                        'unique_id': comment.get('user').get('unique_id'),
                        # 用户id，用于获取用户信息，【目前暂时找不到方法获取】。
                        'sec_uid': comment.get('user').get('sec_uid'),
                    }
                    comment_author = comment.get('user').get('nickname')

                    # 点赞数
                    comment_digg_count = comment.get('digg_count')
                    cmt = {'aweme_id': aweme_id, 'comment_text': comment_text, 'user': user,
                           'comment_digg_count': comment_digg_count}
                    comments_info.append(cmt)
                    # 插入一页评论
                self.video_comments_collection.insert_one(
                    {
                        '_id': next(self.snowflake),
                        'aweme_id': aweme_id,
                        'title': title,
                        'author_name': author_name,
                        'comments_info': comments_info,
                        'keyword': keyword,
                        'cursor': cursor,
                        'page': page,
                        'category': category
                    }
                )
                print(f"视频   [{title}]   [第{page}页]    评论已存入")
                page += 1

        return data.get('cursor')

    def get_comments(self, aweme_id, cursor):
        # params = {
        #     "aweme_id": aweme_id,
        #     "cursor": cursor
        # }
        # response = requests.get(
        #     self.video_comments_url,
        #     params=params,
        #     headers=self.headers
        # )
        url = f"{self.video_comments_url}?aweme_id={aweme_id}&cursor={cursor}"
        response = requests.get(
            url,
            headers=self.headers
        )
        response.raise_for_status()
        response = response.json()
        data = response.get('data')
        return data

    def search_video(self, content_type, offset, sort_type, keyword):
        # params = {
        #     "keyword": keyword,
        #     "offset": offset,
        #     "sort_type": sort_type,
        #     "content_type": content_type
        # }
        url = f"{self.search_url}?keyword={keyword}&offset={offset}&sort_type={sort_type}&content_type={content_type}"
        response = requests.get(
            url,
            headers=self.headers
        )
        response.raise_for_status()
        response = response.json()
        data = response.get('data').get('data', [])
        return data


if __name__ == "__main__":
    douyin_scraper = DouyinScraper()
    keyword = "同性恋"
    # for i in range(1, 100):
    # 一页20个视频
    offset = 0
    for i in range(1, 2):
        offset = douyin_scraper.get_video_comments_by_keyword(keyword, offset)
