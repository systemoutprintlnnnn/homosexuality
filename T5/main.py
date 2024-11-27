import torch
from transformers import T5Tokenizer, T5Config, T5ForConditionalGeneration

example_dict={
    "文本分类":{"text_a":"钢琴块3别踩白块儿3钢琴块3是一款简洁的钢琴模拟软件,在Android平台上,类似的软件还是比较多的。","choices":["相机","影视娱乐","棋牌中心","新闻","财经","策略","休闲益智","教育"]},
    '新闻分类':{"text_a":"微软披露拓扑量子计算机计划！","choices":["故事","文化","娱乐","体育","财经","房产","汽车","教育","科技"]},
    '情感分析':{"text_a":"刚买iphone13 pro 还不到一个月，天天死机最差的一次购物体验","choices":["好评","差评"]},
    '意图识别':{"text_a":"打电话给吴小军。","choices":["放音乐","播放下一首","打电话","退出导航","开始导航","其他","暂停音乐","导航","开导航"]},

    '语义匹配':{"text_a":"今天心情不好","text_b":"我很不开心","choices":["相似","不相似"]},
    '自然语言推理':{"text_a":"小明正在上高中","text_b":"小明是一个初中生","choices":["无关","矛盾","蕴含"]},

    '多项选择':{"text_a":"这大家千万不能着急，我们现在只是暂时输了7分。距离比赛结束还有20多分钟呢，我们是完全有机会转败为赢的，大家加油!","question":"说话人希望大家：","choices":["别得意","冷静一些","加快速度","提前预习"]},
    '指代消解':{"text_a":"李鸣觉得董客这人，踏实得叫人难受。可因为孟野和森森太疯，他只好去找董客聊天，但在董客眼里，李鸣也是不正常，他竟然放着现成的大学不愿上。","question":"【他】指的是【李鸣】吗？","choices":["是","不是"]},

    '实体识别':{"text_a":"北京大学是我国的一座历史名校，坐落在海淀区，蔡元培曾经担任校长","question":"机构"},
    '抽取式阅读理解':{"text_a":"《H》正式定档3月7日下午两点整在京东商城独家平台开启第一批5000份预售,定价230元人民币,回馈最忠实的火星歌迷,意在用精品回馈三年来跟随华晨宇音乐不离不弃的粉丝们的支持与厚爱","question":"华晨宇专辑h预售价格是多少？"},
    '关键词抽取':{"text_a":"今儿在大众点评，找到了口碑不错的老茶故事私房菜。"},

    "生成式摘要":{"text_a":"针对传统的流量分类管理系统存在不稳定、结果反馈不及时、分类结果显示不直观等问题,设计一个基于web的在线的流量分类管理系统.该系统采用流中前5个包(排除3次握手包)所含信息作为特征值计算资源,集成一种或多种分类算法用于在线网络流量分类,应用数据可视化技术处理分类结果.实验表明:在采用适应在线分类的特征集和c4.5决策树算法做分类时,系统能快速做出分类,且精度达到94％以上;数据可视化有助于人机交互,改善分类指导."}
}


# 构造prompt的过程中，verbalizer这个占位key的内容，是通过 "/".join(choices) 拼接起来
dataset2instruction = {
    "情感分析": {
        "prompt": "{}任务：【{}】这篇文章的情感态度是什么？{}",
        "keys_order": ["subtask_type","text_a", "verbalizer"],
        "data_type": "classification",
    },
    "文本分类": {
        "prompt": "{}任务：【{}】这篇文章的类别是什么？{}",
        "keys_order": ["subtask_type","text_a", "verbalizer"],
        "data_type": "classification",
    },
    "新闻分类": {
        "prompt": "{}任务：【{}】这篇文章的类别是什么？{}",
        "keys_order": ["subtask_type","text_a", "verbalizer"],
        "data_type": "classification",
    },
    "意图识别": {
        "prompt": "{}任务：【{}】这句话的意图是什么？{}",
        "keys_order": ["subtask_type","text_a", "verbalizer"],
        "data_type": "classification",
    },
    # --------------------
    "自然语言推理": {
        "prompt": "{}任务：【{}】和【{}】，以上两句话的逻辑关系是什么？{}",
        "keys_order": ["subtask_type","text_a", "text_b", "verbalizer"],
        "data_type": "classification",
    },
    "语义匹配": {
        "prompt": "{}任务：【{}】和【{}】，以上两句话的内容是否相似？{}",
        "keys_order": ["subtask_type","text_a", "text_b", "verbalizer"],
        "data_type": "classification",
    },
    # -----------------------
    "指代消解": {
        "prompt": "{}任务：文章【{}】中{}{}",
        "keys_order": ["subtask_type","text_a", "question", "verbalizer"],
        "data_type": "classification",
    },
    "多项选择": {
        "prompt": "{}任务：阅读文章【{}】问题【{}】？{}",
        "keys_order": ["subtask_type","text_a", "question", "verbalizer"],
        "data_type": "classification",
    },
    # ------------------------
    "抽取式阅读理解": {
        "prompt": "{}任务：阅读文章【{}】问题【{}】的答案是什么？",
        "keys_order": ["subtask_type","text_a", "question"],
        "data_type": "mrc",
    },
    "实体识别": {
        "prompt": "{}任务：找出【{}】这篇文章中所有【{}】类型的实体？",
        "keys_order": ["subtask_type","text_a", "question"],
        "data_type": "ner",
    },
    # ------------------------
    "关键词抽取": {
        "prompt": "{}任务：【{}】这篇文章的关键词是什么？",
        "keys_order": ["subtask_type","text_a"],
        "data_type": "keys",
    },
    "关键词识别":{
        "prompt": "{}任务：阅读文章【{}】问题【{}】{}",
        "keys_order": ["subtask_type","text_a","question","verbalizer"],
        "data_type": "classification",
    },
    "生成式摘要": {
        "prompt": "{}任务：【{}】这篇文章的摘要是什么？",
        "keys_order": ["subtask_type","text_a"],
        "data_type": "summ",
    },
}

def get_instruction(sample):

    template = dataset2instruction[sample["新闻分类"]]
    # print(template)
    # print(sample)
    sample["instruction"] = template["prompt"].format(*[
        sample[k] for k in template["keys_order"]
    ])

    print(sample["instruction"])

    return sample["instruction"]



# load tokenizer and model
# pretrained_model = "IDEA-CCNL/Randeng-T5-77M-MultiTask-Chinese"
pretrained_model = "D:\ADATA\PycharmProject\Homosexuality\T5"

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

# tokenize
# text = "情感分析任务：【房间还是比较舒适的,酒店服务良好】这篇文章的情感态度是什么？正面/负面"
# text = "新闻分类任务：【微软披露拓扑量子计算机计划！】这篇文章的类别是什么？'故事','文化','娱乐','体育','财经','房产','汽车','教育','科技'"
comments = "'川哥的歌喉让我乱七八糟的', '碳水够了，就是缺点蛋白质', '去吧，AI铁人大军\n@机器工具人   听歌识曲\n@有趣的程序员  总结一下\n@AI视频小助理   总结一下\n@课代表猫   总结一下\n@AI课代表呀 总结一下\n@木几萌Moe 总结一下\n@星崽丨StarZai 总结内容\n@星崽丨StarZai 提取图片\n@AI识片酱 视频总结\n@AI沈阳美食家 笑点解析\n@AI全文总结 总结文本', '老哥还需要人吗，找不到工地活干了[笑哭]', '肚子饿遭了，吃个面包，带一桶丸子工地吃，不错', '沙发，川哥加油[打call]', '支持川哥[打call][打call][打call][打call]', '面包加丸子，吃了就饿掉，一吃管不久，一下就饿了[doge]', '--本内容由 @红尘太平人 大佬下凡召唤，热心市民@AI视频小助理闪现赶来\n本视频讲述了作者在工地辛勤工作了一上午，到了中午最开心的时刻就是走去吃饭。他今天中午没有做饭，而是来了一桶精品鱼丸，加点豆瓣酱和香葱，还有牛肉丸、火锅丸、潮汕丸和福州鱼丸等。最后，他呼吁浪迹天涯的游子们归来吧，感受故乡的泥土芬芳。\n实名羡慕up这溢出屏幕的才华[点赞][点赞][点赞]，YYDS！快来一键三连吧[热词系列_优雅]', '这一碗碗的看的好香哦[星星眼][星星眼][星星眼]', '[打call][打call][打call]', '来了[呲牙][呲牙][呲牙]', '没吃米饭呀，可以吃饱吗', '[打call]', '呜呜呜还没吃饭呢，还不知道吃啥', '很快哈', '为啥不直接把辣酱倒进保温桶里 摇一摇更入味', '第一[喜欢]', '下饭视频来了', '哎，房地产的阵痛', '祝川哥越来越好[打call]', '感觉你大儿子是真的不行，在家全职自媒体，拍的还是川哥去打工，合着自己是啥也不用干。一般到川哥这个年纪还干工地活的不多了。还天天嫌你们催婚，自己三十多了，弟弟还小，父母享受天伦之乐不就靠你个大的吗，是一点谱都没有', '丸子面包没营养啊'"
text = f"生成式摘要任务：【{comments}】这篇文章的摘要是什么？"

encode_dict = tokenizer(text, max_length=10240, padding='max_length',truncation=True)
# encode_dict = tokenizer(text, max_length=512, padding='max_length',truncation=True)

inputs = {
    "input_ids": torch.tensor([encode_dict['input_ids']]).long(),
    "attention_mask": torch.tensor([encode_dict['attention_mask']]).long(),
}

# generate answer
logits = model.generate(
    input_ids = inputs['input_ids'],
    max_length=100,
    early_stopping=True,
    num_beams=10
)

logits=logits[:,1:]
predict_label = [tokenizer.decode(i,skip_special_tokens=True) for i in logits]
print(predict_label)

# model output: 正面

