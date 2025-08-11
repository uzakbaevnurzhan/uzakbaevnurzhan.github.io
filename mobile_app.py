from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
import json
import threading
import requests
from urllib.parse import urljoin

class UzakbaevNurzhanApp(App):
    def __init__(self):
        super().__init__()
        self.base_url = "http://localhost:5000"  # Измените на ваш сервер
        self.session = requests.Session()
        self.logged_in = False
        self.username = ""
        
    def build(self):
        # Основной layout
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title_label = Label(
            text='Uzakbaev Nurzhan\nSite Monitor',
            size_hint_y=None,
            height=100,
            font_size='24sp',
            bold=True
        )
        self.main_layout.add_widget(title_label)
        
        # Форма входа
        self.login_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=200)
        
        self.username_input = TextInput(
            hint_text='Username',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        self.login_layout.add_widget(self.username_input)
        
        self.password_input = TextInput(
            hint_text='Password',
            multiline=False,
            password=True,
            size_hint_y=None,
            height=40
        )
        self.login_layout.add_widget(self.password_input)
        
        self.login_button = Button(
            text='Login',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)
        )
        self.login_button.bind(on_press=self.login)
        self.login_layout.add_widget(self.login_button)
        
        self.main_layout.add_widget(self.login_layout)
        
        # Основной контент (скрыт до входа)
        self.content_layout = BoxLayout(orientation='vertical', spacing=10)
        
        # Кнопки навигации
        nav_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=120)
        
        self.pages_button = Button(
            text='Pages',
            background_color=(0.3, 0.7, 0.3, 1)
        )
        self.pages_button.bind(on_press=self.show_pages)
        nav_layout.add_widget(self.pages_button)
        
        self.updates_button = Button(
            text='Check Updates',
            background_color=(0.8, 0.6, 0.2, 1)
        )
        self.updates_button.bind(on_press=self.check_updates)
        nav_layout.add_widget(self.updates_button)
        
        self.search_button = Button(
            text='Search',
            background_color=(0.6, 0.3, 0.8, 1)
        )
        self.search_button.bind(on_press=self.show_search)
        nav_layout.add_widget(self.search_button)
        
        self.logout_button = Button(
            text='Logout',
            background_color=(0.8, 0.3, 0.3, 1)
        )
        self.logout_button.bind(on_press=self.logout)
        nav_layout.add_widget(self.logout_button)
        
        self.content_layout.add_widget(nav_layout)
        
        # Область для отображения данных
        self.data_scroll = ScrollView(size_hint=(1, 1))
        self.data_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.data_layout.bind(minimum_height=self.data_layout.setter('height'))
        self.data_scroll.add_widget(self.data_layout)
        self.content_layout.add_widget(self.data_scroll)
        
        self.main_layout.add_widget(self.content_layout)
        self.content_layout.opacity = 0  # Скрыт до входа
        
        return self.main_layout
    
    def login(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.show_message("Please enter username and password")
            return
        
        # Отправляем запрос на вход
        try:
            response = self.session.post(
                urljoin(self.base_url, "/login"),
                data={'username': username, 'password': password},
                timeout=10
            )
            
            if response.status_code == 200 and "error" not in response.text.lower():
                self.logged_in = True
                self.username = username
                self.show_main_content()
                self.show_message("Login successful!")
                self.load_pages()  # Загружаем страницы сразу после входа
            else:
                self.show_message("Login failed. Check credentials.")
                
        except Exception as e:
            self.show_message(f"Connection error: {str(e)}")
    
    def show_main_content(self):
        # Показываем основной контент
        self.content_layout.opacity = 1
        self.login_layout.opacity = 0
    
    def logout(self, instance):
        try:
            self.session.get(urljoin(self.base_url, "/logout"))
        except:
            pass
        
        self.logged_in = False
        self.username = ""
        self.content_layout.opacity = 0
        self.login_layout.opacity = 1
        self.clear_data()
        self.show_message("Logged out")
    
    def show_pages(self, instance):
        self.load_pages()
    
    def load_pages(self):
        self.clear_data()
        self.add_data_label("Loading pages...", "Loading")
        
        def fetch_pages():
            try:
                response = self.session.get(urljoin(self.base_url, "/pages"), timeout=10)
                if response.status_code == 200:
                    # Парсим HTML для извлечения ссылок
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = soup.find_all('a')
                    
                    Clock.schedule_once(lambda dt: self.clear_data())
                    
                    for link in links:
                        href = link.get('href')
                        if href and 'view' in href:
                            text = link.get_text().strip()
                            if text:
                                Clock.schedule_once(lambda dt, t=text, h=href: self.add_page_button(t, h))
                else:
                    Clock.schedule_once(lambda dt: self.show_message("Failed to load pages"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_message(f"Error: {str(e)}"))
        
        threading.Thread(target=fetch_pages, daemon=True).start()
    
    def add_page_button(self, text, href):
        btn = Button(
            text=text,
            size_hint_y=None,
            height=50,
            background_color=(0.4, 0.4, 0.8, 1)
        )
        btn.bind(on_press=lambda x: self.view_page(href))
        self.data_layout.add_widget(btn)
    
    def view_page(self, href):
        try:
            response = self.session.get(urljoin(self.base_url, href), timeout=10)
            if response.status_code == 200:
                self.show_page_content(response.text)
            else:
                self.show_message("Failed to load page")
        except Exception as e:
            self.show_message(f"Error: {str(e)}")
    
    def show_page_content(self, content):
        # Создаем popup с содержимым страницы
        popup_layout = BoxLayout(orientation='vertical', padding=10)
        
        scroll = ScrollView(size_hint=(1, 1))
        content_label = Label(
            text=content[:1000] + "..." if len(content) > 1000 else content,
            size_hint_y=None,
            height=max(400, len(content) * 0.5),
            text_size=(Window.width - 40, None)
        )
        scroll.add_widget(content_label)
        popup_layout.add_widget(scroll)
        
        close_btn = Button(text='Close', size_hint_y=None, height=50)
        popup_layout.add_widget(close_btn)
        
        popup = Popup(title='Page Content', content=popup_layout, size_hint=(0.9, 0.9))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def check_updates(self, instance):
        self.clear_data()
        self.add_data_label("Checking for updates...", "Checking")
        
        def fetch_updates():
            try:
                response = self.session.get(urljoin(self.base_url, "/check_updates"), timeout=10)
                if response.status_code == 200:
                    Clock.schedule_once(lambda dt: self.clear_data())
                    Clock.schedule_once(lambda dt: self.add_data_label("Updates checked", "Success"))
                    # Можно добавить парсинг результатов
                else:
                    Clock.schedule_once(lambda dt: self.show_message("Failed to check updates"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_message(f"Error: {str(e)}"))
        
        threading.Thread(target=fetch_updates, daemon=True).start()
    
    def show_search(self, instance):
        # Создаем popup для поиска
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        search_input = TextInput(
            hint_text='Enter search term',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        popup_layout.add_widget(search_input)
        
        search_btn = Button(
            text='Search',
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.7, 0.3, 1)
        )
        
        def do_search(instance):
            query = search_input.text.strip()
            if query:
                popup.dismiss()
                self.perform_search(query)
        
        search_btn.bind(on_press=do_search)
        popup_layout.add_widget(search_btn)
        
        close_btn = Button(text='Cancel', size_hint_y=None, height=50)
        popup_layout.add_widget(close_btn)
        
        popup = Popup(title='Search', content=popup_layout, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def perform_search(self, query):
        self.clear_data()
        self.add_data_label(f"Searching for: {query}", "Searching")
        
        def fetch_search():
            try:
                response = self.session.get(
                    urljoin(self.base_url, f"/search?q={query}"),
                    timeout=10
                )
                if response.status_code == 200:
                    Clock.schedule_once(lambda dt: self.clear_data())
                    # Парсим результаты поиска
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = soup.find_all('a')
                    
                    for link in links:
                        href = link.get('href')
                        if href and 'view' in href:
                            text = link.get_text().strip()
                            if text:
                                Clock.schedule_once(lambda dt, t=text, h=href: self.add_page_button(t, h))
                else:
                    Clock.schedule_once(lambda dt: self.show_message("Search failed"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_message(f"Error: {str(e)}"))
        
        threading.Thread(target=fetch_search, daemon=True).start()
    
    def clear_data(self):
        self.data_layout.clear_widgets()
    
    def add_data_label(self, text, category="Info"):
        label = Label(
            text=f"{category}: {text}",
            size_hint_y=None,
            height=40,
            color=(0.8, 0.8, 0.8, 1)
        )
        self.data_layout.add_widget(label)
    
    def show_message(self, message):
        popup = Popup(
            title='Message',
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)

if __name__ == '__main__':
    UzakbaevNurzhanApp().run()