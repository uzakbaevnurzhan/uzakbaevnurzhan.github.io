#!/usr/bin/env python3
"""
Uzakbaev Nurzhan Site Monitor Mobile App
Main entry point for the Android application
"""

import os
import sys
from mobile_app import UzakbaevNurzhanApp

if __name__ == '__main__':
    # Set up environment for mobile
    if hasattr(sys, '_MEIPASS'):
        # Running as compiled executable
        os.chdir(sys._MEIPASS)
    
    # Start the Kivy application
    UzakbaevNurzhanApp().run()