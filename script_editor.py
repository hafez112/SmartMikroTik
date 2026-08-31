#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""محرر السكربتات المتقدم"""

import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog

from scripts_manager import ScriptsManager


class ScriptEditorScreen(MDScreen):
    current_script_id = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scripts_manager = ScriptsManager()
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="📝 محرر السكربتات", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["play", lambda x: self._run_script()], ["content-save", lambda x: self._save_script()]],
            elevation=4
        )
        layout.add_widget(self.toolbar)

        info_card = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(10), spacing=dp(10))
        self.script_name_field = MDTextField(hint_text="اسم السكربت", size_hint_x=0.4, mode="rectangle")
        self.script_device_field = MDTextField(hint_text="رقم الجهاز", size_hint_x=0.3, mode="rectangle")
        self.script_schedule = MDTextField(hint_text="الجدولة", size_hint_x=0.3, mode="rectangle")
        info_card.add_widget(self.script_name_field)
        info_card.add_widget(self.script_device_field)
        info_card.add_widget(self.script_schedule)
        layout.add_widget(info_card)

        editor_card = MDCard(size_hint=(1, 0.6), padding=dp(10), elevation=2)
        self.script_editor = MDTextField(
            hint_text="# اكتب سكربت RouterOS هنا...", multiline=True,
            mode="rectangle", size_hint=(1, 1)
        )
        editor_card.add_widget(self.script_editor)
        layout.add_widget(editor_card)

        ai_box = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5), spacing=dp(5))
        ai_box.add_widget(MDLabel(text="🤖 توليد ذكي:", size_hint_x=0.2, halign="right"))
        ai_buttons = [
            ("🔥 فايروول", "اكتب سكربت فايروول شامل"),
            ("📡 هوتسبوت", "اكتب سكربت هوتسبوت كامل"),
            ("⚡ QoS", "اكتب سكربت QoS"),
            ("🔒 أمان", "اكتب سكربت أمان متكامل"),
        ]
        for text, prompt in ai_buttons:
            btn = MDRaisedButton(text=text, size_hint_x=0.2, md_bg_color="#9C27B0", on_release=lambda x, p=prompt: self._generate_with_ai(p))
            ai_box.add_widget(btn)
        layout.add_widget(ai_box)

        result_card = MDCard(size_hint=(1, 0.25), padding=dp(10), elevation=1, md_bg_color="#1A1A1A")
        self.result_label = MDLabel(text="نتيجة التنفيذ...", theme_text_color="Secondary", markup=True, halign="right", valign="top", size_hint_y=None)
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        scroll = MDScrollView()
        scroll.add_widget(self.result_label)
        result_card.add_widget(scroll)
        layout.add_widget(result_card)
        self.add_widget(layout)

    def _generate_with_ai(self, prompt):
        self.result_label.text = "[color=#9C27B0]🤖 جاري التوليد...[/color]"
        def generate():
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            try:
                script = app.ai.generate_script(prompt)
                Clock.schedule_once(lambda dt: self._insert_script(script), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_result(f"[color=#F44336]خطأ: {str(e)}[/color]"), 0)
        threading.Thread(target=generate, daemon=True).start()

    def _insert_script(self, script):
        self.script_editor.text = script
        self._show_result("[color=#4CAF50]✅ تم التوليد[/color]")

    def _run_script(self):
        content = self.script_editor.text.strip()
        if not content:
            self._show_result("[color=#F44336]❌ السكربت فارغ[/color]")
            return
        device_id = self.script_device_field.text.strip()
        device = None
        if device_id:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            device = app.db.get_device(device_id)
        self._show_result("[color=#2196F3]⏳ جاري التنفيذ...[/color]")
        def run():
            try:
                if device:
                    from mikrotik_api import MikroTikAPI
                    api = MikroTikAPI()
                    result = api._execute_ssh_command(device, content)
                    Clock.schedule_once(lambda dt: self._show_result(f"[color=#4CAF50]✅ النتيجة:\n{result}[/color]"), 0)
                else:
                    Clock.schedule_once(lambda dt: self._show_result("[color=#FF9800]⚠️ لا يوجد جهاز[/color]"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_result(f"[color=#F44336]❌ خطأ: {str(e)}[/color]"), 0)
        threading.Thread(target=run, daemon=True).start()

    def _save_script(self):
        name = self.script_name_field.text.strip()
        content = self.script_editor.text.strip()
        if not name or not content:
            self._show_result("[color=#F44336]❌ الاسم والمحتوى مطلوبان[/color]")
            return
        script_data = {
            'name': name, 'content': content,
            'device_id': self.script_device_field.text.strip() or None,
            'schedule': self.script_schedule.text.strip() or None
        }
        if self.scripts_manager.create_script(script_data):
            self._show_result("[color=#4CAF50]✅ تم الحفظ[/color]")
        else:
            self._show_result("[color=#F44336]❌ فشل الحفظ[/color]")

    def _show_result(self, text):
        self.result_label.text = text

    def _go_back(self):
        self.manager.current = "main"
