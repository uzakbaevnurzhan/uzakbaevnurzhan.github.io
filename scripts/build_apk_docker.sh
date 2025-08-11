#!/usr/bin/env bash
set -euo pipefail

APP_DIR=$(cd "$(dirname "$0")/.." && pwd)

docker run --rm -it \
  -v "$APP_DIR":/home/user/app \
  -w /home/user/app \
  kivy/buildozer \
  buildozer -v android debug

echo "\nIf successful, your APK will be in ./bin/*.apk"