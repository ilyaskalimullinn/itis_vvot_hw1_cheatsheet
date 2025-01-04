import os
import json
import requests


DEFAULT_RESPONSE = {"statusCode": 200, "body": ""}
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
SERVICE_ACCOUNT_API_KEY = os.environ.get("SERVICE_ACCOUNT_API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")

HELP_TEXT = (
    "Я помогу подготовить ответ на экзаменационный вопрос по "
    'дисциплине "Операционные системы".\n'
    "Пришлите мне фотографию с вопросом или наберите его текстом."
)
MESSAGE_TYPE_ERROR_TEXT = "Я могу обработать только текстовое сообщение или фотографию."
PHOTO_LENGTH_ERROR_TEXT = "Я могу обработать только одну фотографию."
LLM_ERROR_TEXT = "Я не смог подготовить ответ на экзаменационный вопрос."


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


def get_llm_response(user_text: str):
    file_body = open("/function/storage/mnt/llm_request_body.json").read()
    request_body = json.loads(file_body)

    request_body["modelUri"] = request_body["modelUri"].replace(
        "{folder_id}", FOLDER_ID
    )
    request_body["messages"].append({"role": "user", "text": user_text})

    headers = {
        "Content-Type": "application/json",
        "x-folder-id": FOLDER_ID,
        "Authorization": f"Api-Key {SERVICE_ACCOUNT_API_KEY}",
    }

    print(request_body)

    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        json=request_body,
        headers=headers,
    )

    return response


def process_text(user_text, message):
    response = get_llm_response(user_text)
    print(response.content)  # TODO remove

    if not response.ok:
        send_message(LLM_ERROR_TEXT, message)
        return DEFAULT_RESPONSE

    data = response.json()

    answer = data["result"]["alternatives"][0]["message"]["text"]
    send_message(answer, message)
    return DEFAULT_RESPONSE


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
        return process_text(message_in["text"], message_in)

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
