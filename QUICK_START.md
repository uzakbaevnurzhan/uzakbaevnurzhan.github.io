# Быстрый старт - Сборка APK

## 🚀 Быстрая сборка (Linux)

### 1. Установка зависимостей
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip git zip unzip openjdk-8-jdk
pip3 install --user buildozer
export PATH=$PATH:$HOME/.local/bin
```

### 2. Запуск автоматической сборки
```bash
./build_apk.sh
```

## 📱 Что получится

После успешной сборки вы получите APK файл: `bin/uzakbaevnurzhan-1.0-debug.apk`

## 🔧 Настройка сервера

Перед использованием APK:

1. Запустите Flask сервер:
```bash
python app.py
```

2. Измените URL в `mobile_app.py` (строка 18):
```python
self.base_url = "http://YOUR_SERVER_IP:5000"
```

## 📲 Установка на устройство

```bash
# Через ADB
adb install bin/uzakbaevnurzhan-1.0-debug.apk

# Или скопируйте файл на устройство и установите вручную
```

## 🔑 Учетные данные по умолчанию

- **Логин**: uzakbaevnurzhan
- **Пароль**: ad951qu1

## ⚠️ Важные замечания

- Убедитесь, что устройство и сервер в одной сети
- Для продакшена настройте HTTPS на сервере
- Измените учетные данные по умолчанию

## 🆘 Если что-то не работает

1. Проверьте логи: `adb logcat | grep python`
2. Убедитесь, что Flask сервер запущен
3. Проверьте правильность IP адреса сервера
4. Убедитесь, что порт 5000 открыт

## 📞 Поддержка

При проблемах обратитесь к полной документации в `README.md`