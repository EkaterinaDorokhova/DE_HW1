# Data Engineering. Проект

## Часть 1 (HW1: Telegram Bot + YandexGPT)

Бот для Telegram, развёрнутый на виртуальной машине Yandex Cloud:
[Botishe_dly_proektisha_bot](https://t.me/Botishe_dly_proektisha_bot)

Python-скрипт: [Файл bot.py](https://github.com/EkaterinaDorokhova/DE_HW1/blob/main/bot.py)

### Функционал:
- Приём сообщений от пользователей
- Генерация ответов с помощью YandexGPT (Lite)
- Логирование действий в CSV-файл

---

## Процесс выполнения работы

### 1. Создана виртуальная машина

- Платформа: Yandex Cloud
- ОС: Ubuntu 22.04
- Подключение по SSH с использованием ключей

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<IP_адрес>
```

### 2. Установлены инструменты и подготовлен проект

Установка python3, pip, venv, zip, nano, scp
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv zip nano
```

Создание виртуального окружения и установка зависимостей:
```bash
mkdir telegram_bot_project && cd telegram_bot_project
python3 -m venv venv
source venv/bin/activate
pip install python-telegram-bot requests
```

Структура проекта:
1. Папка telegram_bot_project/
2. Подкаталог data/ для логов
3. Файл bot.py

```
telegram_bot_project/
├── bot.py
├── data/
│   └── log.csv
├── venv/
```

---

### 3. Настроен Telegram-бот
- Создан бот через @BotFather
- Получен токен доступа
- Токен подставлен в переменную `TELEGRAM_TOKEN` в `bot.py`

---

### 4. Настроено логирование действий
В файл `data/log.csv` записываются данные:
- user_id
- timestamp
- action (`start`, `user_message`, `gpt_reply`)
- текст сообщения или ответа.

Архивация логов:
```bash
zip -r part1_logs.zip data/
```

Скачивание на локальный компьютер:
```bash
scp -i ~/.ssh/id_ed25519 ubuntu@<IP_адрес>:~/telegram_bot_project/part1_logs.zip ~/Downloads/
```

Пример документа с логами: [Файл log.csv](https://github.com/EkaterinaDorokhova/DE_HW1/blob/main/log.csv)

---

### 5. Настроен API и подключен YandexGPT

- Создан сервисный аккаунт в Yandex Cloud
- Назначены роли
- Сгенерирован ключ (JSON) и получен IAM-токен
- Токен подключен в bot.py

### Инициализация и настройки

1. Загрузка библиотек (telegram, requests, csv, os, datetime, json)
2. Настройка параметров:
- TELEGRAM_TOKEN — токен бота из BotFather
- IAM_TOKEN — IAM-токен для авторизации в API YandexGPT
- FOLDER_ID — ID каталога в Yandex Cloud
- LOG_FILE_PATH — путь к CSV-файлу с логами

```python
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime
import requests
import csv
import os
import json

from yandex_cloud_ml_sdk import YCloudML

TELEGRAM_TOKEN = "7151965357:AAFpyYFg6mBcteEuXhp8gQLwbRuSS6pxEG0"
IAM_TOKEN ="t1.9euelZqYkZnIk8uVnIyQz5GSjZeMj-3rnpWampuXzJ2SlpyOi52PjI-Knpfl9PdtQm8_-e8uPWO63fT3LXFsP_nvLj1jus3n9euelZqeyp6UjI7Jx8-Qi4zNjsuMnO_8zef1656VmpOezpTMlsvPzs-Qj5mYzZqY7_3F656Vmp7KnpSMjsnHz5CLjM2Oy4yc.ewJ6w2FwMFdWrB-_c6ZtCZwRZOC_KSFKm6BFh0EwivbrgPe2dsjE4NrV08zVpoy5PVTDzmkRJlERV3IKxrhVCw"
FOLDER_ID = "b1gv54oj5gk7o0lvehoh"
LOG_FILE_PATH = "data/log.csv"
```

### Логирование действий

1. При первом запуске создаётся файл data/log.csv
2. Затем в лог записываются:
- user_id пользователя
- время (timestamp)
- тип действия (start, user_message, gpt_reply)
- текст сообщения

```python
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
```

### Обращение к YandexGPT

1. Используется API-адрес https://llm.api.cloud.yandex.net/foundationModels/v1/completion
2. Формируется JSON-запрос с параметрами:
- модель: yandexgpt-lite
- temperature: 0.6
- maxTokens: 200
- история сообщений
3. При возникновении ошибки возвращается фраза "Ошибка при обращении к YandexGPT 😔".

```python
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
```

### Начало диалога (ответ на /start)

1. Логируется действие
2. Отправляется приветственное сообщение пользователю

```python
# Обработка для /start
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    log_action(user_id, "start")
    update.message.reply_text("Здравствуйте! Если вы видите этот текст, значит, уже всё неплохо 😎 Теперь можно попробовать что-нибудь спросить у гпт 🤓 ")
```

### Ответ на последующие сообщения

1. Пользователь отправляет сообщение - оно логируется (user_message)
2. Вызывается функция ask_yandexgpt(...):
- отправляет запрос в YandexGPT Lite через HTTP API
- получает сгенерированный ответ
- ответ логируется как gpt_reply
- бот отправляет ответ пользователю

```python
# Обработка остальных сообщений
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_text = update.message.text
    log_action(user_id, "user_message", user_text)

    reply = ask_yandexgpt(user_text)

    log_action(user_id, "gpt_reply", reply)
    update.message.reply_text(reply)
```

### Запуск бота

Функция main:
- запускает Updater для Telegram
- добавляет обработчики команд и текстов
- запускает бот в режиме polling.

```python
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
```
---

### 6. Бот запущен и протестирован

Запуск
```bash
python3 bot.py
```

Результат: бот принимает сообщения, генерирует ответы через YandexGPT и логирует действия в `data/log.csv`.

---



## Часть 2 (HW2: интеграция с облачным сервисом Яндекс Диск и визуализации в Yandex DataLens)
Файл логов
