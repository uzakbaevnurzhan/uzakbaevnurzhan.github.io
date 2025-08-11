import os
import json
import threading
from datetime import datetime

from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.list import MDList, ThreeLineListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.relativelayout import MDRelativeLayout

import requests
from kivy.clock import Clock


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        
        layout = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(20),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint_x=0.8
        )
        
        # Logo/Title
        title = MDLabel(
            text="Mirror App",
            theme_text_color="Primary",
            font_style="H4",
            halign="center",
            size_hint_y=None,
            height=dp(40)
        )
        
        # Login form
        self.username_field = MDTextField(
            hint_text="Логин",
            icon_left="account",
            mode="outlined",
            size_hint_y=None,
            height=dp(56)
        )
        
        self.password_field = MDTextField(
            hint_text="Пароль",
            icon_left="lock",
            password=True,
            mode="outlined",
            size_hint_y=None,
            height=dp(56)
        )
        
        # Server URL field
        self.server_field = MDTextField(
            hint_text="Адрес сервера (например: http://192.168.1.100:5000)",
            icon_left="server",
            mode="outlined",
            size_hint_y=None,
            height=dp(56),
            text="http://localhost:5000"
        )
        
        login_btn = MDRaisedButton(
            text="Войти",
            size_hint_y=None,
            height=dp(40),
            on_release=self.login
        )
        
        layout.add_widget(title)
        layout.add_widget(self.username_field)
        layout.add_widget(self.password_field)
        layout.add_widget(self.server_field)
        layout.add_widget(login_btn)
        
        self.add_widget(layout)
    
    def login(self, *args):
        username = self.username_field.text
        password = self.password_field.text
        server_url = self.server_field.text.rstrip('/')
        
        if not all([username, password, server_url]):
            self.show_dialog("Ошибка", "Заполните все поля")
            return
        
        # Store server URL for future requests
        self.parent.parent.server_url = server_url
        
        # Attempt login
        try:
            response = requests.post(
                f"{server_url}/login",
                data={"username": username, "password": password},
                allow_redirects=False,
                timeout=10
            )
            
            if response.status_code == 302:  # Redirect indicates successful login
                # Store session cookies
                self.parent.parent.session = requests.Session()
                self.parent.parent.session.cookies.update(response.cookies)
                
                # Switch to main screen
                self.parent.current = "main"
            else:
                self.show_dialog("Ошибка", "Неверные учётные данные")
                
        except requests.exceptions.RequestException as e:
            self.show_dialog("Ошибка", f"Ошибка подключения: {str(e)}")
    
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "main"
        self.pages_data = []
        
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Mirror App",
            right_action_items=[
                ["refresh", lambda x: self.refresh_data()],
                ["logout", lambda x: self.logout()]
            ]
        )
        
        # Navigation bar
        self.nav_bar = MDNavigationBar(
            on_item_press=self.on_nav_item_press
        )
        
        nav_item_pages = MDNavigationItem(
            icon="file-multiple",
            text="Страницы"
        )
        nav_item_updates = MDNavigationItem(
            icon="update",
            text="Обновления"
        )
        nav_item_chat = MDNavigationItem(
            icon="chat",
            text="Чат"
        )
        nav_item_audit = MDNavigationItem(
            icon="history",
            text="Журнал"
        )
        
        self.nav_bar.add_widget(nav_item_pages)
        self.nav_bar.add_widget(nav_item_updates)
        self.nav_bar.add_widget(nav_item_chat)
        self.nav_bar.add_widget(nav_item_audit)
        
        # Content area
        self.content_area = MDScreenManager()
        self.setup_content_screens()
        
        layout.add_widget(top_bar)
        layout.add_widget(self.content_area)
        layout.add_widget(self.nav_bar)
        
        self.add_widget(layout)
        
        # Auto refresh every 30 seconds
        Clock.schedule_interval(self.refresh_data, 30)
    
    def setup_content_screens(self):
        # Pages screen
        pages_screen = MDScreen(name="pages")
        pages_layout = MDBoxLayout(orientation="vertical", padding=dp(10))
        
        self.pages_scroll = MDScrollView()
        self.pages_list = MDList()
        self.pages_scroll.add_widget(self.pages_list)
        pages_layout.add_widget(self.pages_scroll)
        
        pages_screen.add_widget(pages_layout)
        self.content_area.add_widget(pages_screen)
        
        # Updates screen  
        updates_screen = MDScreen(name="updates")
        updates_layout = MDBoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        
        check_btn = MDRaisedButton(
            text="Проверить обновления",
            size_hint_y=None,
            height=dp(40),
            on_release=self.check_updates
        )
        
        update_btn = MDRaisedButton(
            text="Обновить локально",
            size_hint_y=None,
            height=dp(40),
            on_release=self.do_update
        )
        
        backup_btn = MDRaisedButton(
            text="Скачать бекап",
            size_hint_y=None,
            height=dp(40),
            on_release=self.download_backup
        )
        
        self.updates_info = MDLabel(
            text="Нажмите 'Проверить обновления' для начала",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(60)
        )
        
        updates_layout.add_widget(check_btn)
        updates_layout.add_widget(update_btn)
        updates_layout.add_widget(backup_btn)
        updates_layout.add_widget(self.updates_info)
        
        updates_screen.add_widget(updates_layout)
        self.content_area.add_widget(updates_screen)
        
        # Chat screen
        chat_screen = MDScreen(name="chat")
        chat_layout = MDBoxLayout(orientation="vertical", padding=dp(10))
        
        self.chat_scroll = MDScrollView()
        self.chat_list = MDList()
        self.chat_scroll.add_widget(self.chat_list)
        
        # Chat input
        chat_input_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(10))
        self.chat_input = MDTextField(
            hint_text="Введите сообщение...",
            mode="outlined"
        )
        send_btn = MDIconButton(
            icon="send",
            on_release=self.send_message
        )
        
        chat_input_layout.add_widget(self.chat_input)
        chat_input_layout.add_widget(send_btn)
        
        chat_layout.add_widget(self.chat_scroll)
        chat_layout.add_widget(chat_input_layout)
        
        chat_screen.add_widget(chat_layout)
        self.content_area.add_widget(chat_screen)
        
        # Audit screen
        audit_screen = MDScreen(name="audit")
        audit_layout = MDBoxLayout(orientation="vertical", padding=dp(10))
        
        self.audit_scroll = MDScrollView()
        self.audit_list = MDList()
        self.audit_scroll.add_widget(self.audit_list)
        audit_layout.add_widget(self.audit_scroll)
        
        audit_screen.add_widget(audit_layout)
        self.content_area.add_widget(audit_screen)
        
        # Set default screen
        self.content_area.current = "pages"
    
    def on_nav_item_press(self, item):
        # Map navigation items to screens
        nav_map = {
            "Страницы": "pages",
            "Обновления": "updates", 
            "Чат": "chat",
            "Журнал": "audit"
        }
        
        screen_name = nav_map.get(item.text)
        if screen_name:
            self.content_area.current = screen_name
            
            # Load data for specific screens
            if screen_name == "pages":
                self.load_pages()
            elif screen_name == "chat":
                self.load_chat()
            elif screen_name == "audit":
                self.load_audit()
    
    def refresh_data(self, *args):
        current_screen = self.content_area.current
        if current_screen == "pages":
            self.load_pages()
        elif current_screen == "chat":
            self.load_chat()
        elif current_screen == "audit":
            self.load_audit()
    
    def load_pages(self):
        try:
            app = self.parent.parent
            response = app.session.get(f"{app.server_url}/pages", timeout=10)
            if response.status_code == 200:
                # Parse HTML to extract page URLs (simplified)
                import re
                urls = re.findall(r'href="/view\?page=([^"]+)"', response.text)
                
                self.pages_list.clear_widgets()
                for url in urls:
                    from urllib.parse import unquote
                    decoded_url = unquote(url)
                    
                    item = ThreeLineListItem(
                        text=decoded_url,
                        secondary_text="Нажмите для просмотра",
                        tertiary_text=f"Обновлено: {datetime.now().strftime('%H:%M')}",
                        on_release=lambda x, u=decoded_url: self.view_page(u)
                    )
                    self.pages_list.add_widget(item)
                    
        except Exception as e:
            self.show_dialog("Ошибка", f"Не удалось загрузить страницы: {str(e)}")
    
    def load_chat(self):
        try:
            app = self.parent.parent
            response = app.session.get(f"{app.server_url}/chat", timeout=10)
            if response.status_code == 200:
                # Parse chat messages from HTML (simplified)
                import re
                messages = re.findall(r'<b>([^<]+)</b>[^:]*:[^<]*<[^>]*>[^<]*</[^>]*>:[^<]*([^<]+)', response.text)
                
                self.chat_list.clear_widgets()
                for user, message in messages[-20:]:  # Show last 20 messages
                    item = ThreeLineListItem(
                        text=user,
                        secondary_text=message,
                        tertiary_text=datetime.now().strftime("%H:%M")
                    )
                    self.chat_list.add_widget(item)
                    
        except Exception as e:
            self.show_dialog("Ошибка", f"Не удалось загрузить чат: {str(e)}")
    
    def load_audit(self):
        try:
            app = self.parent.parent
            response = app.session.get(f"{app.server_url}/audit", timeout=10)
            if response.status_code == 200:
                # Parse audit log from HTML (simplified)
                import re
                entries = re.findall(r'<b>([^<]+)</b>[^—]*—[^<]*([^<]+)<small[^>]*>[^<]*([^<]*)</small>', response.text)
                
                self.audit_list.clear_widgets()
                for user, action, timestamp in entries[-20:]:  # Show last 20 entries
                    item = ThreeLineListItem(
                        text=f"{user} - {action}",
                        secondary_text=timestamp,
                        tertiary_text="Запись журнала"
                    )
                    self.audit_list.add_widget(item)
                    
        except Exception as e:
            self.show_dialog("Ошибка", f"Не удалось загрузить журнал: {str(e)}")
    
    def view_page(self, url):
        # Simple dialog showing page URL for now
        self.show_dialog("Страница", f"URL: {url}\n\nОткрытие страниц будет реализовано в следующей версии.")
    
    def check_updates(self, *args):
        try:
            app = self.parent.parent
            response = app.session.get(f"{app.server_url}/check_updates", timeout=30)
            if response.status_code == 200:
                data = response.json()
                changed = len(data.get('changed', []))
                new = len(data.get('new', []))
                removed = len(data.get('removed', []))
                
                self.updates_info.text = f"Изменено: {changed}\nНовых: {new}\nУдалено: {removed}"
                
                if changed + new > 0:
                    self.show_dialog("Обновления", f"Найдено изменений: {changed + new}")
                else:
                    self.show_dialog("Обновления", "Изменений не найдено")
                    
        except Exception as e:
            self.show_dialog("Ошибка", f"Не удалось проверить обновления: {str(e)}")
    
    def do_update(self, *args):
        try:
            app = self.parent.parent
            response = app.session.post(f"{app.server_url}/do_update", timeout=60)
            if response.status_code == 200:
                data = response.json()
                self.show_dialog("Обновление", data.get('msg', 'Обновление завершено'))
            else:
                self.show_dialog("Ошибка", "Не удалось выполнить обновление")
                
        except Exception as e:
            self.show_dialog("Ошибка", f"Ошибка обновления: {str(e)}")
    
    def download_backup(self, *args):
        self.show_dialog("Бекап", "Функция скачивания бекапа будет добавлена в следующей версии")
    
    def send_message(self, *args):
        message = self.chat_input.text.strip()
        if not message:
            return
            
        try:
            app = self.parent.parent
            response = app.session.post(
                f"{app.server_url}/chat_send",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.chat_input.text = ""
                self.load_chat()  # Refresh chat
            else:
                self.show_dialog("Ошибка", "Не удалось отправить сообщение")
                
        except Exception as e:
            self.show_dialog("Ошибка", f"Ошибка отправки: {str(e)}")
    
    def logout(self):
        self.parent.current = "login"
    
    def show_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class MirrorApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_url = ""
        self.session = None
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        
        sm = MDScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(MainScreen())
        
        return sm


if __name__ == "__main__":
    MirrorApp().run()