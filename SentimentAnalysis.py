from aip import AipNlp

""" 你的 APPID AK SK """
APP_ID = '116434783'
API_KEY = '84WTMbNN6Bj2Ia7XyF8eZiBb'
SECRET_KEY = 'sD4oI3vSUtr1P7s59jrCndhxOsfOkogZ'

client = AipNlp(APP_ID, API_KEY, SECRET_KEY)

text = "支持同性恋不是让所有人都去找同性，只是希望性爱平等，世间没有歧视，同性恋不是变多了，只是越来越多的人开始关注这个群体，并给予他们鼓励，抵制不能够让这个群体消失，只会让他们伪装或是走上反社会的道路"

""" 调用情感倾向分析 """
res = client.sentimentClassify(text);
print(res)