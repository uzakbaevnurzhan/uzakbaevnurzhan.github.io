#!/bin/bash

echo "=== Mirror App APK Builder ==="
echo "Building APK for uzakbaevnurzhan Mirror App"
echo

# Check if virtual environment exists
if [ ! -d "mobile_app_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv mobile_app_env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source mobile_app_env/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install kivy buildozer cython requests

# Set Java home
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

# Check Java installation
if [ ! -d "$JAVA_HOME" ]; then
    echo "Error: Java 8 not found. Please install with:"
    echo "sudo apt install openjdk-8-jdk"
    exit 1
fi

echo "Java Home: $JAVA_HOME"

# Clean previous builds (optional)
echo "Cleaning previous build files..."
rm -rf .buildozer/android/platform/build-*
rm -rf bin/*.apk

# Start build
echo "Starting APK build process..."
echo "This may take 10-30 minutes for the first build..."
timeout 3600 buildozer android debug

# Check if build succeeded
if [ -f "bin/mirrorapp-1.0-debug.apk" ]; then
    echo
    echo "=== BUILD SUCCESS ==="
    echo "APK file created: bin/mirrorapp-1.0-debug.apk"
    echo "File size: $(du -h bin/mirrorapp-1.0-debug.apk | cut -f1)"
    echo
    echo "Next steps:"
    echo "1. Copy the APK file to your Android device"
    echo "2. Enable 'Unknown sources' in Android settings"
    echo "3. Install the APK file"
    echo "4. Run the Mirror App and connect to your Flask server"
    echo
    echo "Default login credentials:"
    echo "Username: uzakbaevnurzhan"
    echo "Password: ad951qu1"
    echo
else
    echo
    echo "=== BUILD FAILED ==="
    echo "Check the output above for errors."
    echo "Common issues:"
    echo "- Missing Java 8: sudo apt install openjdk-8-jdk"
    echo "- Missing build tools: sudo apt install build-essential"
    echo "- Insufficient disk space"
    echo "- Network connectivity issues"
fi