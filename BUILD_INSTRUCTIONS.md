# Инструкция по сборке APK

## Быстрая сборка

Для автоматической сборки APK выполните:

```bash
./build-apk.sh
```

Этот скрипт автоматически:
1. Проверит наличие Node.js
2. Установит зависимости
3. Очистит предыдущие сборки
4. Соберет debug APK
5. Попытается собрать release APK
6. Скопирует APK файлы в корневую папку

## Ручная сборка

### 1. Установка зависимостей
```bash
npm install
```

### 2. Сборка debug APK
```bash
cd android
./gradlew assembleDebug
cd ..
```

APK будет создан в: `android/app/build/outputs/apk/debug/app-debug.apk`

### 3. Сборка release APK
```bash
cd android
./gradlew assembleRelease
cd ..
```

APK будет создан в: `android/app/build/outputs/apk/release/app-release.apk`

## Требования

- Node.js 16+
- Java JDK 11+
- Android SDK
- Android Studio (рекомендуется)

## Переменные окружения

Убедитесь, что установлены:
- `ANDROID_HOME` или `ANDROID_SDK_ROOT`
- `JAVA_HOME`

## Установка на устройство

1. Скопируйте APK файл на Android устройство
2. Включите "Установка из неизвестных источников" в настройках
3. Установите APK файл
4. Запустите приложение

## Учетные данные для входа

- **Пользователь**: uzakbaevnurzhan
- **Пароль**: ad951qu1

## Подключение к серверу

Убедитесь, что Flask сервер запущен на порту 5000. В файле `src/services/apiService.js` настройте правильный URL сервера.

## Устранение проблем

### Ошибка "Command not found: gradlew"
```bash
chmod +x android/gradlew
```

### Ошибка сборки
```bash
cd android
./gradlew clean
./gradlew assembleDebug
```

### Проблемы с зависимостями
```bash
rm -rf node_modules
npm install
```