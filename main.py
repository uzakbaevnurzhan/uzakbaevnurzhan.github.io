import threading
import time
import webbrowser

from kivy.app import App
from kivy.uix.label import Label

# Import the Flask application defined in app.py
import app as flask_app


def _run_flask():
    """Run the Flask server in a background thread."""
    # Disable reloader to avoid creating extra threads/processes on Android
    flask_app.app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


class UzakbaevApp(App):
    """Simple Kivy front-end that launches the Flask backend."""

    def build(self):
        # Start Flask in background
        threading.Thread(target=_run_flask, daemon=True).start()

        # Try to open system browser after a short delay
        threading.Thread(target=self._open_browser, daemon=True).start()

        return Label(text="Server running at http://127.0.0.1:5000\n" "If your browser does not open automatically, open it manually.",
                     halign="center")

    def _open_browser(self):
        # Wait a moment for the server to start
        time.sleep(3)
        try:
            webbrowser.open("http://127.0.0.1:5000")
        except Exception as exc:
            # On some Android versions, this may fail; we just log the error.
            print("Could not launch browser:", exc)


if __name__ == "__main__":
    UzakbaevApp().run()