import json
import os
import re
import shutil
import time

from pymongo import MongoClient
from sentiment_analysis import SentimentAnalysis

# 连接到MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['bilibili']
# collection = db['video_comments_v4']
collection = db['video_comments_5110']

"""
将数据库中的评论数据根据aid导出为JSON文件
"""


def export_comments_to_json(aid):
    # 根据aid筛选出同一个视频的所有评论
    comments_cursor = collection.find({'aid': aid}).sort('page', 1)

    # 初始化变量
    comments_info = []
    keyword = ""
    title = ""
    video_info = {}

    # 遍历所有评论数据
    for doc in comments_cursor:
        if doc['page'] == 1:
            keyword = doc['keyword']
            title = doc['title']
            video_info = doc['video_info']

        comments_info.extend(doc['commentsInfo'])

    # 构建JSON数据
    json_data = {
        'aid': aid,
        'keyword': keyword,
        'title': title,
        'video_info': video_info,
        'commentsInfo': comments_info
    }

    # 输出JSON文件
    sanitized_title = sanitize_filename(title)
    # file_name = f"comments/bilibili/raw/{keyword}__{sanitized_title}.json"
    file_name = f"comments/5110/raw/{keyword}__{sanitized_title}.json"
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    print(f"[{title}]  导出成功\n文件名: {file_name}\n")


"""
    清洗文件名字符串
"""


def sanitize_filename(filename):
    filename = re.sub(r'<.*?>', '', filename)
    filename = re.sub(r'".*?"', r'“.*?”', filename)
    filename = filename.replace('?', '？')
    filename = filename.replace('"', '')
    filename = filename.replace(':', '：')
    filename = filename.replace('+', '+')
    filename = filename.replace('|', '  ')
    filename = filename.replace('\\', '_')
    filename = filename.replace('/', '_')
    filename = filename.replace('*', '×')
    filename = filename.replace('<', '《')
    filename = filename.replace('>', '》')
    return filename


def get_json_files():
    aid_list = collection.distinct('aid')
    # 遍历aid数组并调用export_comments_to_json函数
    for aid in aid_list:
        export_comments_to_json(aid)


def categorize_by_gender():
    # raw_file_path = "comments/bilibili/homo/"
    raw_file_path = "comments/bilibili/raw/"
    # processed_file_path = "comments/bilibili/categorized/processed_homo/"
    processed_file_path = "comments/bilibili/processed/"
    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            comments_info = data['commentsInfo']
            comments_male = []
            comments_female = []
            comments_unknown = []
            comments_all = [{"MALE": comments_male}, {"FEMALE": comments_female}, {"UNKNOWN": comments_unknown}]
            # 遍历所有评论数据
            for comment in comments_info:
                # 判断性别
                if comment['usex'] == '男':
                    comments_male.append(comment)
                elif comment['usex'] == '女':
                    comments_female.append(comment)
                elif comment['usex'] == '保密':
                    comments_unknown.append(comment)

            # 构建JSON数据
            for c in comments_all:
                json_data = {
                    'aid': data['aid'],
                    'keyword': data['keyword'],
                    'title': data['title'],
                    'video_info': data['video_info'],
                    'commentsInfo': c.get(list(c.keys())[0])
                }
                # 输出JSON文件
                os.makedirs(processed_file_path, exist_ok=True)
                file_name = f"{processed_file_path}{list(c.keys())[0]}__{file}"
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)

                print(f"导出成功, 文件名: {file_name}\n")


def merge_comments():
    raw_file_path = "comments/bilibili/raw/"
    # raw_file_path = "comments/bilibili/categorized/female/"
    processed_file_path = "comments/bilibili/merge_v2/"
    # processed_file_path = "comments/bilibili/categorized/female_merged/"
    comments_male = []
    comments_female = []
    comments_unknown = []
    comments_all = [{"MALE": comments_male}, {"FEMALE": comments_female}, {"UNKNOWN": comments_unknown}]
    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            comments_info = data['commentsInfo']
            # 遍历所有评论数据
            for comment in comments_info:
                # 判断性别
                # if comment['usex'] == '男':
                #     comments_male.append(comment)
                # elif comment['usex'] == '女':
                #     comments_female.append(comment)
                # elif comment['usex'] == '保密':
                #     comments_unknown.append(comment)

                if comment['usex'] == '男':
                    comments_male.append(comment['content'])
                elif comment['usex'] == '女':
                    comments_female.append(comment['content'])
                elif comment['usex'] == '保密':
                    comments_unknown.append(comment['content'])

    # 构建JSON数据
    for c in comments_all:
        json_data = {
            'commentsInfo': c.get(list(c.keys())[0])
        }
        # 输出JSON文件
        os.makedirs(processed_file_path, exist_ok=True)
        # file_name = f"{processed_file_path}{list(c.keys())[0]}__comments_all.json"
        file_name = f"{processed_file_path}{list(c.keys())[0]}__comments_to_female.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"导出成功, 文件名: {file_name}\n")


"""
不区分性别，合并所有评论数据
"""


def merge_all_comments():
    # raw_file_path = "comments/bilibili/raw/"
    sen = "negative"
    raw_file_path = f"comments/5110/processed/{sen}/"
    # raw_file_path = "comments/bilibili/categorized/female/"
    # processed_file_path = "comments/bilibili/merge_v2/"
    processed_file_path = "comments/5110/processed/"
    # processed_file_path = "comments/bilibili/categorized/female_merged/"
    comments_all = []
    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            comments_info = data['commentsInfo']
            # 遍历所有评论数据
            for comment in comments_info:
                comments_all.append(comment['content'])
            print(f"导出成功, 文件名: {file}\n")

        # 构建JSON数据

    json_data = {
        'commentsInfo': comments_all
    }
    # 输出JSON文件
    os.makedirs(processed_file_path, exist_ok=True)
    file_name = f"{processed_file_path}comments_{sen}.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def merge_all_comments_5110():
    # raw_file_path = "comments/bilibili/raw/"
    sen = "neural"
    raw_file_path = f"comments/5110/processed/{sen}/"
    # raw_file_path = "comments/bilibili/categorized/female/"
    # processed_file_path = "comments/bilibili/merge_v2/"
    processed_file_path = "comments/5110/processed/"
    # processed_file_path = "comments/bilibili/categorized/female_merged/"
    comments_all = []
    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            comments_info = data['commentsInfo']
            # 遍历所有评论数据
            comments_all.extend(comments_info)
            print(f"导出成功, 文件名: {file}\n")

        # 构建JSON数据

    json_data = {
        'commentsInfo': comments_all
    }
    # 输出JSON文件
    os.makedirs(processed_file_path, exist_ok=True)
    file_name = f"{processed_file_path}comments_{sen}.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

# 合并同一视频的评论数据
def merge_video_comments():
    # raw_file_path = "comments/bilibili/raw/"
    raw_file_path = "comments/5110/raw/"
    # raw_file_path = "comments/bilibili/categorized/female/"
    # processed_file_path = "comments/bilibili/merge_v2/"
    processed_file_path = "comments/5110/merge/"
    # processed_file_path = "comments/bilibili/categorized/female_merged/"

    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        comments_all = []
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            comments_info = data['commentsInfo']
            # 遍历所有评论数据
            for comment in comments_info:
                comments_all.append(comment['content'])
            # 构建JSON数据
            json_data = {
                'commentsInfo': comments_all
            }
            print(f"导出成功, 文件名: {file}\n")
            # 输出JSON文件
            os.makedirs(processed_file_path, exist_ok=True)
            file_name = f"{processed_file_path}__{file}"
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)


def category_by_keyword():
    # 提取视频关键字
    raw_file_path = "comments/bilibili/raw/"
    processed_file_path = "comments/bilibili/categorized/female"
    keyword_male = ["男同性恋", "男生和男生谈恋爱日常"]
    keyword_female = ["女同性恋", "le"]
    keyword_homo = ["同性恋"]
    male_path = "male/"
    female_path = "female/"
    homo_path = "homo/"
    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            keyword = data['keyword']
            if keyword in keyword_male:
                target_path = processed_file_path + male_path
            elif keyword in keyword_female:
                target_path = processed_file_path + female_path
            elif keyword in keyword_homo:
                target_path = processed_file_path + homo_path
            shutil.copy(raw_file_path + file, target_path + file)

            print(f"导出成功, 文件名: {file}\n")


def categorize_by_sentiment():
    sentiment_analyzer = SentimentAnalysis()
    raw_file_path = "comments/5110/merge/"
    processed_file_path = "comments/5110/processed/"

    # 读取所有原文件
    for file in os.listdir(raw_file_path):
        with open(raw_file_path + file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                print(f"文件读取失败: {file}")
            comments_info = data['commentsInfo']
            comments_postive = []
            comments_negative = []
            comments_neutral = []
            comments_all = [{"postive": comments_postive}, {"negative": comments_negative},
                            {"neutral": comments_neutral}]
            # 遍历所有评论数据
            for comment in comments_info:
                # 判断情感
                sentiment_result = sentiment_analyzer.sentiment_classify(comment)
                print(sentiment_result)
                if 'items' not in sentiment_result or sentiment_result['items'] is None:
                    while True:
                        if sentiment_result['error_code'] == 18:
                            time.sleep(0.1)
                            sentiment_result = sentiment_analyzer.sentiment_classify(comment)
                        if 'items' in sentiment_result or sentiment_result['error_code'] == 216630:
                            break
                        # if sentiment_result['error_code'] == 216630:
                        #     break
                    if sentiment_result['error_code'] == 216630:
                        # 此时为无效词
                        # total_weight = total_weight - weight
                        continue

                sentiment = sentiment_result['items'][0]['sentiment']
                confidence = sentiment_result['items'][0]['confidence']
                negative_prob = sentiment_result['items'][0]['negative_prob']
                positive_prob = sentiment_result['items'][0]['positive_prob']

                if sentiment == 2:
                    comments_postive.append(comment)
                elif sentiment == 0:
                    comments_negative.append(comment)
                elif sentiment == 1:
                    comments_neutral.append(comment)

            # 构建JSON数据
            for c in comments_all:
                json_data = {
                    'commentsInfo': c.get(list(c.keys())[0])
                }
                # 输出JSON文件
                os.makedirs(processed_file_path, exist_ok=True)
                file_name = f"{processed_file_path}{list(c.keys())[0]}__{file}"
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)

                print(f"导出成功, 文件名: {file_name}\n")


if __name__ == "__main__":
    # 导出所有数据库评论数据到JSON文件
    # get_json_files()

    # 将所有评论信息根据视频类别分类
    # category_by_keyword()

    # 将所有评论信息根据性别分类
    # categorize_by_gender()

    # 合并所有相同性别的评论数据
    # merge_comments()
    # 不区分性别合并评论数据
    # merge_all_comments()
    merge_all_comments_5110()
    # merge_video_comments()

    # categorize_by_sentiment()

    # pass
