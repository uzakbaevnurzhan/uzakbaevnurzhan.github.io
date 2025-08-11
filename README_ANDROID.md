# Building the **UzakbaevNurzhan** APK

This repository now includes everything required to turn the existing `app.py` Flask project into a self-contained Android application.

The packaging approach is:

1. A small **Kivy** launcher (`main.py`) starts the Flask server in a background thread.
2. Once the backend is running it attempts to open the system browser at `http://127.0.0.1:5000`.  You can bookmark this address or create a home-screen shortcut so the app behaves like a native UI.
3. All Python code (including Flask, Selenium, etc.) is bundled into an APK using **Buildozer** / **python-for-android**.

---

## Prerequisites (Ubuntu/Debian)

```bash
# 1. System dependencies (Java, Android SDK helpers, etc.)
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
    build-essential pkg-config libffi-dev libssl-dev

# 2. Create and activate a virtualenv (recommended)
python3 -m venv venv
source venv/bin/activate

# 3. Install Buildozer
pip install --upgrade buildozer cython packaging
# Make sure ~/.local/bin (or your venv bin dir) is on $PATH
```

On macOS use `brew install openjdk git wget autoconf automake libtool pkg-config` instead of `apt`.

> **Tip:** The first build downloads ~2-3 GB (Android SDK, NDK, etc.).  Make sure you have bandwidth and disk space available.

---

## Building the APK

```bash
# Inside the repo root
git clone <this-repo>
cd <this-repo>

# (Optional) Adjust anything in buildozer.spec if you need

# Run the build (debug build is enough for testing)
buildozer -v android debug

# When it finishes you will find the apk under
bin/UzakbaevNurzhan-0.1-debug.apk
```

To install the APK on a connected device with **ADB**:

```bash
adb install -r bin/UzakbaevNurzhan-0.1-debug.apk
```

---

## Releasing to Play Store

1. Make a *release* build: `buildozer android release`.
2. Sign the generated `.aab`/`.apk` with your keystore (Buildozer can automate this: see the commented options in *buildozer.spec*).
3. Follow Google Play console instructions to upload and publish.

---

## Customising

* **Permissions** – edit `android.permissions` in `buildozer.spec` if you need more than `INTERNET`.
* **Version** – bump the `version` field and optionally set `version.regex` and `version.git` for auto-versioning.
* **Package name** – update `package.name` and `package.domain`.

---

### Troubleshooting

* *Download errors / checksum mismatch* – just rerun the command.  Remote servers occasionally fail.
* *`Could not find SDK/NDK`* – delete the `~/.buildozer` directory and start over, or set `android.sdk_path`/`android.ndk_path` manually.
* *App opens but shows blank page* – open your mobile browser to `http://127.0.0.1:5000` manually.  Some Android ROMs block the automatic `Intent`.

Happy hacking!