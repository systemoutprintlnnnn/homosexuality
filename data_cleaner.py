import os
import re
import jieba
import emoji
class DataProcessor:
    def __init__(self):

        self.rep = ['@','～', 'hia', '💘','🥰','🥺','🥵','�','❌','⭕',
                    '同性', '同性恋', '说', '!', '…', '想']
        self.patterns = [
            re.compile(r'@[\u4e00-\u9fff\w\-]+'),
            re.compile(r'@\s*[\u4e00-\u9fff\w]+'),
            re.compile(r'@\w+'),
            re.compile(r'[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF]'),
            re.compile(r'<.*?>'),
            re.compile(r'\([^)]*\)'),
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
    file_path = "comments/bilibili/categorized/merged/homo_merged/"
    file_path = "comments/douyin/merge/"
    # target_path = "comments/bilibili/categorized/cleaned/homo_cleaned/"
    target_path = "comments/douyin/cleaned/"
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



if __name__ == "__main__":
    main()

