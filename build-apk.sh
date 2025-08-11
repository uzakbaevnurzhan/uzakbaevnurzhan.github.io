#!/bin/bash

echo "🚀 Начинаем сборку APK для Uzakbaevnurzhan Mirror..."

# Проверяем наличие Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен. Пожалуйста, установите Node.js 16+"
    exit 1
fi

# Проверяем наличие npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm не установлен"
    exit 1
fi

# Проверяем версию Node.js
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Требуется Node.js версии 16 или выше. Текущая версия: $(node -v)"
    exit 1
fi

echo "✅ Node.js версии $(node -v) найден"

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при установке зависимостей"
    exit 1
fi

echo "✅ Зависимости установлены"

# Проверяем наличие Android SDK
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    echo "⚠️  Переменные окружения ANDROID_HOME или ANDROID_SDK_ROOT не установлены"
    echo "   Это может вызвать проблемы при сборке"
fi

# Очищаем предыдущие сборки
echo "🧹 Очищаем предыдущие сборки..."
cd android
./gradlew clean

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при очистке проекта"
    exit 1
fi

echo "✅ Проект очищен"

# Собираем debug APK
echo "🔨 Собираем debug APK..."
./gradlew assembleDebug

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при сборке debug APK"
    exit 1
fi

echo "✅ Debug APK собран"

# Проверяем, что APK файл создан
APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK_PATH" ]; then
    APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
    echo "✅ APK файл создан: $APK_PATH (размер: $APK_SIZE)"
    
    # Копируем APK в корневую папку проекта
    cp "$APK_PATH" "../uzakbaevnurzhan-mirror-debug.apk"
    echo "📱 APK скопирован в корневую папку: uzakbaevnurzhan-mirror-debug.apk"
else
    echo "❌ APK файл не найден"
    exit 1
fi

cd ..

# Собираем release APK (если есть подписанный keystore)
echo "🔨 Собираем release APK..."
cd android
./gradlew assembleRelease

if [ $? -eq 0 ]; then
    RELEASE_APK_PATH="app/build/outputs/apk/release/app-release.apk"
    if [ -f "$RELEASE_APK_PATH" ]; then
        RELEASE_APK_SIZE=$(du -h "$RELEASE_APK_PATH" | cut -f1)
        echo "✅ Release APK собран: $RELEASE_APK_PATH (размер: $RELEASE_APK_SIZE)"
        
        # Копируем release APK в корневую папку проекта
        cp "$RELEASE_APK_PATH" "../uzakbaevnurzhan-mirror-release.apk"
        echo "📱 Release APK скопирован в корневую папку: uzakbaevnurzhan-mirror-release.apk"
    fi
else
    echo "⚠️  Release APK не собран (возможно, отсутствует keystore)"
fi

cd ..

echo ""
echo "🎉 Сборка завершена!"
echo ""
echo "📱 Созданные файлы:"
if [ -f "uzakbaevnurzhan-mirror-debug.apk" ]; then
    echo "   - uzakbaevnurzhan-mirror-debug.apk (для тестирования)"
fi
if [ -f "uzakbaevnurzhan-mirror-release.apk" ]; then
    echo "   - uzakbaevnurzhan-mirror-release.apk (для публикации)"
fi
echo ""
echo "📋 Инструкции по установке:"
echo "   1. Скопируйте APK файл на Android устройство"
echo "   2. Включите 'Установка из неизвестных источников' в настройках"
echo "   3. Установите APK файл"
echo "   4. Запустите приложение и войдите с учетными данными:"
echo "      Пользователь: uzakbaevnurzhan"
echo "      Пароль: ad951qu1"
echo ""
echo "🔧 Для подключения к серверу:"
echo "   - Убедитесь, что Flask сервер запущен на порту 5000"
echo "   - В настройках приложения укажите IP адрес сервера"
echo ""