import os
import jieba
import json
import logging
from typing import List, Optional

class BatchTokenizer:
    def __init__(self,
                 input_dir: str,
                 output_dir: str,
                 mode: str = 'precise',
                 remove_stopwords: bool = True,
                 custom_words: Optional[List[str]] = None,
                 custom_dict: Optional[List[str]] = None):
        """
        批量分词处理器

        参数:
        - input_dir: 输入文件夹路径
        - output_dir: 输出文件夹路径
        - mode: 分词模式 ('precise', 'all', 'search')
        - remove_stopwords: 是否去除停用词
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.mode = mode
        self.remove_stopwords = remove_stopwords

        self.custom_words = set(custom_words) if custom_words else set()

        # 设置日志
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 加载停用词
        self.stopwords = self._load_stopwords()

        for word in custom_dict:
            jieba.add_word(word)

    def _load_stopwords(self) -> set:
        """
        加载停用词（来源：https://github.com/CharyHong/Stopwords/blob/main/stopwords_cn.txt）
        """
        stopwords_file = 'resources/stopwords_cn.txt'
        with open(stopwords_file, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)

    def tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词处理

        参数:
        - text: 输入文本

        返回:
        分词后的列表
        """
        # 根据模式选择分词方法
        if self.mode == 'all':
            words = list(jieba.cut(text, cut_all=True))
        elif self.mode == 'search':
            words = list(jieba.cut_for_search(text))
        else:  # precise模式
            words = list(jieba.cut(text, cut_all=False))

        # 是否去除停用词
        if self.remove_stopwords:
            words = [word for word in words
                     if word.strip() and word not in self.stopwords]

        # 去除自定义词
        words = [word for word in words if word not in self.custom_words]
        return words

    def process_file(self, input_file: str, output_file: str):
        """
        处理单个文件的分词

        参数:
        - input_file: 输入文件路径
        - output_file: 输出文件路径
        """
        try:
            # 读取输入文件
            with open(input_file, 'r', encoding='utf-8') as f:
                # 假设文件是JSON格式的评论列表
                comments = json.load(f).get('commentsInfo')

            # 存储分词结果
            tokenized_results = []

            # 遍历每条评论
            for idx, comment in enumerate(comments, 1):
                # 分词处理
                tokenized_comment = self.tokenize(comment)
                tokenized_results.append({
                    'id': idx,
                    'original': comment,
                    'tokens': tokenized_comment
                })

                # 进度日志
                if idx % 1000 == 0:
                    self.logger.info(f'已处理 {idx} 条评论')

            # 写入输出文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tokenized_results, f,
                          ensure_ascii=False,
                          indent=2)

            self.logger.info(f'文件 {input_file} 分词处理完成, 结果已保存到 {output_file}')

        except Exception as e:
            self.logger.error(f'处理文件 {input_file} 时发生错误: {e}')

    def batch_process(self):
        """
        批量处理文件夹中的所有文件
        """
        # 遍历输入目录
        for filename in os.listdir(self.input_dir):
            # 只处理JSON文件
            if filename.endswith('.json'):
                input_path = os.path.join(self.input_dir, filename)
                output_filename = f'TOKENIZED_{filename}'
                output_path = os.path.join(self.output_dir, output_filename)

                self.logger.info(f'开始处理文件: {filename}')
                self.process_file(input_path, output_path)

def main():
    custom_words = ['同性', '同性恋', '说', '!', '…', '想', '异性恋', '异性', '男', '女', 'txl', '性别', '￴', '‍', '❤']
    custom_dict = ['妈的', '你俩', '评论区', '尬笑']
    tokenizer = BatchTokenizer(
        # input_dir='comments/bilibili/categorized/cleaned/homo_cleaned/',
        # output_dir='comments/bilibili/categorized/tokenized/homo_tokenized/',
        input_dir='comments/bilibili/cleaned_v2',
        # input_dir='comments/douyin/cleaned',
        output_dir='comments/bilibili/tokenized_v3',
        # output_dir='comments/douyin/tokenized',

        mode='precise',  # 分词模式
        remove_stopwords=True,  # 是否去除停用词
        custom_words=custom_words,
        custom_dict=custom_dict

    )

    # 执行批量分词
    tokenizer.batch_process()

if __name__ == '__main__':
    main()
