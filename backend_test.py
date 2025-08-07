#!/usr/bin/env python3
"""
Backend Test for Лесной Оракул (Forest Oracle) Web Application
This is a static web application test - checking server responses and static assets
"""

import requests
import sys
import json
from datetime import datetime

class StaticWebAppTester:
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, endpoint, expected_status=200, check_content=None):
        """Run a single test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            response = requests.get(url, timeout=10)
            success = response.status_code == expected_status
            
            if success and check_content:
                content_check = check_content in response.text
                if not content_check:
                    success = False
                    print(f"❌ Failed - Content check failed for '{check_content}'")
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if check_content:
                    print(f"   Content check passed: '{check_content}' found")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                
            return success, response
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_main_page(self):
        """Test main login page"""
        success, response = self.run_test(
            "Main Login Page",
            "",
            200,
            "Вход через Яндекс"
        )
        
        if success:
            # Check for essential elements
            checks = [
                ("OAuth title", "OAuth Вход - Лесной Оракул"),
                ("Captcha checkbox", "Я не робот"),
                ("Login button", "Войти"),
                ("Star animation CSS", ".star"),
                ("JavaScript functions", "loginViaService"),
                ("Yandex OAuth", "oauth.yandex.ru")
            ]
            
            for check_name, check_content in checks:
                if check_content in response.text:
                    print(f"   ✅ {check_name} found")
                else:
                    print(f"   ❌ {check_name} missing")
                    
        return success

    def test_ai_chat_page(self):
        """Test AI chat page"""
        success, response = self.run_test(
            "AI Chat Page",
            "ai.html",
            200,
            "Лесной Оракул"
        )
        
        if success:
            # Check for essential elements
            checks = [
                ("Chat title", "Лесной Оракул [Феникс]"),
                ("Google Gemini import", "@google/generative-ai"),
                ("API key setup", "AIzaSyAA6tHh2635MndLLPqYKa3e0j-rg3uNJfA"),
                ("Chat input", "userInput"),
                ("Send button", "sendButton"),
                ("History functionality", "historyBtn"),
                ("Image upload", "imageUpload"),
                ("PWA manifest", "manifest.json"),
                ("Responsive CSS", "@media"),
                ("Toast notifications", "toast-container")
            ]
            
            for check_name, check_content in checks:
                if check_content in response.text:
                    print(f"   ✅ {check_name} found")
                else:
                    print(f"   ❌ {check_name} missing")
                    
        return success

    def test_pwa_manifest(self):
        """Test PWA manifest"""
        success, response = self.run_test(
            "PWA Manifest",
            "manifest.json",
            200,
            "Лесной Оракул"
        )
        
        if success:
            try:
                manifest_data = json.loads(response.text)
                required_fields = ["name", "short_name", "start_url", "display", "icons"]
                
                for field in required_fields:
                    if field in manifest_data:
                        print(f"   ✅ Manifest field '{field}' present")
                    else:
                        print(f"   ❌ Manifest field '{field}' missing")
                        
                # Check icons
                if "icons" in manifest_data:
                    for icon in manifest_data["icons"]:
                        if "src" in icon and "sizes" in icon:
                            print(f"   ✅ Icon: {icon['src']} ({icon['sizes']})")
                        
            except json.JSONDecodeError:
                print("   ❌ Invalid JSON in manifest")
                
        return success

    def test_pwa_icons(self):
        """Test PWA icons"""
        icons = [
            ("PWA Icon 192x192", "icon-192x192.png"),
            ("PWA Icon 512x512", "icon-512x512.png")
        ]
        
        all_passed = True
        for icon_name, icon_file in icons:
            success, _ = self.run_test(icon_name, icon_file, 200)
            if not success:
                all_passed = False
                
        return all_passed

    def test_static_assets(self):
        """Test other static assets"""
        assets = [
            ("Yandex verification", "yandex_f6b8f9cc6c174e4a.html"),
            ("SVG Icon", "icon.svg")
        ]
        
        all_passed = True
        for asset_name, asset_file in assets:
            success, _ = self.run_test(asset_name, asset_file, 200)
            if not success:
                all_passed = False
                
        return all_passed

    def test_external_dependencies(self):
        """Test external dependencies accessibility"""
        print(f"\n🔍 Testing External Dependencies...")
        
        external_urls = [
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap",
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css",
            "https://cdn.jsdelivr.net/npm/marked/marked.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"
        ]
        
        for url in external_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {url}")
                else:
                    print(f"   ❌ {url} - Status: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {url} - Error: {str(e)}")

def main():
    print("=" * 60)
    print("🧪 ЛЕСНОЙ ОРАКУЛ - BACKEND/STATIC ASSETS TEST")
    print("=" * 60)
    
    # Setup
    tester = StaticWebAppTester()
    
    # Run tests
    print("\n📋 Running Static Web Application Tests...")
    
    tests = [
        ("Main Login Page", tester.test_main_page),
        ("AI Chat Page", tester.test_ai_chat_page),
        ("PWA Manifest", tester.test_pwa_manifest),
        ("PWA Icons", tester.test_pwa_icons),
        ("Static Assets", tester.test_static_assets)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"🔬 {test_name}")
        print(f"{'='*40}")
        test_func()
    
    # Test external dependencies
    tester.test_external_dependencies()
    
    # Print results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())