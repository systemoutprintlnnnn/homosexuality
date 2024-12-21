import json
import math
import os
import sys
import time

from gensim import corpora
from gensim.models import LdaModel, CoherenceModel, LdaMulticore
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis
import matplotlib.pyplot as plt
import multiprocessing
from wordcloud import WordCloud
from sentiment_analysis import SentimentAnalysis

# 重定向print输出到文件

output_file = f"lda/logs_new/test____lda_output_female_to_homo.log"
log_file = open(output_file, 'w', encoding='utf-8')
sys.stdout = log_file


# 加载分词文件
def load_tokenized_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        res = [item['tokens'] for item in data]
        print(f"分词文件来源: {file_path}")
    return res


# 构建词典及向量空间
def build_dictionary_and_corpus(tokenized_data):
    # 构建词典
    dictionary = corpora.Dictionary(tokenized_data)
    # 构建向量空间
    corpus = [dictionary.doc2bow(text) for text in tokenized_data]
    print(f"成功构建词典和向量空间")
    return dictionary, corpus


# 训练LDA模型
def train_lda_model(corpus, dictionary, num_topics=20, passes=15, iteration=3000, eta=0.01):
    # print(f"开始训练LDA模型，主题数: {num_topics}")
    # lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=num_topics, passes=passes)
    lda_model = LdaMulticore(corpus=corpus, id2word=dictionary, num_topics=num_topics)
    return lda_model


# 输出LDA模型的主题和相关词语
def print_lda_topics(lda_model, num_words=10):
    for idx, topic in lda_model.print_topics(num_words=num_words):
        print(f"Topic #{idx}: {topic}")


# 可视化LDA模型
def visualize_lda_model(lda_model, corpus, dictionary):
    vis_data = gensimvis.prepare(lda_model, corpus, dictionary)
    os.makedirs("lda", exist_ok=True)
    for i in range(1, 100):
        lda_path = f"lda/lda_html/lda_{i}.html"
        # 如果文件名存在则i++
        if os.path.exists(lda_path):
            continue
        else:
            pyLDAvis.save_html(vis_data, lda_path)
            break
    return lda_path


# 计算困惑度和一致性
def evaluate_lda_model(lda_model, corpus, dictionary, texts):
    log_perplexity = lda_model.log_perplexity(corpus)
    perplexity = math.exp(log_perplexity)
    coherence_model_lda = CoherenceModel(model=lda_model, texts=texts, dictionary=dictionary, coherence='c_v')
    coherence = coherence_model_lda.get_coherence()
    return perplexity, coherence


def show_plot(perplexities, coherences, min_topics, max_topics, step):
    # 困惑度曲线
    plt.subplot(1, 2, 1)
    plt.plot(range(min_topics, max_topics + 1, step), perplexities, marker='o')
    plt.title("Perplexity Scores")
    plt.xlabel("Number of Topics")
    plt.ylabel("Perplexity")
    # 一致性曲线
    plt.subplot(1, 2, 2)
    plt.plot(range(min_topics, max_topics + 1, step), coherences, marker='o', color='green')
    plt.title("Coherence Scores")
    plt.xlabel("Number of Topics")
    plt.ylabel("Coherence Score")
    plt.tight_layout()
    for i in range(1, 100):
        output_file = f"lda/plot_v2/perplexity_coherence_{i}.png"
        # 如果文件名存在则i++
        if os.path.exists(output_file):
            continue
        else:
            plt.savefig(output_file, format='png')
            print(f"困惑度、一致性曲线保存至: {output_file}")
            break
    plt.show()


def find_best_lda_model(min_topics, max_topics, step):
    # global best_lda_model, perplexities, coherences, min_topics, max_topics, step
    best_num_topics = 0
    best_coherence = float('-inf')
    best_lda_model = None
    perplexities = []
    coherences = []

    for num_topics in range(min_topics, max_topics + 1, step):
        lda_model = train_lda_model(corpus, dictionary, num_topics=num_topics)
        perplexity, coherence = evaluate_lda_model(lda_model, corpus, dictionary, tokenized_data)
        print(f"主题数: {num_topics}, 困惑度: {perplexity}, 一致性: {coherence}")
        perplexities.append(perplexity)
        coherences.append(coherence)

        if coherence > best_coherence:
            best_coherence = coherence
            best_num_topics = num_topics
            best_lda_model = lda_model
    print(f"最佳主题数: {best_num_topics}, 最佳一致性: {best_coherence}")
    # 输出最佳LDA模型的主题和相关词语
    print_lda_topics(best_lda_model)
    return best_lda_model, perplexities, coherences


def generate_wordcloud(lda_model, topic_id, num_words=50):
    # 获取指定主题的词语及其权重
    topic_words = lda_model.show_topic(topic_id, topn=num_words)
    word_freq = {word: weight for word, weight in topic_words}

    font_path = 'C:/Windows/Fonts/simhei.ttf'
    wordcloud = WordCloud(width=800, height=400, background_color='white',
                          font_path=font_path).generate_from_frequencies(word_freq)

    # 显示词云图
    plt.figure()
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'Topic #{topic_id}')
    # 保存词云图
    # output_file = f"lda/wordcloud_{topic_id}.png"
    for i in range(1, 10000):
        output_file = f"lda/wordcloud_v4/wordcloud_{i}.png"
        # 如果文件名存在则i++
        if os.path.exists(output_file):
            continue
        else:
            plt.savefig(output_file, format='png')
            break

    plt.show()

    return output_file


def calculate_sentiment_score(lda_model, num_topics, num_words):
    sentiment_analyzer = SentimentAnalysis()
    topic_sentiments = {}

    for topic_id in range(num_topics):
        print(f"计算主题#{topic_id}的情感倾向评分")
        topic_words = lda_model.show_topic(topic_id, topn=num_words)

        sentiment_score = 0

        scores = []
        for word, weight in topic_words:

            sentiment_result = sentiment_analyzer.sentiment_classify(word)
            if 'items' not in sentiment_result or sentiment_result['items'] is None:
                while True:
                    if sentiment_result['error_code'] == 18:
                        time.sleep(0.1)
                        sentiment_result = sentiment_analyzer.sentiment_classify(word)
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
            # 计算情感评分
            if positive_prob > negative_prob:
                score = positive_prob * confidence
                # score = positive_prob
            elif positive_prob < negative_prob:
                score = -negative_prob * confidence
                # score = -negative_prob
            else:
                score = 0.5
            scores.append({'weight': weight, 'score': score, 'confidence': confidence})
            # if sentiment == 2:  # positive
            #     score = positive_prob * confidence
            # elif sentiment == 0:  # negative
            #     score = -negative_prob * confidence
            # else:  # neutral
            #     score = 0

        # 加权平均
        total_weight = 0
        total_confidence = 0
        for t in scores:
            total_weight += t['weight']
            total_confidence += t['confidence']
        avg_confidence = total_confidence / len(scores)
        for t in scores:
            w = t['weight']
            s = t['score']
            sentiment_score += (w / total_weight) * s

        topic_sentiments[topic_id] = sentiment_score / avg_confidence

    return topic_sentiments


if __name__ == "__main__":
    num_cores = multiprocessing.cpu_count()
    # 示例用法
    # file_path = 'comments/douyin/tokenized/TOKENIZED_CLEANED__ALL__comments_all.json'
    file_path = 'comments/bilibili/tokenized_v3/TOKENIZED_CLEANED__ALL__comments_all.json'
    # file_path = 'comments/bilibili/tokenized_v3/TOKENIZED_CLEANED__MALE__comments_all.json'
    # file_path = 'comments/bilibili/tokenized_v3/TOKENIZED_CLEANED__UNKNOWN__comments_all.json'
    # file_path = 'comments/bilibili/tokenized_v3/TOKENIZED_CLEANED__FEMALE__comments_all.json'
    # file_path = 'comments/bilibili/categorized/tokenized/female_tokenized/TOKENIZED_CLEANED__FEMALE__comments_to_female.json'
    # file_path = 'comments/bilibili/categorized/tokenized/female_tokenized/TOKENIZED_CLEANED__MALE__comments_to_female.json'
    # file_path = 'comments/bilibili/categorized/tokenized/male_tokenized/TOKENIZED_CLEANED__FEMALE__comments_to_male.json'
    # file_path = 'comments/bilibili/categorized/tokenized/homo_tokenized/TOKENIZED_CLEANED__MALE__comments_to_homo.json'
    # file_path = 'comments/bilibili/categorized/tokenized/homo_tokenized/TOKENIZED_CLEANED__FEMALE__comments_to_homo.json'
    # file_path = 'comments/bilibili/categorized/tokenized/homo_tokenized/TOKENIZED_CLEANED__MALE__comments_to_homo.json'
    tokenized_data = load_tokenized_file(file_path)
    dictionary, corpus = build_dictionary_and_corpus(tokenized_data)

    # # 训练LDA模型
    # lda_model = train_lda_model(corpus, dictionary)
    #
    # # 输出LDA模型的主题和相关词语
    # print_lda_topics(lda_model)

    min_topics = 800
    max_topics = 800
    step = 2

    best_lda_model, perplexities, coherences = find_best_lda_model(min_topics, max_topics, step)
    # 输出困惑度、一致性曲线
    show_plot(perplexities, coherences, min_topics, max_topics, step)

    # 可视化best LDA模型
    p = visualize_lda_model(best_lda_model, corpus, dictionary)
    print(f"最佳LDA模型可视化完成, 保存至: {p}")
    # 最佳LDA模型的主题数
    num_topics = best_lda_model.num_topics

    # 生成词云图
    for topic_id in range(0, num_topics):
        i = 50
        output_path = generate_wordcloud(best_lda_model, topic_id, i)
        print(f"Topic #{topic_id}  {i}词的词云图生成完毕, 保存至: {output_path}")

    # 计算并输出情感倾向评分

    topic_sentiments = calculate_sentiment_score(best_lda_model, num_topics, num_words=i)
    sentiment_scores_sum = 0
    for topic_id, sentiment_score in topic_sentiments.items():
        print(f"Topic #{topic_id} Sentiment Score: {sentiment_score}")
        sentiment_scores_sum += sentiment_score
    print(f"Average Sentiment Score: {sentiment_scores_sum / num_topics}")
    # 关闭日志文件
log_file.close()
