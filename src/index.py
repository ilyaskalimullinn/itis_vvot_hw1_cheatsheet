import os
import json
import requests


DEFAULT_RESPONSE = {"statusCode": 200, "body": ""}
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

HELP_TEXT = (
    "Я помогу подготовить ответ на экзаменационный вопрос по "
    'дисциплине "Операционные системы".\n'
    "Пришлите мне фотографию с вопросом или наберите его текстом."
)
MESSAGE_TYPE_ERROR_TEXT = "Я могу обработать только текстовое сообщение или фотографию."
PHOTO_LENGTH_ERROR_TEXT = "Я могу обработать только одну фотографию."


def send_message(text, message):
    """Отправка сообщения пользователю Telegram."""
    message_id = message["message_id"]
    chat_id = message["chat"]["id"]
    reply_message = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": message_id,
    }

    requests.post(url=f"{TELEGRAM_API_URL}/sendMessage", json=reply_message)


def handler(event, context):
    """Обработчик облачной функции. Реализует Webhook для Telegram Bot."""

    # Logging
    print(event)

    if TELEGRAM_BOT_TOKEN is None:
        return DEFAULT_RESPONSE

    update = json.loads(event["body"])

    if "message" not in update:
        return DEFAULT_RESPONSE

    message_in = update["message"]

    # If only text
    if "text" in message_in:
        # TODO text logic
        send_message(f"You sent text: {message_in['text']}", message_in)
        return DEFAULT_RESPONSE

    # If only images
    if "photo" in message_in:
        # If multiple photos
        if "media_group_id" in message_in:
            send_message(PHOTO_LENGTH_ERROR_TEXT, message_in)
            return DEFAULT_RESPONSE

        # TODO image logic
        send_message(f"You sent {len(message_in['photo'])} photos", message_in)
        return DEFAULT_RESPONSE

    # If no text or images then error
    send_message(MESSAGE_TYPE_ERROR_TEXT, message_in)
    return DEFAULT_RESPONSE
