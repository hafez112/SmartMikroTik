#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إعدادات التطبيق المتقدمة"""

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.selectioncontrol import MDSwitch

from database import DatabaseManager


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(title="⚙️ الإعدادات", left_action_items=[["arrow-right", lambda x: self._go_back()]], elevation=4)
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        content.add_widget(MDLabel(text="[b]🌐 إعدادات الاتصال[/b]", markup=True, font_style="H6"))
        conn_card = MDCard(padding=dp(15), elevation=2, size_hint_y=None, height=dp(200))
        conn_layout = MDBoxLayout(orientation="vertical", spacing=dp(10))
        self.api_timeout = MDTextField(hint_text="مهلة API (ثواني)", text="10", mode="rectangle")
        self.ssh_timeout = MDTextField(hint_text="مهلة SSH (ثواني)", text="30", mode="rectangle")
        self.retry_count = MDTextField(hint_text="عدد المحاولات", text="3", mode="rectangle")
        conn_layout.add_widget(self.api_timeout)
        conn_layout.add_widget(self.ssh_timeout)
        conn_layout.add_widget(self.retry_count)
        conn_card.add_widget(conn_layout)
        content.add_widget(conn_card)

        content.add_widget(MDLabel(text="[b]🤖 إعدادات AI[/b]", markup=True, font_style="H6"))
        ai_card = MDCard(padding=dp(15), elevation=2, size_hint_y=None, height=dp(200))
        ai_layout = MDBoxLayout(orientation="vertical", spacing=dp(10))
        self.ai_api_key = MDTextField(hint_text="مفتاح API", password=True, mode="rectangle")
        self.ai_url = MDTextField(hint_text="رابط API", text="https://api.groq.com/openai/v1/chat/completions", mode="rectangle")
        self.ai_model = MDTextField(hint_text="النموذج", text="llama-3.1-70b-versatile", mode="rectangle")
        ai_layout.add_widget(self.ai_api_key)
        ai_layout.add_widget(self.ai_url)
        ai_layout.add_widget(self.ai_model)
        ai_card.add_widget(ai_layout)
        content.add_widget(ai_card)

        content.add_widget(MDLabel(text="[b]🎨 المظهر[/b]", markup=True, font_style="H6"))
        theme_card = MDCard(padding=dp(15), elevation=2, size_hint_y=None, height=dp(120))
        theme_layout = MDBoxLayout(orientation="vertical", spacing=dp(10))
        self.dark_mode = MDSwitch(active=True)
        dark_row = MDBoxLayout(size_hint_y=None, height=dp(50))
        dark_row.add_widget(MDLabel(text="الوضع الداكن", halign="right"))
        dark_row.add_widget(self.dark_mode)
        theme_layout.add_widget(dark_row)
        theme_card.add_widget(theme_layout)
        content.add_widget(theme_card)

        content.add_widget(MDLabel(text="[b]🔒 الأمان[/b]", markup=True, font_style="H6"))
        sec_card = MDCard(padding=dp(15), elevation=2, size_hint_y=None, height=dp(120))
        sec_layout = MDBoxLayout(orientation="vertical", spacing=dp(10))
        self.app_password = MDTextField(hint_text="كلمة مرور التطبيق", password=True, mode="rectangle")
        sec_layout.add_widget(self.app_password)
        sec_card.add_widget(sec_layout)
        content.add_widget(sec_card)

        buttons = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        buttons.add_widget(MDRaisedButton(text="💾 حفظ", md_bg_color="#4CAF50", size_hint=(0.5, 1), on_release=self._save_settings))
        buttons.add_widget(MDRaisedButton(text="🔄 استعادة", md_bg_color="#F44336", size_hint=(0.5, 1), on_release=self._reset_defaults))
        content.add_widget(buttons)

        content.add_widget(MDLabel(text="[b]ℹ️ حول التطبيق[/b]", markup=True, font_style="H6"))
        info_card = MDCard(padding=dp(15), elevation=2, size_hint_y=None, height=dp(120))
        info_layout = MDBoxLayout(orientation="vertical", spacing=dp(5))
        info_layout.add_widget(MDLabel(text="[b]Smart MikroTik Manager v7.0[/b]", markup=True, halign="center", font_style="H6"))
        info_layout.add_widget(MDLabel(text="النظام الذكي لإدارة أجهزة MikroTik", halign="center", theme_text_color="Secondary"))
        info_layout.add_widget(MDLabel(text="© 2024", halign="center", theme_text_color="Hint", font_style="Caption"))
        info_card.add_widget(info_layout)
        content.add_widget(info_card)

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self._load_settings(), 0.5)

    def _load_settings(self):
        try:
            settings = self.db.get_ai_settings()
            if settings.get('api_key'):
                self.ai_api_key.text = settings['api_key']
            if settings.get('api_url'):
                self.ai_url.text = settings['api_url']
            if settings.get('model'):
                self.ai_model.text = settings['model']
        except:
            pass

    def _save_settings(self, instance):
        settings = {
            'api_key': self.ai_api_key.text, 'api_url': self.ai_url.text, 'model': self.ai_model.text
        }
        try:
            self.db.update_ai_settings(settings)
            from kivymd.app import MDApp
            MDApp.get_running_app().show_snackbar("✅ تم الحفظ")
        except Exception as e:
            from kivymd.app import MDApp
            MDApp.get_running_app().show_snackbar(f"❌ خطأ: {str(e)}", "error")

    def _reset_defaults(self, instance):
        self.api_timeout.text = "10"
        self.ssh_timeout.text = "30"
        self.retry_count.text = "3"
        self.ai_url.text = "https://api.groq.com/openai/v1/chat/completions"
        self.ai_model.text = "llama-3.1-70b-versatile"
        self.dark_mode.active = True
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("🔄 تمت الاستعادة")

    def _go_back(self):
        self.manager.current = "main"
