#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""موجه الأوامر المتقدم"""

import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ListProperty

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar

from mikrotik_api import MikroTikAPI


class AdvancedCLIScreen(MDScreen):
    command_history = ListProperty([])
    history_index = -1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = MikroTikAPI()
        self.device = None
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(
            title="💻 موجه الأوامر", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["history", lambda x: self._show_history()], ["content-save", lambda x: None]],
            elevation=4
        )
        layout.add_widget(toolbar)

        self.device_bar = MDBoxLayout(size_hint_y=None, height=dp(35), padding=dp(5), md_bg_color="#1A237E")
        self.device_label = MDLabel(text="🔴 غير متصل", theme_text_color="Custom", text_color="white", halign="right")
        self.device_bar.add_widget(self.device_label)
        layout.add_widget(self.device_bar)

        output_card = MDBoxLayout(orientation="vertical", padding=dp(5))
        tools = MDBoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        quick_cmds = [
            ("📊", "system resource print", "#4CAF50"), ("🌐", "ip address print", "#2196F3"),
            ("👥", "ip hotspot user print", "#FF9800"), ("📡", "interface print", "#9C27B0"),
            ("🔥", "ip firewall filter print", "#F44336"), ("⚡", "ping 8.8.8.8", "#00BCD4"),
        ]
        for icon, cmd, color in quick_cmds:
            btn = MDIconButton(icon="code-tags", theme_text_color="Custom", text_color=color, on_release=lambda x, c=cmd: self._quick_command(c))
            tools.add_widget(btn)
        output_card.add_widget(tools)

        self.output_scroll = MDScrollView()
        self.output_label = MDLabel(
            text="[b]🤖 Smart MikroTik CLI v2.0[/b]\n[color=#4CAF50]✓[/color] اكتب 'help' للمساعدة\n[color=#2196F3]────────────────────────────[/color]\n",
            markup=True, halign="right", valign="top", size_hint_y=None
        )
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        self.output_scroll.add_widget(self.output_label)
        output_card.add_widget(self.output_scroll)
        layout.add_widget(output_card)

        input_card = MDBoxLayout(size_hint_y=None, height=dp(70), padding=dp(10), spacing=dp(5), md_bg_color="#1E1E1E")
        self.prompt_label = MDLabel(text="[admin@MikroTik] > ", markup=True, theme_text_color="Custom", text_color="#4CAF50", size_hint_x=0.35, halign="right")
        input_card.add_widget(self.prompt_label)
        self.cmd_input = MDTextField(hint_text="أدخل الأمر...", mode="rectangle", size_hint_x=0.55, multiline=False, on_text_validate=self._execute_command)
        input_card.add_widget(self.cmd_input)
        run_btn = MDIconButton(icon="send", theme_text_color="Custom", text_color="#4CAF50", on_release=self._execute_command, size_hint_x=0.1)
        input_card.add_widget(run_btn)
        layout.add_widget(input_card)
        self.add_widget(layout)

    def on_enter(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app.current_device:
            self.device = app.current_device
            self.prompt_label.text = f"[admin@{self.device['name']}] > "
            self.device_label.text = f"🟢 متصل بـ {self.device['name']} ({self.device['ip']})"
            self.device_bar.md_bg_color = "#1B5E20"
        else:
            self.device = None
            self.prompt_label.text = "[local] > "
            self.device_label.text = "🔴 غير متصل"
            self.device_bar.md_bg_color = "#B71C1C"

    def _execute_command(self, instance=None):
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        if cmd not in self.command_history:
            self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        self._append_output(f"\n[b][color=#4CAF50]➜[/color] {cmd}[/b]\n")
        self.cmd_input.text = ""
        if self.device:
            self._execute_remote(cmd)
        else:
            self._execute_local(cmd)

    def _execute_remote(self, cmd):
        def run():
            try:
                result = self.api.execute_command(self.device, cmd)
                Clock.schedule_once(lambda dt: self._append_output(result), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._append_output(f"[color=#F44336]✗ خطأ: {str(e)}[/color]"), 0)
        threading.Thread(target=run, daemon=True).start()

    def _execute_local(self, cmd):
        parts = cmd.split()
        base = parts[0] if parts else ""
        if base == "help":
            self._show_help()
        elif base == "devices":
            self._show_devices()
        elif base == "connect" and len(parts) > 1:
            self._connect_device(parts[1])
        elif base == "clear":
            self.output_label.text = ""
            self._append_output("[b]🤖 Smart MikroTik CLI v2.0[/b]\n")
        elif base == "history":
            self._show_history_local()
        elif base == "ai" and len(parts) > 1:
            self._ask_ai(" ".join(parts[1:]))
        else:
            self._append_output(f"[color=#F44336]✗ أمر غير معروف: {cmd}[/color]\n")

    def _show_help(self):
        help_text = """
[b][color=#2196F3]═══════════════════════════════════════[/color][/b]
[b]📚 دليل أوامر Smart MikroTik CLI[/b]
[b][color=#2196F3]═══════════════════════════════════════[/color][/b]
[b][color=#4CAF50]🖥️ أوامر النظام:[/color][/b]
  system resource print    - عرض موارد النظام
  system identity print    - عرض هوية الجهاز
  system reboot            - إعادة تشغيل
[b][color=#4CAF50]🌐 أوامر IP:[/color][/b]
  ip address print         - عرض عناوين IP
  ip route print           - عرض جدول التوجيه
  ip firewall filter print - عرض قواعد الفايروول
  ip hotspot user print    - عرض مستخدمي الهوتسبوت
[b][color=#4CAF50]🔧 أوامر الواجهات:[/color][/b]
  interface print          - عرض الواجهات
[b][color=#4CAF50]📋 أوامر عامة:[/color][/b]
  help                     - هذا الدليل
  devices                  - عرض الأجهزة
  connect <id>             - الاتصال بجهاز
  clear                    - مسح الشاشة
  history                  - عرض سجل الأوامر
"""
        self._append_output(help_text)

    def _show_devices(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        devices = app.db.get_all_devices()
        output = "\n[b][color=#2196F3]📡 الأجهزة:[/color][/b]\n"
        for d in devices:
            status = "🟢" if d.get('status') == 'online' else "🔴"
            output += f"  [{d['id']}] {status} {d['name']} - {d['ip']}\n"
        self._append_output(output)

    def _connect_device(self, device_id):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        device = app.db.get_device(device_id)
        if device:
            app.current_device = device
            self.device = device
            self.prompt_label.text = f"[admin@{device['name']}] > "
            self.device_label.text = f"🟢 متصل بـ {device['name']}"
            self.device_bar.md_bg_color = "#1B5E20"
            self._append_output(f"[color=#4CAF50]✓ تم الاتصال[/color]\n")

    def _show_history_local(self):
        output = "\n[b][color=#2196F3]📜 السجل:[/color][/b]\n"
        for i, cmd in enumerate(self.command_history[-20:], 1):
            output += f"  {i}. {cmd}\n"
        self._append_output(output)

    def _ask_ai(self, question):
        self._append_output("[color=#9C27B0]🤖 جاري التفكير...[/color]\n")
        def ask():
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            try:
                response = app.ai.ask(question)
                Clock.schedule_once(lambda dt: self._append_output(f"[color=#9C27B0]🤖 {response}[/color]\n"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._append_output(f"[color=#F44336]✗ خطأ: {str(e)}[/color]\n"), 0)
        threading.Thread(target=ask, daemon=True).start()

    def _quick_command(self, cmd):
        self.cmd_input.text = cmd
        self._execute_command()

    def _append_output(self, text):
        self.output_label.text += text
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _scroll_to_bottom(self):
        self.output_scroll.scroll_y = 0

    def _show_history(self):
        self._show_history_local()

    def _go_back(self):
        self.manager.current = "main"
