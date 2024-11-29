import re

import pandas as pd
# import numpy as np
import jieba
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

class TitleEDA:
    def __init__(self, video_dict):
        """
        初始化EDA分析类

        参数:
        video_dict (dict): 包含视频id和标题的字典
                           格式示例: {
                               'video_id1': '标题1',
                               'video_id2': '标题2',
                               ...
                           }
        """
        # 转换为DataFrame
        self.df = pd.DataFrame.from_dict(video_dict, orient='index', columns=['title'])
        self.df.index.name = 'video_id'
        self.df.reset_index(inplace=True)

        # 中文分词停用词
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self):
        """
        加载中文停用词

        返回:
        set: 停用词集合
        """
        # 基础停用词列表，可根据需要扩展
        basic_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '都', '与',
            '个', '这', '那', '为', '啊', '呢', '吧', '吗', '呀', '哦',
            ' ', '', '视频', ''
        }
        return basic_stopwords

    def basic_statistics(self):
        """
        基本文本统计分析

        输出:
        - 总视频数
        - 标题长度统计
        - 标题字数分布
        """
        print("===== 基本统计分析 =====")
        print(f"总视频数: {len(self.df)}")

        # 标题长度分析
        self.df['title_length'] = self.df['title'].str.len()

        print("\n标题长度统计:")
        print(self.df['title_length'].describe())

        # 绘制标题长度分布直方图
        plt.figure(figsize=(10, 5))
        sns.histplot(self.df['title_length'], kde=True)
        plt.title('视频标题长度分布')
        plt.xlabel('标题长度')
        plt.ylabel('频率')
        plt.rcParams['font.sans-serif'] = ['SimHei']  # Use SimHei font for Chinese characters
        plt.rcParams['axes.unicode_minus'] = False
        plt.tight_layout()
        plt.show()

    def word_frequency_analysis(self, top_n=20):
        """
        词频分析

        参数:
        top_n (int): 展示top N高频词
        """
        print(f"\n===== 词频分析 (Top {top_n}) =====")

        # 分词并过滤停用词
        all_words = []
        for title in self.df['title']:
            words = list(jieba.cut_for_search(title))
            words = [word for word in words if word not in self.stopwords and len(word.strip()) > 0]
            words = [re.sub(r'[^\w\s]', '', word) for word in words]  # 去除中文和英文符号
            all_words.extend(words)

        # 词频统计
        word_freq = Counter(all_words)
        top_words = word_freq.most_common(top_n)

        # 绘制词频柱状图
        plt.figure(figsize=(15, 6))
        words, freqs = zip(*top_words)

        plt.bar(words, freqs)
        plt.title(f'Top {top_n} 高频词')
        plt.xlabel('词语')
        plt.ylabel('出现频率')
        plt.rcParams['font.sans-serif'] = ['SimHei']  # Use SimHei font for Chinese characters
        plt.rcParams['axes.unicode_minus'] = False
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

        # 打印词频信息
        print("高频词及其出现次数:")
        for word, freq in top_words:
            print(f"{word}: {freq}")

    def unique_title_analysis(self):
        """
        唯一性分析
        """
        print("\n===== 唯一性分析 =====")

        # 重复标题分析
        title_counts = self.df['title'].value_counts()
        duplicate_titles = title_counts[title_counts > 1]

        print(f"唯一标题数: {len(self.df['title'].unique())}")
        print(f"重复标题数: {len(duplicate_titles)}")

        if len(duplicate_titles) > 0:
            print("\n重复标题详情:")
            for title, count in duplicate_titles.items():
                print(f"'{title}' 出现 {count} 次")

    def run_eda(self):
        """
        执行全面EDA分析
        """
        self.basic_statistics()
        self.word_frequency_analysis()
        self.unique_title_analysis()

