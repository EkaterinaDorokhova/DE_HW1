# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import requests
import csv
import os
import json

from yandex_cloud_ml_sdk import YCloudML

# Инициализация и настройки
TELEGRAM_TOKEN = "7151965357:AAFpyYFg6mBcteEuXhp8gQLwbRuSS6pxEG0"
IAM_TOKEN ="t1.9euelZqYkZnIk8uVnIyQz5GSjZeMj-3rnpWampuXzJ2SlpyOi52PjI-Knpfl9PdtQm8_-e8uPWO63fT3LXFsP_nvLj1jus3n9euelZqeyp6UjI7Jx8-Qi4zNjsuMnO_8zef1656VmpOezpTMlsvPzs-Qj5mYzZqY7_3F656Vmp7KnpSMjsnHz5CLjM2Oy4yc.ewJ6w2FwMFdWrB-_c6ZtCZwRZOC_KSFKm6BFh0EwivbrgPe2dsjE4NrV08zVpoy5PVTDzmkRJlERV3IKxrhVCw"
FOLDER_ID = "b1gv54oj5gk7o0lvehoh"
LOG_FILE_PATH = "data/log.csv"

# Лог-файл
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["user_id", "timestamp", "action", "text"])

# Логирование
def log_action(user_id: int, action: str, text: str = ""):
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE_PATH, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([user_id, timestamp, action, text])
    print(f"LOG: {user_id} — {action} — {text[:40]}")

# Ответ YandexGPT
def ask_yandexgpt(user_text: str) -> str:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 200
        },
        "messages": [
            {"role": "user", "text": user_text}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()["result"]["alternatives"][0]["message"]["text"]
    except Exception as e:
        print(f"Ошибка запроса к GPT: {e}")
        return "Ошибка при обращении к YandexGPT 😔"

# Обработка для /start
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    log_action(user_id, "start")
    update.message.reply_text("Здравствуйте! Если вы видите этот текст, значит, уже всё неплохо 😎 Теперь можно попробовать что-нибудь спросить у гпт 🤓 ")

# Обработка остальных сообщений
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_text = update.message.text
    log_action(user_id, "user_message", user_text)

    reply = ask_yandexgpt(user_text)

    log_action(user_id, "gpt_reply", reply)
    update.message.reply_text(reply)

# Запуск бота
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    print("Бот запущен...")
    updater.idle()

if __name__ == '__main__':
    main()
