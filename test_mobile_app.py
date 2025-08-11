#!/usr/bin/env python3
"""
Тестовый скрипт для проверки мобильного приложения
"""

import sys
import os

def test_imports():
    """Тестирует импорт всех необходимых модулей"""
    print("Тестируем импорты...")
    
    try:
        import requests
        print("✓ requests импортирован")
    except ImportError as e:
        print(f"✗ Ошибка импорта requests: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✓ BeautifulSoup импортирован")
    except ImportError as e:
        print(f"✗ Ошибка импорта BeautifulSoup: {e}")
        return False
    
    try:
        from kivy.app import App
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.textinput import TextInput
        from kivy.uix.label import Label
        print("✓ Kivy модули импортированы")
    except ImportError as e:
        print(f"✗ Ошибка импорта Kivy: {e}")
        return False
    
    return True

def test_mobile_app():
    """Тестирует мобильное приложение"""
    print("\nТестируем мобильное приложение...")
    
    try:
        from mobile_app import UzakbaevNurzhanApp
        print("✓ UzakbaevNurzhanApp импортирован")
        
        # Создаем экземпляр приложения
        app = UzakbaevNurzhanApp()
        print("✓ Экземпляр приложения создан")
        
        # Проверяем основные атрибуты
        assert hasattr(app, 'base_url'), "Отсутствует base_url"
        assert hasattr(app, 'session'), "Отсутствует session"
        assert hasattr(app, 'logged_in'), "Отсутствует logged_in"
        print("✓ Основные атрибуты присутствуют")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования мобильного приложения: {e}")
        return False

def test_flask_app():
    """Тестирует Flask приложение"""
    print("\nТестируем Flask приложение...")
    
    try:
        # Импортируем Flask приложение
        import app
        print("✓ Flask приложение импортировано")
        
        # Проверяем основные переменные
        assert hasattr(app, 'app'), "Отсутствует Flask app"
        assert hasattr(app, 'BASE_SITE'), "Отсутствует BASE_SITE"
        assert hasattr(app, 'DEFAULT_ADMIN'), "Отсутствует DEFAULT_ADMIN"
        print("✓ Основные переменные Flask приложения присутствуют")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования Flask приложения: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("=== Тестирование Uzakbaev Nurzhan Site Monitor ===")
    
    # Тестируем импорты
    if not test_imports():
        print("\n❌ Тест импортов не пройден")
        sys.exit(1)
    
    # Тестируем мобильное приложение
    if not test_mobile_app():
        print("\n❌ Тест мобильного приложения не пройден")
        sys.exit(1)
    
    # Тестируем Flask приложение
    if not test_flask_app():
        print("\n❌ Тест Flask приложения не пройден")
        sys.exit(1)
    
    print("\n✅ Все тесты пройдены успешно!")
    print("\nПриложение готово к сборке APK.")
    print("Выполните: ./build_apk.sh")

if __name__ == "__main__":
    main()