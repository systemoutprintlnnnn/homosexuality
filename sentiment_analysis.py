from aip import AipNlp


class SentimentAnalysis:
    def __init__(self):
        APP_ID = '116434783'
        API_KEY = '84WTMbNN6Bj2Ia7XyF8eZiBb'
        SECRET_KEY = 'sD4oI3vSUtr1P7s59jrCndhxOsfOkogZ'
        client = AipNlp(APP_ID, API_KEY, SECRET_KEY)
        self.client = client

    def sentiment_classify(self, text):
        """ 调用情感倾向分析 """
        res = self.client.sentimentClassify(text)
        return res
