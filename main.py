from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
import requests


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login'
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Mirror App', font_size=30, size_hint_y=None, height=50))
        
        self.server_input = TextInput(hint_text='Server URL (http://ip:5000)', multiline=False)
        self.username_input = TextInput(hint_text='Username', multiline=False)
        self.password_input = TextInput(hint_text='Password', password=True, multiline=False)
        
        login_btn = Button(text='Login', size_hint_y=None, height=50)
        login_btn.bind(on_press=self.login)
        
        layout.add_widget(self.server_input)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        
        self.add_widget(layout)
    
    def login(self, instance):
        server = self.server_input.text
        username = self.username_input.text
        password = self.password_input.text
        
        if server and username and password:
            try:
                response = requests.post(
                    f"{server}/login",
                    data={"username": username, "password": password},
                    timeout=10
                )
                if response.status_code == 302:
                    # Success - store session and switch screen
                    app = App.get_running_app()
                    app.server_url = server
                    app.session = requests.Session()
                    app.session.cookies.update(response.cookies)
                    self.manager.current = 'main'
                else:
                    print("Login failed")
            except Exception as e:
                print(f"Error: {e}")


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text='Mirror App - Connected', font_size=24, size_hint_y=None, height=50))
        
        # Action buttons
        check_btn = Button(text='Check Updates', size_hint_y=None, height=50)
        check_btn.bind(on_press=self.check_updates)
        
        update_btn = Button(text='Update Site', size_hint_y=None, height=50)
        update_btn.bind(on_press=self.do_update)
        
        pages_btn = Button(text='View Pages', size_hint_y=None, height=50)
        pages_btn.bind(on_press=self.view_pages)
        
        logout_btn = Button(text='Logout', size_hint_y=None, height=50)
        logout_btn.bind(on_press=self.logout)
        
        self.status_label = Label(text='Ready', size_hint_y=None, height=50)
        
        layout.add_widget(check_btn)
        layout.add_widget(update_btn)
        layout.add_widget(pages_btn)
        layout.add_widget(self.status_label)
        layout.add_widget(logout_btn)
        
        self.add_widget(layout)
    
    def check_updates(self, instance):
        app = App.get_running_app()
        try:
            response = app.session.get(f"{app.server_url}/check_updates", timeout=30)
            if response.status_code == 200:
                data = response.json()
                changed = len(data.get('changed', []))
                new = len(data.get('new', []))
                self.status_label.text = f"Changed: {changed}, New: {new}"
            else:
                self.status_label.text = "Update check failed"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
    
    def do_update(self, instance):
        app = App.get_running_app()
        try:
            response = app.session.post(f"{app.server_url}/do_update", timeout=60)
            if response.status_code == 200:
                data = response.json()
                self.status_label.text = data.get('msg', 'Update completed')
            else:
                self.status_label.text = "Update failed"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
    
    def view_pages(self, instance):
        app = App.get_running_app()
        try:
            response = app.session.get(f"{app.server_url}/pages", timeout=10)
            if response.status_code == 200:
                # Count pages in response
                page_count = response.text.count('href="/view?page=')
                self.status_label.text = f"Found {page_count} pages"
            else:
                self.status_label.text = "Failed to load pages"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
    
    def logout(self, instance):
        self.manager.current = 'login'


class MirrorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_url = ""
        self.session = None
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(MainScreen())
        return sm


if __name__ == '__main__':
    MirrorApp().run()