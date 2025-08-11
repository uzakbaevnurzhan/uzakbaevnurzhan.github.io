[app]
# (str) Title of your application
title = UzakbaevNurzhan

# (str) Package name
package.name = uzakbaevnurzhan

# (str) Package domain (should be unique; reverse-DNS style)
package.domain = org.uzakbaev

# (str) Source code directory (relative to this spec file)
source.dir = .

# (list) List of inclusions using pattern matching
source.include_exts = py,kv,txt,db,json,html,css,js,png,jpg,jpeg,ttf,otf,zip

# (str) Application versioning (method 1)
version = 0.1

# (str) Application entry point
# We will create a small Kivy-based launcher `main.py` that starts app.py
entrypoint = main.py

# (list) Application requirements
# Kivy is needed for UI WebView; others pulled from app.py imports
requirements = python3,kivy,flask,requests,beautifulsoup4,lxml,selenium,webdriver-manager,cryptography

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (str) Android minimum API, supports from API 23 (Android 6.0) upwards by default
android.api = 29

# (str) Architecture
android.archs = arm64-v8a, armeabi-v7a

# (bool) Copy library instead of compiling (speeds up for pure-python requirements)
#android.copy_libs = 1

# (str) The bootstrap to use; sdl2 is default and includes a Python interpreter
bootstrap = sdl2

# (bool) Use service-only mode (no window). We need a small window to embed WebView, so keep false.
#service_only = false

# (str) Orientation
orientation = portrait

# (str) Full package name (com.example.myapp). Automatically generated if omitted.
#android.package = org.uzakbaev.uzakbaevnurzhan

# -- End of app section --

[buildozer]
# (bool) Should we require buildozer to automatically download Android SDK/NDK etc?
android.accept_sdk_license = True

# (str) Path to Android SDK, NDK if you have them pre-installed; otherwise leave blank.
#android.sdk_path = /opt/android-sdk
#android.ndk_path = /opt/android-ndk

# (str) Log level (info, debug, error)
log_level = 2

# (bool) Enable verbose debug output
warn_on_root = 1