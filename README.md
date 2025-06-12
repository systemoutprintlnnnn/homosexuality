
# Social Media Attitudes Analysis: Gender and Homosexuality

本项目旨在通过分析中国主流社交媒体平台（Bilibili、抖音）的用户评论数据，研究不同性别用户对不同类型同性恋（男性同性恋、女性同性恋）的态度差异。项目采用数据抓取、自然语言处理（NLP）、主题建模和情感分析等技术，构建了一个完整的数据分析流水线。

---

## 核心发现

通过对Bilibili（约24万条评论）和抖音（约13万条评论）的数据进行分析，我们得出了以下初步结论：

- **平台差异**：总体而言，Bilibili用户对同性恋议题的情感倾向比抖音用户更积极。
- **性别与态度关联**：在Bilibili平台，我们观察到明显的性别偏好差异：
  - **男性用户**对男性同性恋（Gay）的接纳度高于女性同性恋（Lesbian）。
  - **女性用户**对女性同性恋（Lesbian）的接纳度则显著高于男性同性恋（Gay）。
- **数据驱动**：本研究证实了通过大规模社交媒体数据来量化和分析社会群体对特定议题态度的可行性。

## 项目架构

- **Controller Layer (控制层)**: 基于 **Flask** 构建的轻量级API服务。作为系统的入口，负责接收和处理HTTP请求，并将处理结果返回给用户。
- **Service Layer (服务层)**: 项目的核心业务逻辑层。包含了数据采集、预处理、清洗、分词、LDA主题建模、词云生成和情感分析等多个功能组件。
- **Persistence Layer (持久化层)**: 使用 **JSON** 文件作为中间数据存储，用于在数据处理流程中高效地传递和暂存数据。
- **Database Layer (数据库层)**: 采用 **MongoDB** 作为主要的数据库。其NoSQL特性非常适合存储和管理从网络上抓取的非结构化/半结构化评论数据。
![image](https://github.com/user-attachments/assets/90f6d4a9-9368-428a-ad99-66ae9e48e3a5)

## 技术流水线 (Methodology)

项目的数据处理和分析流程遵循以下步骤：

1.  **数据采集 (Data Collection)**:
    - 使用定制化的Web爬虫脚本，针对Bilibili和抖音平台，根据关键词（如同性恋、gay、les）搜索相关视频。
    - 抓取视频的元数据（如标题、标签、aid/aweme_id）以及其下方的用户评论。
    - 原始数据实时存入 **MongoDB** 数据库，以应对网络不稳定和抓取中断的风险。

2.  **数据预处理 (Data Preprocessing)**:
    - 从MongoDB中导出原始数据。
    - 根据视频的标题和标签，将其分为“男性同性恋”、“女性同性恋”和“泛同性恋”三个类别。
    - 对Bilibili平台的用户评论，根据其公开的性别信息进行分类（男、女、未知）。（注：抖音无法直接获取用户性别信息）。

3.  **数据清洗 (Data Cleaning)**:
    - 移除文本中的噪声数据，如`@username`提及、HTML标签、Unicode表情符号（Emojis）等。
    - 标准化中英文标点符号，并处理多余的换行符和空格。

4.  **中文分词 (Tokenization)**:
    - 使用 **Jieba** 分词库对清洗后的评论文本进行分词。
    - 加载了停用词表（Stopwords）以移除无实际意义的词语（如“的”、“是”、“了”等），并移除了自定义的无关词，以提高后续分析的准确性。

5.  **主题建模 (Topic Modeling)**:
   ![image](https://github.com/user-attachments/assets/939316f0-d143-4d15-9e32-7859066ea707)
    - 使用 **Gensim** 库实现Latent Dirichlet Allocation (LDA) 模型。
    - 通过计算不同主题数量下的**困惑度 (Perplexity)** 和 **一致性 (Coherence)** 指标，确定最优的主题数量，以确保模型的可解释性和有效性。

7.  **情感分析 (Sentiment Analysis)**:
    - 对每个LDA主题下的高频词，调用**百度智能云NLP情感倾向分析API**进行打分。
    - API返回`positive_prob`（积极概率）、`negative_prob`（消极概率）和`confidence`（置信度）。
    - 根据以下公式计算每个主题的加权情感分数，最终得到各类用户群体的整体情感倾向值：
![image](https://github.com/user-attachments/assets/9150825c-9517-4a07-ae02-6bd924796adb)

![image](https://github.com/user-attachments/assets/ef5073bf-6630-4cf8-936f-9b566470197a)

![image](https://github.com/user-attachments/assets/a8f6ece5-314e-479d-8418-6b3d2025686f)

## 技术栈

- **编程语言**: Python 3
- **Web框架**: Flask
- **数据库**: MongoDB
- **NLP/数据分析**:
  - `jieba`: 中文分词
  - `gensim`: LDA主题建模
  - `pandas`: 数据处理
  - `wordcloud`: 词云可视化
- **API**: 百度智能云情感分析API
- **其他**: `requests`, `pymongo`

## 如何运行

### 1. 先决条件

- Python 3.8+
- 安装并运行 MongoDB 服务
- 获取百度智能云的情感分析 API Key 和 Secret Key

### 2. 环境设置

```bash
# 克隆项目到本地
git clone https://github.com/systemoutprintlnnnn/homosexuality.git
cd homosexuality

# (推荐) 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

在项目根目录下创建一个 `config.py` 文件，并填入你的配置信息：

```python
# config.py

# MongoDB 配置
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "social_media_data"

# 百度云 NLP API 配置
BAIDU_API_KEY = "YOUR_BAIDU_API_KEY"
BAIDU_SECRET_KEY = "YOUR_BAIDU_SECRET_KEY"
```

### 4. 运行流水线

你可以按顺序执行以下脚本来复现整个流程（请根据你的实际文件名进行调整）：

```bash
# 步骤 1: 运行爬虫抓取数据
python scraper.py

# 步骤 2: 运行数据预处理和分析脚本
python analysis_pipeline.py

# 步骤 3: (可选) 启动Flask API服务查看结果
flask run
```

## 局限性与未来工作

- **数据清洗**：抖音评论中包含大量非标准的符号和表情，目前的清洗策略仍有待加强，未来可以引入更专业的表情符号情感分析库。
- **数据获取**：抖音平台无法获取用户性别，限制了在该平台上的性别维度分析。
- **计算资源**：受限于本地计算资源（RAM），LDA模型的主题数量设置得相对保守。在更强大的服务器上可以探索更多主题的可能性。
- **平台扩展**：未来的研究可以扩展到微博、知乎等其他社交平台，以获得更全面的图景。
- **模型验证**：情感分析的准确性依赖于第三方API，未来可以通过交叉验证或自建模型来提高结果的稳健性。

## 致谢

本项目参考了以下优秀的开源项目，特此感谢：

- [Nemo2011/bilibili-api](https://github.com/Nemo2011/bilibili-api)
- [SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)
- [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)
- [CharyHong/Stopwords](https://github.com/CharyHong/Stopwords)
