#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""شاشة المراقبة الحية"""

import threading
import time
from collections import deque
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.widget import Widget

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.progressbar import MDProgressBar

from mikrotik_api import MikroTikAPI


class Tab(MDFloatLayout, MDTabsBase):
    pass


class TrafficGraph(Widget):
    def __init__(self, color, max_points=100, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.max_points = max_points
        self.data = deque([0] * max_points, maxlen=max_points)
        self.padding = dp(10)
        with self.canvas:
            Color(0.1, 0.1, 0.1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            Color(*color)
            self.line = Line(points=[], width=1.5)
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        if len(self.data) > 1:
            width = self.width - 2 * self.padding
            height = self.height - 2 * self.padding
            max_val = max(self.data) or 1
            points = []
            for i, val in enumerate(self.data):
                x = self.x + self.padding + (i / (self.max_points - 1)) * width
                y = self.y + self.padding + (val / max_val) * height
                points.extend([x, y])
            self.line.points = points

    def add_value(self, value):
        self.data.append(value)
        self._update_canvas()


class MonitorScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = MikroTikAPI()
        self.device = None
        self.monitoring = False
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="📊 المراقبة الحية", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["play", lambda x: self._start_monitoring()], ["stop", lambda x: self._stop_monitoring()]],
            elevation=4
        )
        layout.add_widget(self.toolbar)

        self.status_bar = MDBoxLayout(size_hint_y=None, height=dp(40), padding=dp(10), md_bg_color="#1A237E")
        self.status_label = MDLabel(text="⏹️ متوقفة", theme_text_color="Custom", text_color="white", halign="center")
        self.status_bar.add_widget(self.status_label)
        layout.add_widget(self.status_bar)

        tabs = MDTabs()
        system_tab = Tab(title="النظام")
        self._setup_system_tab(system_tab)
        tabs.add_widget(system_tab)

        traffic_tab = Tab(title="الشبكة")
        self._setup_traffic_tab(traffic_tab)
        tabs.add_widget(traffic_tab)

        users_tab = Tab(title="المستخدمون")
        self._setup_active_users_tab(users_tab)
        tabs.add_widget(users_tab)
        layout.add_widget(tabs)
        self.add_widget(layout)

    def _setup_system_tab(self, tab):
        layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        stats_grid = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(200))
        self.cpu_value = MDLabel(text="0%", halign="center", font_style="H3")
        self.ram_value = MDLabel(text="0 MB", halign="center", font_style="H3")
        cpu_card = MDCard(size_hint=(1, 1), padding=dp(10), elevation=2)
        cpu_layout = MDBoxLayout(orientation="vertical")
        cpu_layout.add_widget(MDLabel(text="⚡ CPU", halign="center", font_style="H6"))
        cpu_layout.add_widget(self.cpu_value)
        cpu_card.add_widget(cpu_layout)
        stats_grid.add_widget(cpu_card)
        ram_card = MDCard(size_hint=(1, 1), padding=dp(10), elevation=2)
        ram_layout = MDBoxLayout(orientation="vertical")
        ram_layout.add_widget(MDLabel(text="💾 RAM", halign="center", font_style="H6"))
        ram_layout.add_widget(self.ram_value)
        ram_card.add_widget(ram_layout)
        stats_grid.add_widget(ram_card)
        layout.add_widget(stats_grid)
        tab.add_widget(layout)

    def _setup_traffic_tab(self, tab):
        layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        graphs_card = MDCard(size_hint=(1, None), height=dp(300), padding=dp(10), elevation=2)
        graphs_layout = MDBoxLayout(orientation="vertical")
        graphs_layout.add_widget(MDLabel(text="[b]📈 حركة المرور[/b]", markup=True, size_hint_y=None, height=dp(30)))
        self.rx_graph = TrafficGraph((0.2, 0.8, 0.2, 1), size_hint_y=0.45)
        graphs_layout.add_widget(self.rx_graph)
        self.tx_graph = TrafficGraph((0.2, 0.4, 0.9, 1), size_hint_y=0.45)
        graphs_layout.add_widget(self.tx_graph)
        graphs_card.add_widget(graphs_layout)
        layout.add_widget(graphs_card)
        tab.add_widget(layout)

    def _setup_active_users_tab(self, tab):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        toolbar.add_widget(MDRaisedButton(text="🔄 تحديث", on_release=lambda x: self._load_active_users()))
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        self.active_users_list = MDBoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None)
        self.active_users_list.bind(minimum_height=self.active_users_list.setter('height'))
        scroll.add_widget(self.active_users_list)
        layout.add_widget(scroll)
        tab.add_widget(layout)

    def on_enter(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        self.device = app.current_device
        if self.device:
            self.toolbar.title = f"📊 مراقبة: {self.device['name']}"

    def _start_monitoring(self):
        if not self.device:
            from kivymd.app import MDApp
            MDApp.get_running_app().show_snackbar("❌ اختر جهازاً أولاً", "error")
            return
        self.monitoring = True
        self.status_bar.md_bg_color = "#1B5E20"
        self.status_label.text = "🟢 نشطة"
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _stop_monitoring(self):
        self.monitoring = False
        self.status_bar.md_bg_color = "#B71C1C"
        self.status_label.text = "⏹️ متوقفة"

    def _monitor_loop(self):
        while self.monitoring:
            try:
                api = self.api.connect_api(self.device)
                resource = api.get_resource('/system/resource')
                info = resource.get()[0]
                Clock.schedule_once(lambda dt, i=info: self._update_system_stats(i), 0)
                interfaces = api.get_resource('/interface')
                ifaces = interfaces.get()
                total_rx = sum(int(iface.get('rx-byte', 0)) for iface in ifaces)
                total_tx = sum(int(iface.get('tx-byte', 0)) for iface in ifaces)
                Clock.schedule_once(lambda dt, rx=total_rx, tx=total_tx: self._update_traffic(rx, tx), 0)
                time.sleep(2)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

    def _update_system_stats(self, info):
        cpu_load = int(info.get('cpu-load', 0))
        self.cpu_value.text = f"{cpu_load}%"
        total_mem = int(info.get('total-memory', 0))
        free_mem = int(info.get('free-memory', 0))
        used_mem = total_mem - free_mem
        self.ram_value.text = f"{used_mem // 1024 // 1024} MB"

    def _update_traffic(self, rx, tx):
        rx_mbps = rx / 1024 / 1024
        tx_mbps = tx / 1024 / 1024
        self.rx_graph.add_value(rx_mbps)
        self.tx_graph.add_value(tx_mbps)

    def _load_active_users(self):
        def load():
            try:
                api = self.api.connect_api(self.device)
                active = api.get_resource('/ip/hotspot/active')
                users = active.get()
                Clock.schedule_once(lambda dt, u=users: self._update_active_users(u), 0)
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=load, daemon=True).start()

    def _update_active_users(self, users):
        self.active_users_list.clear_widgets()
        for user in users:
            name = user.get('user', 'N/A')
            ip = user.get('address', 'N/A')
            card = MDCard(size_hint=(1, None), height=dp(60), padding=dp(10), elevation=1)
            layout = MDBoxLayout(orientation="vertical")
            layout.add_widget(MDLabel(text=f"👤 {name}", font_style="H6"))
            layout.add_widget(MDLabel(text=f"IP: {ip}", theme_text_color="Secondary", font_style="Caption"))
            card.add_widget(layout)
            self.active_users_list.add_widget(card)

    def _go_back(self):
        self._stop_monitoring()
        self.manager.current = "main"
