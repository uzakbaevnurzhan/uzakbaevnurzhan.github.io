# Uzakbaev Nurzhan Site Monitor - Mobile App

Мобильное приложение для мониторинга сайта Uzakbaev Nurzhan, созданное на основе Flask веб-приложения.

## Описание

Это Android приложение, которое предоставляет мобильный интерфейс для взаимодействия с Flask API приложения `app.py`. Приложение позволяет:

- Входить в систему с учетными данными
- Просматривать сохраненные страницы сайта
- Проверять обновления
- Выполнять поиск по содержимому
- Просматривать содержимое страниц

## Структура проекта

```
├── app.py              # Оригинальное Flask приложение
├── mobile_app.py       # Мобильное приложение на Kivy
├── main.py             # Точка входа для мобильного приложения
├── buildozer.spec      # Конфигурация для сборки APK
├── requirements.txt    # Зависимости для Flask приложения
└── README.md          # Этот файл
```

## Требования для сборки

### Системные требования:
- Ubuntu/Debian Linux (рекомендуется)
- Python 3.7+
- Java JDK 8+
- Android SDK
- Android NDK

### Установка зависимостей:

```bash
# Обновление системы
sudo apt update
sudo apt upgrade

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y git zip unzip openjdk-8-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Установка buildozer
pip3 install --user buildozer

# Добавление buildozer в PATH
export PATH=$PATH:$HOME/.local/bin
```

## Сборка APK

### 1. Подготовка окружения

```bash
# Клонирование репозитория (если еще не сделано)
git clone <your-repo-url>
cd <your-repo-directory>

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка сервера

Перед сборкой APK убедитесь, что Flask приложение (`app.py`) запущено и доступно:

```bash
# Запуск Flask приложения
python app.py
```

Приложение будет доступно по адресу `http://localhost:5000`

### 3. Настройка URL сервера

В файле `mobile_app.py` измените URL сервера на ваш:

```python
self.base_url = "http://your-server-ip:5000"  # Замените на ваш IP
```

### 4. Сборка APK

```bash
# Инициализация buildozer (если нужно)
buildozer init

# Сборка APK
buildozer android debug

# Или для релизной версии
buildozer android release
```

### 5. Установка на устройство

После успешной сборки APK файл будет находиться в папке `bin/`:

```bash
# Копирование APK на устройство
adb install bin/uzakbaevnurzhan-1.0-debug.apk
```

## Использование приложения

1. **Запуск**: Откройте приложение на Android устройстве
2. **Вход**: Введите учетные данные (по умолчанию: uzakbaevnurzhan / ad951qu1)
3. **Навигация**: Используйте кнопки для доступа к различным функциям:
   - **Pages**: Просмотр сохраненных страниц
   - **Check Updates**: Проверка обновлений сайта
   - **Search**: Поиск по содержимому
   - **Logout**: Выход из системы

## Устранение неполадок

### Проблемы с подключением
- Убедитесь, что Flask сервер запущен
- Проверьте правильность URL в `mobile_app.py`
- Убедитесь, что устройство и сервер находятся в одной сети

### Проблемы со сборкой
- Проверьте, что все зависимости установлены
- Убедитесь, что Java JDK 8+ установлен
- Проверьте переменные окружения JAVA_HOME и ANDROID_HOME

### Логи
Для отладки используйте:
```bash
adb logcat | grep python
```

## Безопасность

- Приложение использует HTTPS для безопасного соединения (если настроено на сервере)
- Учетные данные передаются через POST запросы
- Сессии управляются Flask приложением

## Лицензия

Этот проект создан для личного использования Uzakbaev Nurzhan.

## Поддержка

При возникновении проблем создайте issue в репозитории или обратитесь к разработчику.