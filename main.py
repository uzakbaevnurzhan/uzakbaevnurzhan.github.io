import threading
import time
import webbrowser

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import os
os.environ.setdefault("APP_DATA_DIR", os.path.join(os.getcwd(), "data"))
from app import app as flask_app


def run_flask_server():
    # Bind explicitly to localhost for Android
    flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


class LauncherLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=16, spacing=12, **kwargs)
        self.status = Label(text="Сервер запускается...", size_hint=(1, None), height=40)
        self.add_widget(self.status)
        self.open_btn = Button(text="Открыть приложение", size_hint=(1, None), height=50)
        self.open_btn.bind(on_release=self.open_app)
        self.add_widget(self.open_btn)

    def open_app(self, *_):
        try:
            webbrowser.open("http://127.0.0.1:5000/")
        except Exception:
            self.status.text = "Не удалось открыть браузер. Откройте вручную: http://127.0.0.1:5000/"


class MirrorApp(App):
    def build(self):
        # Start Flask in a background thread
        t = threading.Thread(target=run_flask_server, daemon=True)
        t.start()
        # Give server a moment to start
        threading.Thread(target=self._delayed_browser_open, daemon=True).start()
        return LauncherLayout()

    def _delayed_browser_open(self):
        # wait a bit then try to open the browser automatically
        time.sleep(1.5)
        try:
            webbrowser.open("http://127.0.0.1:5000/")
        except Exception:
            pass


if __name__ == "__main__":
    MirrorApp().run()