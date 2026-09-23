#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""أدوات الشبكة المتقدمة"""

import socket
import subprocess
import threading

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.progressbar import MDProgressBar


class Tab(MDFloatLayout, MDTabsBase):
    pass


class NetworkToolsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        layout.add_widget(MDTopAppBar(title="🔧 أدوات الشبكة", left_action_items=[["arrow-right", lambda x: self._go_back()]], elevation=4))
        tabs = MDTabs()
        ping_tab = Tab(title="Ping")
        self._setup_ping_tab(ping_tab)
        tabs.add_widget(ping_tab)
        port_tab = Tab(title="Port Scan")
        self._setup_port_scan_tab(port_tab)
        tabs.add_widget(port_tab)
        dns_tab = Tab(title="DNS")
        self._setup_dns_tab(dns_tab)
        tabs.add_widget(dns_tab)
        layout.add_widget(tabs)
        self.add_widget(layout)

    def _setup_ping_tab(self, tab):
        layout = MDBoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        input_box = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        self.ping_host = MDTextField(hint_text="IP أو نطاق", mode="rectangle", size_hint_x=0.7)
        self.ping_count = MDTextField(hint_text="العدد", text="4", mode="rectangle", size_hint_x=0.2)
        input_box.add_widget(self.ping_host)
        input_box.add_widget(self.ping_count)
        layout.add_widget(input_box)
        layout.add_widget(MDRaisedButton(text="▶️ Ping", size_hint=(1, None), height=dp(45), md_bg_color="#4CAF50", on_release=self._do_ping))
        self.ping_result = MDLabel(text="", markup=True, halign="right", valign="top", size_hint_y=None)
        self.ping_result.bind(texture_size=self.ping_result.setter("size"))
        scroll = MDScrollView()
        scroll.add_widget(self.ping_result)
        layout.add_widget(scroll)
        tab.add_widget(layout)

    def _do_ping(self, instance):
        host = self.ping_host.text.strip()
        count = self.ping_count.text.strip() or "4"
        if not host:
            return
        self.ping_result.text = "⏳ جاري الاختبار...\n"
        def ping():
            try:
                result = subprocess.run(["ping", "-c", count, host], capture_output=True, text=True, timeout=30)
                output = result.stdout if result.returncode == 0 else result.stderr
                Clock.schedule_once(lambda dt: self._show_ping_result(output), 0)
            except Exception as exc:
                Clock.schedule_once(lambda dt: self._show_ping_result(f"❌ خطأ: {exc}"), 0)
        threading.Thread(target=ping, daemon=True).start()

    def _show_ping_result(self, text):
        self.ping_result.text = f"[b]📊 نتيجة Ping:[/b]\n\n{text}"

    def _setup_port_scan_tab(self, tab):
        layout = MDBoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        input_box = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        self.scan_host = MDTextField(hint_text="IP", mode="rectangle", size_hint_x=0.5)
        self.scan_start = MDTextField(hint_text="من", text="1", mode="rectangle", size_hint_x=0.2)
        self.scan_end = MDTextField(hint_text="إلى", text="100", mode="rectangle", size_hint_x=0.2)
        input_box.add_widget(self.scan_host)
        input_box.add_widget(self.scan_start)
        input_box.add_widget(self.scan_end)
        layout.add_widget(input_box)
        self.scan_progress = MDProgressBar(value=0, size_hint_y=None, height=dp(5))
        layout.add_widget(self.scan_progress)
        layout.add_widget(MDRaisedButton(text="🔍 فحص", size_hint=(1, None), height=dp(45), md_bg_color="#2196F3", on_release=self._do_port_scan))
        self.scan_result = MDLabel(text="", markup=True, halign="right", valign="top", size_hint_y=None)
        self.scan_result.bind(texture_size=self.scan_result.setter("size"))
        scroll = MDScrollView()
        scroll.add_widget(self.scan_result)
        layout.add_widget(scroll)
        tab.add_widget(layout)

    def _do_port_scan(self, instance):
        host = self.scan_host.text.strip()
        try:
            start_port = max(1, int(self.scan_start.text or 1))
            end_port = min(65535, int(self.scan_end.text or 100))
        except ValueError:
            self.scan_result.text = "❌ نطاق المنافذ غير صحيح"
            return
        if not host or start_port > end_port:
            return
        self.scan_result.text = "⏳ جاري الفحص...\n"
        self.scan_progress.value = 0
        def scan():
            open_ports = []
            total = end_port - start_port + 1
            for index, port in enumerate(range(start_port, end_port + 1)):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(0.5)
                        if sock.connect_ex((host, port)) == 0:
                            open_ports.append(port)
                except OSError:
                    pass
                Clock.schedule_once(lambda dt, p=((index + 1) / total) * 100: self._update_scan_progress(p), 0)
            Clock.schedule_once(lambda dt, ports=open_ports: self._show_scan_result(ports), 0)
        threading.Thread(target=scan, daemon=True).start()

    def _update_scan_progress(self, value):
        self.scan_progress.value = value

    def _show_scan_result(self, open_ports):
        if open_ports:
            ports_text = ", ".join(map(str, open_ports))
            self.scan_result.text = f"[b]✅ مفتوحة:[/b]\n{ports_text}"
        else:
            self.scan_result.text = "❌ لا توجد منافذ مفتوحة"

    def _setup_dns_tab(self, tab):
        layout = MDBoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        input_box = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        self.dns_host = MDTextField(hint_text="نطاق", mode="rectangle", size_hint_x=0.7)
        self.dns_type = MDTextField(hint_text="نوع", text="A", mode="rectangle", size_hint_x=0.3)
        input_box.add_widget(self.dns_host)
        input_box.add_widget(self.dns_type)
        layout.add_widget(input_box)
        layout.add_widget(MDRaisedButton(text="🔍 DNS", size_hint=(1, None), height=dp(45), md_bg_color="#9C27B0", on_release=self._do_dns_lookup))
        self.dns_result = MDLabel(text="", markup=True, halign="right", valign="top", size_hint_y=None)
        self.dns_result.bind(texture_size=self.dns_result.setter("size"))
        scroll = MDScrollView()
        scroll.add_widget(self.dns_result)
        layout.add_widget(scroll)
        tab.add_widget(layout)

    def _do_dns_lookup(self, instance):
        host = self.dns_host.text.strip()
        if not host:
            return
        self.dns_result.text = "⏳ جاري البحث...\n"
        def lookup():
            try:
                result = socket.gethostbyname_ex(host)
                output = f"Hostname: {result[0]}\nIPs: {result[2]}"
                Clock.schedule_once(lambda dt: self._show_dns_result(output), 0)
            except Exception as exc:
                Clock.schedule_once(lambda dt: self._show_dns_result(f"❌ خطأ: {exc}"), 0)
        threading.Thread(target=lookup, daemon=True).start()

    def _show_dns_result(self, text):
        self.dns_result.text = f"[b]📋 DNS:[/b]\n\n{text}"

    def _go_back(self):
        self.manager.current = "main"
