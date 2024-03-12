from flask import Flask, request, abort
import os
import json
import requests
import cfg
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# 設置LINE Bot的API URL和Token
LINE_API_URL = "https://api.line.me/v2/bot/message/reply"
LINE_ACCESS_TOKEN = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
LINE_SECRET = os.getenv('CHANNEL_SECRET')
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 設置OpenAI API的URL和密鑰
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


@app.route("/")
def welcome():
    return "welcome to my flask web service"


@app.route("/t")
def test():
    return "testing page"


@app.route('/webhook', methods=['POST'])
def webhook():
    # 接收LINE Bot的請求
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        # 驗證 Webhook 請求是否來自 LINE 平臺
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 如果不是來自 LINE 平臺的 Webhook 請求，則拋出錯誤
        abort(400)

    # 如果是來自 LINE 平臺的 Webhook 請求，則處理訊息事件
    events = json.loads(body)["events"]
    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            # 取得使用者 ID 和訊息內容
            user_id = event["source"]["userId"]
            message_text = event["message"]["text"]

            # 調用OpenAI API進行文本生成
            response = generate_text(message_text)

            # 回復用戶的消息
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + LINE_ACCESS_TOKEN
            }
            data = {
                'replyToken': event['replyToken'],
                'messages': [{
                    'type': 'text',
                    'text': response
                }]
            }
            requests.post(LINE_API_URL, headers=headers, data=json.dumps(data))

    return 'OK', 200


def generate_text(prompt):
    # 設置OpenAI API請求的數據
    data = {
        'prompt': prompt,
        'temperature': 0.5,
        'max_tokens': 500,
        "model": "davinci",
        'stop': '\n',
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + OPENAI_API_KEY
    }

    # 發送OpenAI API請求
    response = requests.post(cfg.OPENAI_ENDPOINT, headers=headers, json=data)
    response_data = json.loads(response.content)

    # 解析OpenAI API的響應數據
    message = response_data['choices'][0]['text'].strip()
    return message


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    # app.run()
