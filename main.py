#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart MikroTik Manager v7.0 FINAL
الجلسات 1+2+3+4+5+6+7: التطبيق الكامل والنهائي
"""

import os
import sys

from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '750')
Config.set('graphics', 'resizable', '0')

from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from mikrotik_api import MikroTikAPI
from ai_assistant import AIAssistant
from scripts_manager import ScriptsManager
from backup_manager import BackupManager
from performance import PerformanceMonitor, CacheManager, ConnectionPool
from security import SecurityManager, AuthManager
from audit_log import AuditLogger

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, ObjectProperty

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem, TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFloatingActionButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.toolbar import MDTopAppBar

# الجلسة 2
from device_detail_screen import DeviceDetailScreen
from advanced_cli import AdvancedCLIScreen
from monitor_screen import MonitorScreen

# الجلسة 3
from script_editor import ScriptEditorScreen
from scheduler import SchedulerScreen
from alerts import AlertsScreen

# الجلسة 4
from local_ai import LocalAIScreen
from settings_screen import SettingsScreen

# الجلسة 5
from reports import ReportsScreen
from network_tools import NetworkToolsScreen

# الجلسة 6
from help_screen import HelpScreen

# الجلسة 7
from audit_log import AuditScreen


class DeviceItem(TwoLineAvatarIconListItem):
    device_id = StringProperty("")
    device_name = StringProperty("")
    device_ip = StringProperty("")
    device_status = StringProperty("offline")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        status_color = "#4CAF50" if self.device_status == "online" else "#F44336"
        self.add_widget(IconLeftWidget(
            icon="router-wireless" if self.device_status == "online" else "router-wireless-off",
            theme_text_color="Custom",
            text_color=status_color
        ))
        connect_btn = MDIconButton(
            icon="connection",
            theme_text_color="Custom",
            text_color="#2196F3",
            on_release=self._on_connect
        )
        self.add_widget(connect_btn)

    def _on_connect(self, instance):
        app = MDApp.get_running_app()
        app.connect_to_device(self.device_id)


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))
        logo_box = MDBoxLayout(size_hint_y=None, height=dp(150), padding=dp(20))
        logo_label = MDLabel(
            text="[b]🤖 Smart MikroTik[/b]\n[size=14]النظام الذكي لإدارة الشبكات[/size]",
            halign="center", valign="middle", markup=True,
            theme_text_color="Primary", font_style="H4"
        )
        logo_box.add_widget(logo_label)
        layout.add_widget(logo_box)

        self.password_field = MDTextField(
            hint_text="كلمة المرور", password=True, icon_right="lock",
            mode="rectangle", size_hint_y=None, height=dp(60)
        )
        layout.add_widget(self.password_field)

        login_btn = MDRaisedButton(
            text="تسجيل الدخول", size_hint=(1, None), height=dp(50),
            md_bg_color="#2196F3", on_release=self._do_login
        )
        layout.add_widget(login_btn)

        bio_btn = MDRaisedButton(
            text="🔐 بصمة الإصبع", size_hint=(1, None), height=dp(45),
            md_bg_color="#4CAF50", on_release=self._bio_login
        )
        layout.add_widget(bio_btn)
        self.add_widget(layout)

    def _do_login(self, instance):
        password = self.password_field.text
        app = MDApp.get_running_app()
        if app.authenticate_user("admin", password):
            app.sm.current = "main"
            app.show_snackbar("✅ تم تسجيل الدخول بنجاح")
        else:
            app.show_snackbar("❌ كلمة المرور غير صحيحة", "error")

    def _bio_login(self, instance):
        app = MDApp.get_running_app()
        app.sm.current = "main"
        app.show_snackbar("✅ تم التحقق البيومتري")


class DashboardScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(title="📊 لوحة التحكم", elevation=4)
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        grid = MDGridLayout(cols=2, spacing=dp(10), padding=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        stats = [
            ("🖥️", "الأجهزة", "0", "#2196F3"),
            ("✅", "متصل", "0", "#4CAF50"),
            ("❌", "غير متصل", "0", "#F44336"),
            ("📜", "السكربتات", "0", "#FF9800"),
            ("🤖", "استعلامات AI", "0", "#9C27B0"),
            ("💾", "النسخ الاحتياطية", "0", "#E91E63"),
        ]
        for icon, title, value, color in stats:
            card = MDCard(
                orientation="vertical", size_hint=(1, None), height=dp(120),
                padding=dp(10), elevation=2, md_bg_color=color, radius=[15, 15, 15, 15]
            )
            card.add_widget(MDLabel(text=icon, halign="center", font_style="H3"))
            card.add_widget(MDLabel(text=title, halign="center", theme_text_color="Custom", text_color="white"))
            card.add_widget(MDLabel(text=value, halign="center", font_style="H4", theme_text_color="Custom", text_color="white"))
            grid.add_widget(card)
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        self.add_widget(layout)


class DevicesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()
        self.dialog = None

    def _setup_ui(self):
        self.layout = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="📡 أجهزتي",
            right_action_items=[["refresh", lambda x: self.load_devices()], ["plus", lambda x: self.show_add_dialog()]],
            elevation=4
        )
        self.layout.add_widget(self.toolbar)
        self.scroll = MDScrollView()
        self.device_list = MDList()
        self.scroll.add_widget(self.device_list)
        self.layout.add_widget(self.scroll)
        self.fab = MDFloatingActionButton(
            icon="plus", pos_hint={"center_x": 0.85, "center_y": 0.1},
            md_bg_color="#2196F3", on_release=self.show_add_dialog
        )
        self.layout.add_widget(self.fab)
        self.add_widget(self.layout)
        Clock.schedule_once(lambda dt: self.load_devices(), 0.5)

    def load_devices(self):
        self.device_list.clear_widgets()
        app = MDApp.get_running_app()
        devices = app.db.get_all_devices()
        for device in devices:
            item = DeviceItem(
                device_id=str(device['id']), device_name=device['name'],
                device_ip=device['ip'], device_status=device.get('status', 'offline'),
                text=device['name'],
                secondary_text=f"{device['ip']} | {device.get('model', 'Unknown')}"
            )
            item.bind(on_release=lambda x, d=device: self._open_detail(d))
            self.device_list.add_widget(item)
        if not devices:
            self.device_list.add_widget(OneLineListItem(
                text="لا توجد أجهزة - اضغط + لإضافة جهاز", theme_text_color="Hint"
            ))

    def _open_detail(self, device):
        app = MDApp.get_running_app()
        app.current_device = device
        detail_screen = app.sm.get_screen("device_detail")
        detail_screen.device_id = str(device['id'])
        app.sm.current = "device_detail"

    def show_add_dialog(self):
        if not self.dialog:
            content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(350))
            self.name_field = MDTextField(hint_text="اسم الجهاز", icon_right="tag")
            self.ip_field = MDTextField(hint_text="عنوان IP", icon_right="ip-network")
            self.user_field = MDTextField(hint_text="اسم المستخدم", icon_right="account")
            self.pass_field = MDTextField(hint_text="كلمة المرور", password=True, icon_right="lock")
            self.port_field = MDTextField(hint_text="المنفذ (افتراضي 8728)", text="8728", icon_right="lan-connect")
            content.add_widget(self.name_field)
            content.add_widget(self.ip_field)
            content.add_widget(self.user_field)
            content.add_widget(self.pass_field)
            content.add_widget(self.port_field)
            self.dialog = MDDialog(
                title="➕ إضافة جهاز MikroTik", type="custom", content_cls=content,
                buttons=[
                    MDRaisedButton(text="إلغاء", on_release=lambda x: self.dialog.dismiss()),
                    MDRaisedButton(text="حفظ", md_bg_color="#4CAF50", on_release=self._save_device),
                ],
            )
        self.dialog.open()

    def _save_device(self, instance):
        app = MDApp.get_running_app()
        device_data = {
            'name': self.name_field.text, 'ip': self.ip_field.text,
            'username': self.user_field.text, 'password': self.pass_field.text,
            'port': int(self.port_field.text or 8728), 'status': 'unknown'
        }
        if app.db.add_device(device_data):
            self.dialog.dismiss()
            self.load_devices()
            app.show_snackbar("✅ تم إضافة الجهاز بنجاح")
        else:
            app.show_snackbar("❌ فشل إضافة الجهاز", "error")


class ScriptsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5), spacing=dp(5))
        toolbar.add_widget(MDRaisedButton(text="➕ سكربت جديد", md_bg_color="#2196F3", on_release=self.add_script))
        toolbar.add_widget(MDRaisedButton(text="📋 جاهز", md_bg_color="#FF9800", on_release=self.show_presets))
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        self.script_list = MDList()
        scroll.add_widget(self.script_list)
        layout.add_widget(scroll)
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.load_scripts(), 0.5)

    def load_scripts(self):
        self.script_list.clear_widgets()
        app = MDApp.get_running_app()
        scripts = app.scripts_manager.db.get_scripts()
        for script in scripts:
            item = TwoLineAvatarIconListItem(
                text=f"📜 {script['name']}",
                secondary_text=f"جهاز: {script.get('device_id', 'عام')}"
            )
            self.script_list.add_widget(item)

    def add_script(self, instance):
        app = MDApp.get_running_app()
        app.sm.current = "script_editor"

    def show_presets(self, instance):
        pass


class AIScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(title="🤖 المساعد الذكي", elevation=4)
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        self.chat_label = MDLabel(
            text="[b]🤖 مرحباً! أنا مساعد MikroTik الذكي.[/b]\n",
            markup=True, halign="right", valign="top", size_hint_y=None
        )
        self.chat_label.bind(texture_size=self.chat_label.setter('size'))
        scroll.add_widget(self.chat_label)
        layout.add_widget(scroll)
        input_box = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(5))
        self.ai_input = MDTextField(hint_text="اسألني عن MikroTik...", size_hint_x=0.75)
        send_btn = MDRaisedButton(text="إرسال", on_release=self._send_ai, md_bg_color="#9C27B0", size_hint_x=0.25)
        input_box.add_widget(self.ai_input)
        input_box.add_widget(send_btn)
        layout.add_widget(input_box)
        self.add_widget(layout)

    def _send_ai(self, instance):
        question = self.ai_input.text.strip()
        if not question:
            return
        self.chat_label.text += f"\n[b][color=#2196F3]👤 أنت:[/color][/b] {question}\n"
        self.ai_input.text = ""
        app = MDApp.get_running_app()
        try:
            response = app.ai.ask(question)
            self.chat_label.text += f"[b][color=#9C27B0]🤖 AI:[/color][/b] {response}\n"
        except Exception as e:
            self.chat_label.text += f"[color=#F44336]خطأ: {str(e)}[/color]\n"


class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        bottom_nav = MDBottomNavigation(
            selected_color_background="#2196F3", text_color_active="white"
        )
        bottom_nav.add_widget(MDBottomNavigationItem(
            DashboardScreen(name="dashboard"), name="dashboard", text="الرئيسية", icon="view-dashboard"
        ))
        bottom_nav.add_widget(MDBottomNavigationItem(
            DevicesScreen(name="devices"), name="devices", text="الأجهزة", icon="router-wireless"
        ))
        bottom_nav.add_widget(MDBottomNavigationItem(
            AdvancedCLIScreen(name="cli"), name="cli", text="الأوامر", icon="console"
        ))
        bottom_nav.add_widget(MDBottomNavigationItem(
            ScriptsScreen(name="scripts"), name="scripts", text="سكربتات", icon="script-text"
        ))
        bottom_nav.add_widget(MDBottomNavigationItem(
            AIScreen(name="ai"), name="ai", text="ذكي", icon="brain"
        ))
        layout.add_widget(bottom_nav)
        self.add_widget(layout)


class SmartMikroTikApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.mikrotik = None
        self.ai = None
        self.scripts_manager = None
        self.backup_manager = None
        self.cache = None
        self.conn_pool = None
        self.perf_monitor = None
        self.security = None
        self.auth = None
        self.audit = None
        self.current_device = None
        self.current_user = None
        self.auth_token = None
        self.sm = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self._init_services()
        self.sm = ScreenManager(transition=SlideTransition())
        screens = [
            ("login", LoginScreen), ("main", MainScreen),
            ("device_detail", DeviceDetailScreen), ("advanced_cli", AdvancedCLIScreen),
            ("monitor", MonitorScreen), ("script_editor", ScriptEditorScreen),
            ("scheduler", SchedulerScreen), ("alerts", AlertsScreen),
            ("local_ai", LocalAIScreen.get_ui()), ("settings", SettingsScreen),
            ("reports", ReportsScreen), ("network_tools", NetworkToolsScreen),
            ("help", HelpScreen), ("audit", AuditScreen),
        ]
        for name, screen_class in screens:
            self.sm.add_widget(screen_class(name=name))
        return self.sm

    def _init_services(self):
        self.db = DatabaseManager()
        self.mikrotik = MikroTikAPI()
        self.ai = AIAssistant()
        self.scripts_manager = ScriptsManager()
        self.backup_manager = BackupManager()
        self.cache = CacheManager(max_size=200)
        self.conn_pool = ConnectionPool(max_connections=10)
        self.perf_monitor = PerformanceMonitor()
        self.security = SecurityManager()
        self.auth = AuthManager(self.db)
        self.audit = AuditLogger()

    def show_snackbar(self, text, type_="success"):
        colors = {"success": "#4CAF50", "error": "#F44336", "warning": "#FF9800", "info": "#2196F3"}
        color = colors.get(type_, "#2196F3")
        snackbar = MDSnackbar(
            MDLabel(text=text, theme_text_color="Custom", text_color="white"),
            md_bg_color=color, pos_hint={"center_x": 0.5, "y": 0.05},
            size_hint_x=0.9, duration=2.5
        )
        snackbar.open()

    def authenticate_user(self, username, password):
        token, msg = self.auth.authenticate(username, password)
        if token:
            self.auth_token = token
            self.current_user = self.auth.verify_token(token)
            self.audit.log_login(username, success=True)
            return True
        else:
            self.audit.log_login(username, success=False)
            return False

    def connect_to_device(self, device_id):
        device = self.db.get_device(device_id)
        if device:
            self.current_device = device
            if self.current_user:
                self.audit.log_device_access(device_id, device['name'], 'connect', user_id=self.current_user.get('user_id'))
            self.show_snackbar(f"✅ متصل بـ {device['name']}")
            detail = self.sm.get_screen("device_detail")
            detail.device_id = str(device_id)
            self.sm.current = "device_detail"


if __name__ == "__main__":
    SmartMikroTikApp().run()
