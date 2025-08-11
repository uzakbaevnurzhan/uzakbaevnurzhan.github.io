# Uzakbaevnurzhan Mirror - Mobile App

Мобильное приложение для управления локальными копиями веб-сайтов, созданное на основе Flask приложения.

## Описание

Это React Native приложение предоставляет мобильный интерфейс для системы зеркалирования сайтов. Приложение позволяет:

- Просматривать локальные копии страниц
- Управлять обновлениями
- Вести журнал аудита
- Общаться в чате
- Администрировать систему (для администраторов)

## Требования

- Node.js 16+
- React Native CLI
- Android Studio (для сборки APK)
- JDK 11+
- Android SDK

## Установка зависимостей

```bash
npm install
```

## Настройка

1. Убедитесь, что Flask сервер запущен на порту 5000
2. В файле `src/services/apiService.js` настройте правильный URL сервера:
   - Для эмулятора Android: `http://10.0.2.2:5000`
   - Для реального устройства: `http://your-server-ip:5000`

## Запуск в режиме разработки

```bash
# Запуск Metro bundler
npm start

# Запуск на Android эмуляторе
npm run android

# Запуск на iOS симуляторе (только на macOS)
npm run ios
```

## Сборка APK

### 1. Подготовка к сборке

```bash
# Очистка кэша
cd android
./gradlew clean
cd ..

# Установка зависимостей
npm install
```

### 2. Сборка debug APK

```bash
cd android
./gradlew assembleDebug
```

APK файл будет создан в: `android/app/build/outputs/apk/debug/app-debug.apk`

### 3. Сборка release APK

```bash
cd android
./gradlew assembleRelease
```

APK файл будет создан в: `android/app/build/outputs/apk/release/app-release.apk`

## Структура проекта

```
├── src/
│   ├── screens/          # Экраны приложения
│   ├── components/       # Переиспользуемые компоненты
│   ├── context/          # React Context
│   ├── services/         # API сервисы
│   └── utils/           # Утилиты
├── android/             # Android конфигурация
├── ios/                # iOS конфигурация
├── App.js              # Главный компонент
├── index.js            # Точка входа
└── package.json        # Зависимости
```

## Основные экраны

1. **LoginScreen** - Экран входа
2. **HomeScreen** - Главная страница с статистикой
3. **PagesScreen** - Список страниц
4. **ViewPageScreen** - Просмотр страницы
5. **AuditScreen** - Журнал аудита
6. **ChatScreen** - Чат
7. **AdminScreen** - Админ панель
8. **SettingsScreen** - Настройки

## API интеграция

Приложение интегрируется с Flask API через следующие эндпоинты:

- `/login` - Аутентификация
- `/pages` - Список страниц
- `/view` - Просмотр страницы
- `/audit` - Журнал аудита
- `/chat` - Чат
- `/admin` - Админ функции

## Учетные данные по умолчанию

- **Пользователь**: uzakbaevnurzhan
- **Пароль**: ad951qu1
- **Роль**: admin

## Особенности

- Темная тема по умолчанию
- Адаптивный дизайн
- Поддержка офлайн режима (кэширование)
- Push-уведомления (в разработке)
- Экспорт данных
- Резервное копирование

## Устранение неполадок

### Ошибка сборки Android

1. Убедитесь, что установлен Android SDK
2. Проверьте переменные окружения ANDROID_HOME и ANDROID_SDK_ROOT
3. Выполните `cd android && ./gradlew clean`

### Ошибки подключения к серверу

1. Проверьте, что Flask сервер запущен
2. Убедитесь в правильности URL в apiService.js
3. Проверьте настройки сети и файрвола

### Проблемы с зависимостями

```bash
# Очистка кэша npm
npm cache clean --force

# Удаление node_modules и переустановка
rm -rf node_modules
npm install
```

## Лицензия

MIT License

## Разработчик

Uzakbaevnurzhan