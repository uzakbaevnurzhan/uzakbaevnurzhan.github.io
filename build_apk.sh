#!/bin/bash

# Скрипт для сборки APK приложения Uzakbaev Nurzhan Site Monitor
# Автор: AI Assistant
# Дата: $(date)

set -e  # Остановка при ошибке

echo "=== Uzakbaev Nurzhan Site Monitor - APK Builder ==="
echo "Начинаем сборку APK..."

# Проверка наличия необходимых файлов
echo "Проверяем наличие необходимых файлов..."

required_files=("app.py" "mobile_app.py" "main.py" "buildozer.spec" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ОШИБКА: Файл $file не найден!"
        exit 1
    fi
done

echo "✓ Все необходимые файлы найдены"

# Проверка Python
echo "Проверяем Python..."
if ! command -v python3 &> /dev/null; then
    echo "ОШИБКА: Python3 не установлен!"
    exit 1
fi

python_version=$(python3 --version)
echo "✓ Python: $python_version"

# Проверка buildozer
echo "Проверяем buildozer..."
if ! command -v buildozer &> /dev/null; then
    echo "Устанавливаем buildozer..."
    pip3 install --user buildozer
    export PATH=$PATH:$HOME/.local/bin
fi

buildozer_version=$(buildozer --version 2>/dev/null || echo "unknown")
echo "✓ Buildozer: $buildozer_version"

# Очистка предыдущих сборок
echo "Очищаем предыдущие сборки..."
if [ -d ".buildozer" ]; then
    rm -rf .buildozer
fi

if [ -d "bin" ]; then
    rm -rf bin
fi

# Создание виртуального окружения для тестирования
echo "Создаем виртуальное окружение для тестирования..."
python3 -m venv venv_test
source venv_test/bin/activate
pip install -r requirements.txt

# Тестирование мобильного приложения
echo "Тестируем мобильное приложение..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from mobile_app import UzakbaevNurzhanApp
    print('✓ Мобильное приложение импортируется успешно')
except Exception as e:
    print(f'✗ Ошибка импорта: {e}')
    sys.exit(1)
"

deactivate
rm -rf venv_test

# Настройка переменных окружения
echo "Настраиваем переменные окружения..."
export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-8-openjdk-amd64}
export ANDROID_HOME=${ANDROID_HOME:-$HOME/Android/Sdk}

echo "JAVA_HOME: $JAVA_HOME"
echo "ANDROID_HOME: $ANDROID_HOME"

# Сборка APK
echo "Начинаем сборку APK..."
echo "Это может занять 10-30 минут..."

buildozer android debug

# Проверка результата
if [ -f "bin/uzakbaevnurzhan-1.0-debug.apk" ]; then
    echo ""
    echo "=== СБОРКА УСПЕШНО ЗАВЕРШЕНА! ==="
    echo "APK файл: bin/uzakbaevnurzhan-1.0-debug.apk"
    echo ""
    echo "Размер файла:"
    ls -lh bin/uzakbaevnurzhan-1.0-debug.apk
    echo ""
    echo "Для установки на устройство выполните:"
    echo "adb install bin/uzakbaevnurzhan-1.0-debug.apk"
    echo ""
    echo "Или скопируйте файл на устройство и установите вручную."
else
    echo ""
    echo "=== ОШИБКА СБОРКИ ==="
    echo "APK файл не был создан."
    echo "Проверьте логи выше для диагностики проблемы."
    exit 1
fi

echo "=== Сборка завершена ==="