from flask import Flask, request, jsonify
import torch
from transformers import T5Tokenizer, T5Config, T5ForConditionalGeneration


app = Flask(__name__)

# Load tokenizer and model
pretrained_model = "D:\\ADATA\\PycharmProject\\Randeng-T5-77M-MultiTask-Chinese"
special_tokens = ["<extra_id_{}>".format(i) for i in range(100)]
tokenizer = T5Tokenizer.from_pretrained(
    pretrained_model,
    do_lower_case=True,
    max_length=512,
    truncation=True,
    additional_special_tokens=special_tokens,
)

config = T5Config.from_pretrained(pretrained_model)
model = T5ForConditionalGeneration.from_pretrained(pretrained_model, config=config)
model.resize_token_embeddings(len(tokenizer))
model.eval()

# Define the dataset2instruction dictionary
dataset2instruction = {
    "情感分析": {
        "prompt": "{}任务：【{}】这篇文章的情感态度是什么？{}",
        "keys_order": ["subtask_type", "text_a", "verbalizer"],
        "data_type": "classification",
    },
    "文本分类": {
        "prompt": "{}任务：【{}】这篇文章的类别是什么？{}",
        "keys_order": ["subtask_type", "text_a", "verbalizer"],
        "data_type": "classification",
    },
    "新闻分类": {
        "prompt": "{}任务：【{}】这篇文章的类别是什么？{}",
        "keys_order": ["subtask_type", "text_a", "verbalizer"],
        "data_type": "classification",
    },
    "意图识别": {
        "prompt": "{}任务：【{}】这句话的意图是什么？{}",
        "keys_order": ["subtask_type", "text_a", "verbalizer"],
        "data_type": "classification",
    },
    "自然语言推理": {
        "prompt": "{}任务：【{}】和【{}】，以上两句话的逻辑关系是什么？{}",
        "keys_order": ["subtask_type", "text_a", "text_b", "verbalizer"],
        "data_type": "classification",
    },
    "语义匹配": {
        "prompt": "{}任务：【{}】和【{}】，以上两句话的内容是否相似？{}",
        "keys_order": ["subtask_type", "text_a", "text_b", "verbalizer"],
        "data_type": "classification",
    },
    "指代消解": {
        "prompt": "{}任务：文章【{}】中{}{}",
        "keys_order": ["subtask_type", "text_a", "question", "verbalizer"],
        "data_type": "classification",
    },
    "多项选择": {
        "prompt": "{}任务：阅读文章【{}】问题【{}】？{}",
        "keys_order": ["subtask_type", "text_a", "question", "verbalizer"],
        "data_type": "classification",
    },
    "抽取式阅读理解": {
        "prompt": "{}任务：阅读文章【{}】问题【{}】的答案是什么？",
        "keys_order": ["subtask_type", "text_a", "question"],
        "data_type": "mrc",
    },
    "实体识别": {
        "prompt": "{}任务：找出【{}】这篇文章中所有【{}】类型的实体？",
        "keys_order": ["subtask_type", "text_a", "question"],
        "data_type": "ner",
    },
    "关键词抽取": {
        "prompt": "{}任务：【{}】这篇文章的关键词是什么？",
        "keys_order": ["subtask_type", "text_a"],
        "data_type": "keys",
    },
    "关键词识别": {
        "prompt": "{}任务：阅读文章【{}】问题【{}】{}",
        "keys_order": ["subtask_type", "text_a", "question", "verbalizer"],
        "data_type": "classification",
    },
    "生成式摘要": {
        "prompt": "{}任务：【{}】这篇文章的摘要是什么？",
        "keys_order": ["subtask_type", "text_a"],
        "data_type": "summ",
    },
}


def get_instruction(sample):
    template = dataset2instruction[sample["subtask_type"]]
    sample["instruction"] = template["prompt"].format(*[
        sample[k] for k in template["keys_order"]
    ])
    return sample["instruction"]


"""
分类接口

参数:
    task_type (str): 子任务类型
    text (str): 待分类文本
"""


@app.route('/categorize', methods=['POST'])
def categorize():
    data = request.json
    task_type = data.get("task_type")
    text = data.get("text")

    # subtask_type = data.get("subtask_type")
    # text_a = data.get("text_a")
    # text_b = data.get("text_b", "")
    # question = data.get("question", "")
    choices = ["故事", "文化", "娱乐", "体育", "财经", "房产", "汽车", "教育", "科技"]

    if not task_type or not text:
        return jsonify({"error": "task_type and text are required"}), 400
    if task_type not in "新闻分类":
        return jsonify({"error": "task_type not supported"}), 400
    instruction = f"{task_type}任务：【{text}】这篇文章的类别是什么？{'/'.join(choices)}"
    text = "新闻分类任务：【微软披露拓扑量子计算机计划！】这篇文章的类别是什么？'故事','文化','娱乐','体育','财经','房产','汽车','教育','科技'"

    # sample = {
    #     "subtask_type": subtask_type,
    #     "text_a": text_a,
    #     "text_b": text_b,
    #     "question": question,
    #     "verbalizer": "/".join(choices)
    # }

    # instruction = get_instruction(sample)

    encode_dict = tokenizer(instruction, max_length=512, padding='max_length', truncation=True)
    inputs = {
        "input_ids": torch.tensor([encode_dict['input_ids']]).long(),
        "attention_mask": torch.tensor([encode_dict['attention_mask']]).long(),
    }

    logits = model.generate(
        input_ids=inputs['input_ids'],
        max_length=100,
        early_stopping=True,
    )

    logits = logits[:, 1:]
    predict_label = [tokenizer.decode(i, skip_special_tokens=True) for i in logits]
    return jsonify({"prediction": predict_label})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
