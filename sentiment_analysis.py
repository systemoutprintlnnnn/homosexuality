import time
from threading import Lock

from aip import AipNlp


class SentimentAnalysis:
    _last_request_time = 0
    _lock = Lock()

    def __init__(self):
        APP_ID = '116434783'
        API_KEY = '84WTMbNN6Bj2Ia7XyF8eZiBb'
        SECRET_KEY = 'sD4oI3vSUtr1P7s59jrCndhxOsfOkogZ'
        client = AipNlp(APP_ID, API_KEY, SECRET_KEY)
        self.client = client

    def sentiment_classify(self, text):
        """ 调用情感倾向分析 """
        res = self.client.sentimentClassify(text)
        with self._lock:
            current_time = time.time()
            if current_time - self._last_request_time < 0.06:
                time.sleep(0.06 - (current_time - self._last_request_time))
            self._last_request_time = time.time()
            res = self.client.sentimentClassify(text)
        return res


if __name__ == "__main__":
    s = SentimentAnalysis()
    # res = s.sentiment_classify('我今天很开心')
    print(s.sentiment_classify('喜欢'))