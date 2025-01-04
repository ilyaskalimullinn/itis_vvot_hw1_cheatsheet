terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  cloud_id                 = "b1g71e95h51okii30p25"
  folder_id                = "b1g9896fnt23hf2ohrrp"
  service_account_key_file = pathexpand("~/.yc-keys/key.json")
  zone                     = "ru-central1-d"
}

resource "yandex_function_iam_binding" "cloud_func_publicity" {
  function_id = yandex_function.cloud_func.id
  role        = "serverless.functions.invoker"

  members = [
    "system:allUsers",
  ]
}

resource "yandex_function" "cloud_func" {
  name        = "function-homework-1"
  user_hash   = archive_file.code_zip.output_sha256
  runtime     = "python312"
  entrypoint  = "index.handler"
  memory      = 128
  environment = { "TELEGRAM_BOT_TOKEN" = var.tg_bot_key }
  content {
    zip_filename = archive_file.code_zip.output_path
  }
  service_account_id = "ajef60r9ud57s8un41b1"
  mounts {
    name = "mnt"
    mode = "rw"
    object_storage {
      bucket = yandex_storage_bucket.bucket.bucket
    }
  }
}

resource "archive_file" "code_zip" {
  type        = "zip"
  output_path = "func.zip"
  source_dir  = "src"
}

output "function_url" {
  value = "https://functions.yandexcloud.net/${yandex_function.cloud_func.id}"
}

variable "tg_bot_key" {
  type        = string
  description = "Telegram Bot Key"
  sensitive   = true
}

data "http" "set_webhook_tg" {
  url = "https://api.telegram.org/bot${var.tg_bot_key}/setWebhook?url=https://functions.yandexcloud.net/${yandex_function.cloud_func.id}"
}

resource "yandex_storage_bucket" "bucket" {
  bucket = "c4ad8ab88294a95b3b2e4049829b761"
}

resource "yandex_storage_object" "llm_request_body" {
  bucket = yandex_storage_bucket.bucket.id
  key = "llm_request_body.json"
  source = "llm_request_body.json"
}
