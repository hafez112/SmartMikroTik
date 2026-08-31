#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""نظام التقارير المتقدم"""

import json
import csv
import os
from datetime import datetime
from io import StringIO

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog

from database import DatabaseManager
from mikrotik_api import MikroTikAPI


class ReportGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        self.api = MikroTikAPI()

    def generate_device_report(self, device_id):
        device = self.db.get_device(device_id)
        if not device:
            return None
        try:
            api = self.api.connect_api(device)
            resource = api.get_resource('/system/resource').get()[0]
            interfaces = api.get_resource('/interface').get()
            try:
                users = api.get_resource('/ip/hotspot/user').get()
            except:
                users = []
            try:
                dhcp = api.get_resource('/ip/dhcp-server/lease').get()
            except:
                dhcp = []
            report = {
                'generated_at': datetime.now().isoformat(),
                'device': {
                    'name': device['name'], 'ip': device['ip'],
                    'model': resource.get('board-name', 'N/A'),
                    'version': resource.get('version', 'N/A'),
                    'uptime': resource.get('uptime', 'N/A'),
                    'cpu_load': resource.get('cpu-load', '0')
                },
                'interfaces': [{'name': i.get('name'), 'type': i.get('type'), 'running': i.get('running', 'false')} for i in interfaces],
                'hotspot_users': len(users), 'dhcp_leases': len(dhcp)
            }
            return report
        except Exception as e:
            return {'error': str(e)}

    def generate_text_report(self, data):
        if 'error' in data:
            return f"خطأ: {data['error']}"
        lines = ["=" * 50, "📊 تقرير Smart MikroTik", f"📅 {data.get('generated_at', 'N/A')}", "=" * 50]
        if 'device' in data:
            d = data['device']
            lines.extend([f"📡 الجهاز: {d['name']}", f"🌐 IP: {d['ip']}", f"🖥️ الطراز: {d['model']}", f"⚙️ الإصدار: {d['version']}", f"⏱️ العمل: {d['uptime']}", f"⚡ CPU: {d['cpu_load']}%"])
        lines.append("\n" + "=" * 50)
        return "\n".join(lines)


class ReportsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.generator = ReportGenerator()
        self.current_report = None
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(
            title="📊 التقارير", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["refresh", lambda x: self._generate_report()], ["download", lambda x: self._show_export_dialog()]],
            elevation=4
        )
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        content.add_widget(MDLabel(text="[b]📋 نوع التقرير[/b]", markup=True, font_style="H6"))
        self.device_field = MDTextField(hint_text="رقم الجهاز", mode="rectangle")
        content.add_widget(self.device_field)
        gen_btn = MDRaisedButton(text="📊 توليد", size_hint=(1, None), height=dp(50), md_bg_color="#2196F3", on_release=self._generate_report)
        content.add_widget(gen_btn)

        self.report_card = MDCard(padding=dp(15), elevation=2, size_hint=(1, None), height=dp(400))
        self.report_label = MDLabel(text="اضغط 'توليد'...", markup=True, halign="right", valign="top", size_hint_y=None)
        self.report_label.bind(texture_size=self.report_label.setter('size'))
        report_scroll = MDScrollView()
        report_scroll.add_widget(self.report_label)
        self.report_card.add_widget(report_scroll)
        content.add_widget(self.report_card)

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def _generate_report(self, instance=None):
        self.report_label.text = "⏳ جاري التوليد..."
        def generate():
            try:
                report = self.generator.generate_device_report(self.device_field.text)
                self.current_report = report
                if report:
                    text = self.generator.generate_text_report(report)
                    Clock.schedule_once(lambda dt: self._show_report(text), 0)
                else:
                    Clock.schedule_once(lambda dt: self._show_report("❌ فشل"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_report(f"❌ خطأ: {str(e)}"), 0)
        threading.Thread(target=generate, daemon=True).start()

    def _show_report(self, text):
        self.report_label.text = text

    def _show_export_dialog(self):
        if not self.current_report:
            from kivymd.app import MDApp
            MDApp.get_running_app().show_snackbar("❌ ولد التقرير أولاً", "error")
            return
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(150))
        filename_field = MDTextField(hint_text="اسم الملف", text=f"report_{datetime.now().strftime('%Y%m%d')}", mode="rectangle")
        content.add_widget(filename_field)
        dialog = MDDialog(title="💾 تصدير", type="custom", content_cls=content,
            buttons=[
                MDRaisedButton(text="إلغاء", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="📄 نص", on_release=lambda x: self._export('txt', filename_field.text, dialog)),
                MDRaisedButton(text="📊 JSON", md_bg_color="#4CAF50", on_release=lambda x: self._export('json', filename_field.text, dialog)),
            ],
        )
        dialog.open()

    def _export(self, format_type, filename, dialog):
        dialog.dismiss()
        filepath = f"{filename}.{format_type}"
        try:
            if format_type == 'txt':
                text = self.generator.generate_text_report(self.current_report)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
            elif format_type == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_report, f, ensure_ascii=False, indent=2)
            from kivymd.app import MDApp
            MDApp.get_running_app().show_snackbar(f"✅ تصدير: {filepath}")
        except Exception as e:
            from kivymd.app import MDApp
            MDApp.get_running_app().show_snackbar(f"❌ فشل: {str(e)}", "error")

    def _go_back(self):
        self.manager.current = "main"
