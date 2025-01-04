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
  name       = "function-homework-1"
  user_hash  = archive_file.code_zip.output_sha256
  runtime    = "python312"
  entrypoint = "index.handler"
  memory     = 128
  content {
    zip_filename = archive_file.code_zip.output_path
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
