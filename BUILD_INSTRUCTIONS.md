# 🚀 Инструкции по сборке APK для Uzakbaev Nurzhan Site Monitor

## ✅ Что уже готово

Я успешно создал все необходимые файлы для конвертации вашего Flask приложения в APK:

### 📁 Созданные файлы:
- `mobile_app.py` - Мобильное приложение на Kivy
- `main.py` - Точка входа для Android
- `buildozer.spec` - Конфигурация сборки APK
- `build_apk.sh` - Автоматический скрипт сборки
- `requirements.txt` - Зависимости Python
- `test_mobile_app.py` - Тестовый скрипт
- `README.md` - Полная документация
- `QUICK_START.md` - Быстрый старт

## 🔧 Шаги для сборки APK

### 1. Подготовка системы (Ubuntu/Debian)

```bash
# Обновление системы
sudo apt update && sudo apt upgrade

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv git zip unzip
sudo apt install -y openjdk-8-jdk autoconf libtool pkg-config
sudo apt install -y zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5
sudo apt install -y cmake libffi-dev libssl-dev libxml2-dev libxslt1-dev

# Установка buildozer
pip3 install --user buildozer
export PATH=$PATH:$HOME/.local/bin
```

### 2. Настройка проекта

```bash
# Перейдите в папку с проектом
cd /path/to/your/project

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 3. Настройка URL сервера

Откройте файл `mobile_app.py` и измените строку 18:

```python
self.base_url = "http://YOUR_SERVER_IP:5000"  # Замените на ваш IP
```

### 4. Запуск Flask сервера

```bash
# В отдельном терминале запустите Flask приложение
python app.py
```

### 5. Сборка APK

```bash
# Автоматическая сборка
./build_apk.sh

# Или ручная сборка
buildozer android debug
```

## 📱 Результат

После успешной сборки вы получите:
- `bin/uzakbaevnurzhan-1.0-debug.apk` - APK файл для установки

## 🔑 Учетные данные по умолчанию

- **Логин**: uzakbaevnurzhan
- **Пароль**: ad951qu1

## 📲 Установка на устройство

```bash
# Через ADB
adb install bin/uzakbaevnurzhan-1.0-debug.apk

# Или скопируйте файл на устройство и установите вручную
```

## 🎯 Функции мобильного приложения

✅ **Вход в систему** - Аутентификация пользователей
✅ **Просмотр страниц** - Список сохраненных страниц сайта
✅ **Проверка обновлений** - Мониторинг изменений на сайте
✅ **Поиск** - Поиск по содержимому страниц
✅ **Просмотр содержимого** - Отображение HTML страниц
✅ **Выход из системы** - Безопасный выход

## ⚠️ Важные замечания

1. **Сеть**: Убедитесь, что мобильное устройство и сервер находятся в одной сети
2. **IP адрес**: Используйте правильный IP адрес сервера в `mobile_app.py`
3. **Порт**: По умолчанию используется порт 5000
4. **Безопасность**: Для продакшена настройте HTTPS на сервере
5. **Учетные данные**: Измените пароль по умолчанию

## 🆘 Устранение неполадок

### Проблемы с подключением
```bash
# Проверьте логи приложения
adb logcat | grep python

# Убедитесь, что сервер запущен
curl http://YOUR_SERVER_IP:5000
```

### Проблемы со сборкой
```bash
# Очистите кэш buildozer
buildozer android clean

# Проверьте зависимости
python test_mobile_app.py
```

## 📞 Поддержка

Если возникнут проблемы:
1. Проверьте логи сборки
2. Убедитесь, что все зависимости установлены
3. Проверьте правильность IP адреса сервера
4. Обратитесь к полной документации в `README.md`

## 🎉 Готово!

Ваше Flask приложение успешно конвертировано в мобильное приложение для Android. APK файл готов к установке и использованию!