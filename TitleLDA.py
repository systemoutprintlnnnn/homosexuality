import pandas as pd
import numpy as np
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import matplotlib.pyplot as plt
from pylab import mpl
import matplotlib.font_manager as fm


class TitleLDA:

    def __init__(self, video_dict, n_topics=5):
        """
        初始化主题模型分析类

        参数:
        video_dict (dict): 包含视频id和标题的字典
        n_topics (int): 要提取的主题数量
        """
        # 转换为DataFrame
        self.df = pd.DataFrame.from_dict(video_dict, orient='index', columns=['title'])
        self.df.index.name = 'video_id'
        self.df.reset_index(inplace=True)

        # 主题数量
        self.n_topics = n_topics

        # 停用词
        self.stopwords = self._load_stopwords()
        mpl.rcParams["axes.unicode_minus"] = False
        mpl.rcParams["font.sans-serif"] = ["SimHei"]

    def visualize_topics(self, topic_keywords):
        """
        可视化主题

        参数:
        topic_keywords (dict): 主题关键词
        """
        # 设置中文字体
        plt.rcParams['font.family']=['SimHei']


        plt.figure(figsize=(15, 5))
        for idx, keywords in topic_keywords.items():
            plt.subplot(1, self.n_topics, idx+1)
            plt.barh(range(len(keywords)), [1]*len(keywords), align='center')
            plt.yticks(range(len(keywords)), keywords)
            plt.title(f'主题 {idx+1}')
            plt.xlabel('重要性')
        plt.tight_layout()
        plt.show()


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
            ' ', '', '视频', ',', '.', '，', '。', '!', '！', '?', '？',
            '、', '：', ':', '《', '》', '“', '”', '【', '】', '（', '）',
            '(', ')', '[', ']', '——', '-', '～', '~', '…', '@', '#',
            '...',
        }
        return basic_stopwords

    def _preprocess_text(self, text):
        """
        文本预处理：分词并去除停用词

        参数:
        text (str): 输入文本

        返回:
        str: 处理后的文本
        """
        # 分词
        words = jieba.cut(text)
        # 去除停用词
        words = [word for word in words if word not in self.stopwords and len(word.strip()) > 0]
        return ' '.join(words)

    def perform_topic_modeling(self, max_df=0.9, min_df=2):
        """
        执行主题建模

        参数:
        max_df (float): 词语文档频率上限
        min_df (int): 词语文档频率下限

        返回:
        dict: 每个主题的关键词
        """
        # 预处理文本
        self.df['processed_title'] = self.df['title'].apply(self._preprocess_text)

        # 文档-词矩阵
        vectorizer = CountVectorizer(
            max_df=max_df,  # 忽略出现在超过90%文档中的词
            min_df=min_df,  # 忽略出现在少于2个文档中的词
        )
        doc_word_matrix = vectorizer.fit_transform(self.df['processed_title'])

        # 获取词汇表
        vocab = vectorizer.get_feature_names_out()

        # LDA主题模型
        lda = LatentDirichletAllocation(
            n_components=self.n_topics,
            random_state=42,
            learning_method='batch'
        )
        lda.fit(doc_word_matrix)

        # 提取每个主题的关键词
        topic_keywords = {}
        for topic_idx, topic in enumerate(lda.components_):
            # 获取当前主题中最重要的10个词
            top_keywords_idx = topic.argsort()[:-10 - 1:-1]
            top_keywords = [vocab[i] for i in top_keywords_idx]
            topic_keywords[topic_idx] = top_keywords

        return topic_keywords

    def visualize_topics(self, topic_keywords):
        """
        可视化主题

        参数:
        topic_keywords (dict): 主题关键词
        """
        plt.figure(figsize=(15, 5))
        for idx, keywords in topic_keywords.items():
            plt.subplot(1, self.n_topics, idx+1)
            plt.barh(range(len(keywords)), [1]*len(keywords), align='center')
            plt.yticks(range(len(keywords)), keywords)
            plt.title(f'主题 {idx+1}')
            plt.xlabel('重要性')
        plt.tight_layout()
        plt.show()

    def assign_topics(self, topic_keywords):
        """
        为每个视频标题分配主题

        参数:
        topic_keywords (dict): 主题关键词

        返回:
        DataFrame: 添加了主题列的DataFrame
        """
        def find_topic(title):
            processed_title = self._preprocess_text(title)
            words = set(processed_title.split())

            # 计算标题与各主题的相似度
            topic_scores = {}
            for topic_idx, keywords in topic_keywords.items():
                topic_words = set(keywords)
                score = len(words.intersection(topic_words)) / len(topic_words)
                topic_scores[topic_idx] = score

            # 返回相似度最高的主题
            return max(topic_scores, key=topic_scores.get)

        # 为每个标题分配主题
        self.df['topic'] = self.df['title'].apply(find_topic)

        return self.df

    def generate_topic_names(self, topic_keywords):
        """
        根据主题关键词生成主题名称建议

        参数:
        topic_keywords (dict): 主题关键词

        返回:
        dict: 主题名称建议
        """
        topic_names = {}
        for topic_idx, keywords in topic_keywords.items():
            # 简单地使用前3个关键词组合作为主题名称
            topic_name = '-'.join(keywords[:3])
            topic_names[topic_idx] = topic_name

        return topic_names

    def run_topic_modeling(self):
        """
        执行完整的主题建模流程

        返回:
        tuple: (主题关键词, 主题名称建议, 带主题的DataFrame)
        """
        # 执行主题建模
        topic_keywords = self.perform_topic_modeling()

        # 可视化主题
        self.visualize_topics(topic_keywords)

        # 生成主题名称建议
        topic_names = self.generate_topic_names(topic_keywords)

        # 打印主题关键词和建议名称
        print("主题关键词和建议名称:")
        for topic_idx, keywords in topic_keywords.items():
            print(f"主题 {topic_idx}: {topic_names[topic_idx]}")
            print("关键词:", ', '.join(keywords))
            print()

        # 为标题分配主题
        df_with_topics = self.assign_topics(topic_keywords)

        return topic_keywords, topic_names, df_with_topics
