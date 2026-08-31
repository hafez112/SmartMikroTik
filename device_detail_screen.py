#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""شاشة تفاصيل الجهاز"""

import threading
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.progressbar import MDProgressBar

from mikrotik_api import MikroTikAPI


class Tab(MDFloatLayout, MDTabsBase):
    pass


class DeviceDetailScreen(MDScreen):
    device_id = StringProperty("")
    device_name = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = MikroTikAPI()
        self.device = None
        self.monitoring = False
        self._setup_ui()

    def _setup_ui(self):
        self.layout = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["refresh", lambda x: self.refresh_all()], ["dots-vertical", lambda x: None]],
            elevation=4
        )
        self.layout.add_widget(self.toolbar)
        self.tabs = MDTabs(tab_indicator_height=dp(3), tab_indicator_color="#2196F3", text_color_active="#2196F3")

        self.overview_tab = Tab(title="[b]📊 نظرة عامة[/b]")
        self._setup_overview_tab()
        self.tabs.add_widget(self.overview_tab)

        self.interfaces_tab = Tab(title="[b]🌐 الواجهات[/b]")
        self._setup_interfaces_tab()
        self.tabs.add_widget(self.interfaces_tab)

        self.users_tab = Tab(title="[b]👥 المستخدمين[/b]")
        self._setup_users_tab()
        self.tabs.add_widget(self.users_tab)

        self.dhcp_tab = Tab(title="[b]📡 DHCP[/b]")
        self._setup_dhcp_tab()
        self.tabs.add_widget(self.dhcp_tab)

        self.layout.add_widget(self.tabs)
        self.add_widget(self.layout)

    def _setup_overview_tab(self):
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        self.status_card = MDCard(size_hint=(1, None), height=dp(80), padding=dp(15), elevation=2, radius=[15, 15, 15, 15])
        status_layout = MDBoxLayout()
        self.status_icon = MDLabel(text="🔴", font_style="H4", size_hint_x=0.2)
        self.status_text = MDLabel(text="غير متصل", font_style="H6", halign="right")
        status_layout.add_widget(self.status_icon)
        status_layout.add_widget(self.status_text)
        self.status_card.add_widget(status_layout)
        content.add_widget(self.status_card)

        stats_grid = MDGridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(320))
        self.cpu_label = MDLabel(text="⚡ CPU\n0%", halign="center", font_style="H4")
        self.ram_label = MDLabel(text="💾 RAM\n0 MB", halign="center", font_style="H4")
        self.uptime_label = MDLabel(text="⏱️ العمل\n0", halign="center", font_style="H4")
        self.temp_label = MDLabel(text="🌡️ الحرارة\n0°C", halign="center", font_style="H4")
        stats_grid.add_widget(self.cpu_label)
        stats_grid.add_widget(self.ram_label)
        stats_grid.add_widget(self.uptime_label)
        stats_grid.add_widget(self.temp_label)
        content.add_widget(stats_grid)

        buttons_card = MDCard(size_hint=(1, None), height=dp(120), padding=dp(10), elevation=2, radius=[15, 15, 15, 15])
        buttons_grid = MDGridLayout(cols=3, spacing=dp(10))
        actions = [
            ("🔄", "إعادة تشغيل", "#E53935", self._reboot_device),
            ("💾", "نسخ احتياطي", "#1E88E5", self._backup_device),
            ("📤", "تصدير", "#43A047", self._export_config),
        ]
        for icon, text, color, callback in actions:
            btn = MDRaisedButton(text=f"{icon}\n{text}", size_hint=(1, 1), md_bg_color=color, on_release=callback)
            buttons_grid.add_widget(btn)
        buttons_card.add_widget(buttons_grid)
        content.add_widget(buttons_card)
        scroll.add_widget(content)
        self.overview_tab.add_widget(scroll)

    def _setup_interfaces_tab(self):
        layout = MDBoxLayout(orientation="vertical")
        search_box = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        self.interface_search = MDTextField(hint_text="🔍 بحث...", size_hint_x=0.8)
        search_box.add_widget(self.interface_search)
        search_box.add_widget(MDIconButton(icon="refresh", on_release=lambda x: self._load_interfaces()))
        layout.add_widget(search_box)
        scroll = MDScrollView()
        self.interfaces_list = MDList()
        scroll.add_widget(self.interfaces_list)
        layout.add_widget(scroll)
        self.interfaces_tab.add_widget(layout)

    def _setup_users_tab(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5), spacing=dp(5))
        toolbar.add_widget(MDRaisedButton(text="➕ إضافة", md_bg_color="#43A047", on_release=self._show_add_user_dialog))
        toolbar.add_widget(MDRaisedButton(text="🔄 تحديث", md_bg_color="#1E88E5", on_release=lambda x: self._load_users()))
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        self.users_list = MDList()
        scroll.add_widget(self.users_list)
        layout.add_widget(scroll)
        self.users_tab.add_widget(layout)

    def _setup_dhcp_tab(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(5))
        toolbar.add_widget(MDRaisedButton(text="🔄 تحديث", on_release=lambda x: self._load_dhcp()))
        layout.add_widget(toolbar)
        scroll = MDScrollView()
        self.dhcp_list = MDList()
        scroll.add_widget(self.dhcp_list)
        layout.add_widget(scroll)
        self.dhcp_tab.add_widget(layout)

    def on_enter(self):
        if self.device_id:
            self._load_device()

    def _load_device(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        self.device = app.db.get_device(self.device_id)
        if self.device:
            self.toolbar.title = f"📡 {self.device['name']}"
            self.device_name = self.device['name']
            self._update_status()

    def _update_status(self):
        def check():
            try:
                result = self.api.test_connection(self.device)
                Clock.schedule_once(lambda dt: self._update_status_ui(result), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._update_status_ui({'status': 'offline', 'error': str(e)}), 0)
        threading.Thread(target=check, daemon=True).start()

    def _update_status_ui(self, result):
        if result['status'] == 'online':
            self.status_icon.text = "🟢"
            self.status_text.text = f"متصل | {result.get('uptime', 'N/A')}"
            self.status_card.md_bg_color = "#E8F5E9"
            self.cpu_label.text = f"⚡ CPU\n{result.get('cpu_load', '0')}%"
            self.ram_label.text = f"💾 RAM\n{result.get('free_memory', '0')}"
            self.uptime_label.text = f"⏱️ العمل\n{result.get('uptime', '0')}"
        else:
            self.status_icon.text = "🔴"
            self.status_text.text = f"غير متصل"
            self.status_card.md_bg_color = "#FFEBEE"

    def _load_interfaces(self):
        def load():
            try:
                interfaces = self.api.get_interfaces(self.device)
                Clock.schedule_once(lambda dt: self._update_interfaces_list(interfaces), 0)
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=load, daemon=True).start()

    def _update_interfaces_list(self, interfaces):
        self.interfaces_list.clear_widgets()
        for iface in interfaces:
            name = iface.get('name', 'N/A')
            status = "🟢" if iface.get('running') == 'true' else "🔴"
            item = TwoLineListItem(text=f"{status} {name}", secondary_text=f"Type: {iface.get('type', 'N/A')}")
            self.interfaces_list.add_widget(item)

    def _load_users(self):
        def load():
            try:
                users = self.api.get_hotspot_users(self.device)
                Clock.schedule_once(lambda dt: self._update_users_list(users), 0)
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=load, daemon=True).start()

    def _update_users_list(self, users):
        self.users_list.clear_widgets()
        for user in users:
            name = user.get('name', 'N/A')
            profile = user.get('profile', 'default')
            item = TwoLineListItem(text=f"👤 {name}", secondary_text=f"Profile: {profile}")
            self.users_list.add_widget(item)

    def _show_add_user_dialog(self, instance):
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(250))
        name_field = MDTextField(hint_text="اسم المستخدم")
        pass_field = MDTextField(hint_text="كلمة المرور", password=True)
        profile_field = MDTextField(hint_text="الملف الشخصي", text="default")
        content.add_widget(name_field)
        content.add_widget(pass_field)
        content.add_widget(profile_field)
        dialog = MDDialog(
            title="➕ إضافة مستخدم", type="custom", content_cls=content,
            buttons=[
                MDRaisedButton(text="إلغاء", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="إضافة", md_bg_color="#43A047", on_release=lambda x: self._add_user(dialog, name_field, pass_field, profile_field)),
            ],
        )
        dialog.open()

    def _add_user(self, dialog, name, password, profile):
        def do_add():
            try:
                self.api.add_hotspot_user(self.device, name.text, password.text, profile.text)
                Clock.schedule_once(lambda dt: self._load_users(), 0)
                Clock.schedule_once(lambda dt: dialog.dismiss(), 0)
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=do_add, daemon=True).start()

    def _load_dhcp(self):
        def load():
            try:
                leases = self.api.get_dhcp_leases(self.device)
                Clock.schedule_once(lambda dt: self._update_dhcp_list(leases), 0)
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=load, daemon=True).start()

    def _update_dhcp_list(self, leases):
        self.dhcp_list.clear_widgets()
        for lease in leases:
            address = lease.get('address', 'N/A')
            mac = lease.get('mac-address', 'N/A')
            item = TwoLineListItem(text=f"📡 {address}", secondary_text=f"MAC: {mac}")
            self.dhcp_list.add_widget(item)

    def _reboot_device(self, instance):
        dialog = MDDialog(
            title="⚠️ تأكيد", text=f"إعادة تشغيل {self.device_name}?",
            buttons=[
                MDRaisedButton(text="إلغاء", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="إعادة تشغيل", md_bg_color="#E53935", on_release=lambda x: self._do_reboot(dialog)),
            ],
        )
        dialog.open()

    def _do_reboot(self, dialog):
        def reboot():
            try:
                self.api.reboot(self.device)
                Clock.schedule_once(lambda dt: dialog.dismiss(), 0)
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=reboot, daemon=True).start()

    def _backup_device(self, instance):
        def backup():
            try:
                name = self.api.backup_config(self.device)
                Clock.schedule_once(lambda dt: self._show_snackbar(f"✅ نسخة: {name}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_snackbar(f"❌ فشل: {str(e)}"), 0)
        threading.Thread(target=backup, daemon=True).start()

    def _export_config(self, instance):
        def export():
            try:
                config = self.api.export_config(self.device)
                filename = f"export_{self.device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.rsc"
                with open(filename, 'w') as f:
                    f.write(config)
                Clock.schedule_once(lambda dt: self._show_snackbar(f"✅ تصدير: {filename}"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_snackbar(f"❌ فشل: {str(e)}"), 0)
        threading.Thread(target=export, daemon=True).start()

    def refresh_all(self):
        self._update_status()
        self._load_interfaces()
        self._load_users()
        self._load_dhcp()

    def _show_snackbar(self, text):
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar(text)

    def _go_back(self):
        self.manager.current = "main"
        self.monitoring = False
