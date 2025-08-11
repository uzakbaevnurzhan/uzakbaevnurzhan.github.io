[app]
title = Mirror
package.name = mirror
package.domain = org.example
source.dir = .
source.include_exts = py,kv,txt,md,ini,json,db,html,css,js
version = 0.1
requirements = python3,kivy,flask,requests,beautifulsoup4,lxml,werkzeug,itsdangerous,click,markupsafe
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
# Increase if you need more heap for Chromium-based webview in external browser
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
log_level = 2

# Ensure Flask serves on localhost; we open external browser
android.add_src = app.py

[buildozer]
log_level = 2
warn_on_root = 0

[android]
# If you want to bundle Chrome WebView and open inside app, add kivy_garden.xcamera or webview libs; we use system browser instead