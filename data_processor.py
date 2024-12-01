import os
import re
import jieba
import emoji
class DataProcessor:
    def __init__(self):

        self.rep = ['@','～', 'hia', '💘','🥰','🥺','🥵','�','❌','⭕',
                    '同性', '同性恋', '说', '!', '…', '想']
        self.patterns = [

            # re.compile(r'@([\u4e00-\u9fa5\w\-]+)'),
            re.compile(r'@[\u4e00-\u9fff\w\-]+'),
            re.compile(r'@\s*[\u4e00-\u9fff\w]+'),
            re.compile(r'@\w+'),
            re.compile(r'[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF]'),
            re.compile(r'<.*?>'),
            re.compile(r'\([^)]*\)'),
            # re.compile("["
            #            u"\U0001F600-\U0001F64F"  # 表情符号
            #            u"\U0001F300-\U0001F5FF"  # 符号与图形
            #            u"\U0001F680-\U0001F6FF"  # 交通工具
            #            u"\U0001F1E0-\U0001F1FF"  # 国旗
            #            u"\U00002702-\U000027B0"
            #            u"\U000024C2-\U0001F251"
            #            "]+", flags=re.UNICODE)
        ]



    def clean(self, text):
        # Clean the data
        for pattern in self.patterns:
            text = pattern.sub('', text)
        for rep in self.rep:
            text = text.replace(rep, '')
        emoji.replace_emoji(text, replace='')
        return text


def clean_data():

    # file_path = "comments/bilibili/merge/"
    file_path = "comments/bilibili/merge_v2/"
    target_path = "comments/bilibili/cleaned_v2/"
    os.makedirs(target_path, exist_ok=True)
    for file in os.listdir(file_path):
        with open(file_path + file, 'r', encoding='utf-8') as f:
            text = f.read()
            cleaned_text = data_processor.clean(text)
        file_name = f"{target_path}CLEANED__{file}"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
            print(f"[{file}]  清洗成功")


def main():
    global data_processor
    data_processor = DataProcessor()
    # 读取指定文件夹进行文本清洗
    clean_data()
    # 分词
    # jieba.load_userdict('comments/bilibili/processed/user_dict.txt')


if __name__ == "__main__":
    main()

