import os
import json
import requests
import base64


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
OCR_ERROR_TEXT = "Я не могу обработать эту фотографию."

SPECIAL_MESSAGES = ["/start", "/help"]


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


def create_yandex_model_headers():
    return {
        "Content-Type": "application/json",
        "x-folder-id": FOLDER_ID,
        "Authorization": f"Api-Key {SERVICE_ACCOUNT_API_KEY}",
    }


def get_llm_response(user_text: str):
    file_body = open("/function/storage/mnt/llm_request_body.json").read()
    request_body = json.loads(file_body)

    request_body["modelUri"] = request_body["modelUri"].replace(
        "{folder_id}", FOLDER_ID
    )
    request_body["messages"].append({"role": "user", "text": user_text})

    headers = create_yandex_model_headers()

    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        json=request_body,
        headers=headers,
    )

    return response


def process_text(user_text, message):
    response = get_llm_response(user_text)

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

    try:
        if TELEGRAM_BOT_TOKEN is None:
            return DEFAULT_RESPONSE

        update = json.loads(event["body"])

        if "message" not in update:
            return DEFAULT_RESPONSE

        message_in = update["message"]

        # If only text
        if "text" in message_in:
            if message_in["text"] in SPECIAL_MESSAGES:
                send_message(HELP_TEXT, message_in)
                return DEFAULT_RESPONSE
            return process_text(message_in["text"], message_in)

        # If only images
        if "photo" in message_in:
            # If multiple photos
            if "media_group_id" in message_in:
                send_message(PHOTO_LENGTH_ERROR_TEXT, message_in)
                return DEFAULT_RESPONSE

            return process_image(message_in["photo"], message_in)

        # If no text or images then error
        send_message(MESSAGE_TYPE_ERROR_TEXT, message_in)
        return DEFAULT_RESPONSE

    except:
        return DEFAULT_RESPONSE


def get_tg_file(file_id):
    get_file_response = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
        params={"file_id": file_id},
    )

    file_path = get_file_response.json()["result"]["file_path"]

    resp = requests.get(
        f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    )
    return base64.b64encode(resp.content).decode("ascii")


def get_ocr_response(img_base64_encoded):
    file_body = open("/function/storage/mnt/ocr_request_body.json").read()
    request_body = json.loads(file_body)
    request_body["content"] = img_base64_encoded

    headers = create_yandex_model_headers()

    response = requests.post(
        "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText",
        json=request_body,
        headers=headers,
    )

    return response


def process_image(photo_sizes: list, message):
    file_id = photo_sizes[-1]["file_id"]
    img = get_tg_file(file_id)
    resp = get_ocr_response(img)

    if not resp.ok:
        send_message(OCR_ERROR_TEXT, message)
        return DEFAULT_RESPONSE

    data = resp.json()

    text = data["result"]["textAnnotation"]["fullText"]

    return process_text(text, message)
