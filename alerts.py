#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""نظام التنبيهات والإشعارات"""

import threading
import time
from datetime import datetime
from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import MDList, ThreeLineListItem
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog

from database import DatabaseManager
from mikrotik_api import MikroTikAPI


class AlertRule:
    def __init__(self, rule_id, name, device_id, metric, operator, threshold, enabled=True):
        self.rule_id = rule_id
        self.name = name
        self.device_id = device_id
        self.metric = metric
        self.operator = operator
        self.threshold = threshold
        self.enabled = enabled
        self.last_triggered = None
        self.trigger_count = 0

    def check_condition(self, value):
        try:
            val = float(value)
            thresh = float(self.threshold)
            if self.operator == '>':
                return val > thresh
            elif self.operator == '<':
                return val < thresh
            elif self.operator == '>=':
                return val >= thresh
            elif self.operator == '<=':
                return val <= thresh
            return False
        except:
            return False


class AlertsManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.rules = []
        self.monitoring = False
        self.alert_history = []
        self._load_rules()

    def _load_rules(self):
        self.rules = [
            AlertRule('1', 'CPU مرتفع', None, 'cpu', '>', '80'),
            AlertRule('2', 'ذاكرة منخفضة', None, 'memory', '<', '10'),
            AlertRule('3', 'حرارة مرتفعة', None, 'temperature', '>', '70'),
        ]

    def add_rule(self, rule_data):
        rule = AlertRule(
            rule_id=str(len(self.rules) + 1), name=rule_data['name'],
            device_id=rule_data.get('device_id'), metric=rule_data['metric'],
            operator=rule_data['operator'], threshold=rule_data['threshold']
        )
        self.rules.append(rule)
        return rule

    def check_device(self, device):
        alerts = []
        try:
            api = MikroTikAPI()
            result = api.test_connection(device)
            if result['status'] != 'online':
                alerts.append({'severity': 'critical', 'message': f"❌ {device['name']} غير متصل", 'time': datetime.now().isoformat()})
                return alerts
            cpu_load = float(result.get('cpu_load', 0))
            for rule in self.rules:
                if rule.metric == 'cpu' and rule.check_condition(cpu_load):
                    alerts.append({'severity': 'warning', 'message': f"⚠️ CPU مرتفع: {cpu_load}%", 'time': datetime.now().isoformat()})
        except Exception as e:
            alerts.append({'severity': 'error', 'message': str(e), 'time': datetime.now().isoformat()})
        return alerts

    def start_monitoring(self, interval=60):
        self.monitoring = True
        def monitor_loop():
            while self.monitoring:
                try:
                    devices = self.db.get_all_devices()
                    for device in devices:
                        alerts = self.check_device(device)
                        for alert in alerts:
                            self.alert_history.append(alert)
                            Clock.schedule_once(lambda dt, a=alert: self._send_notification(a), 0)
                except Exception as e:
                    print(f"Monitor error: {e}")
                time.sleep(interval)
        threading.Thread(target=monitor_loop, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring = False

    def _send_notification(self, alert):
        from kivymd.app import MDApp
        try:
            app = MDApp.get_running_app()
            app.show_snackbar(alert['message'], 'warning')
        except:
            pass


class AlertsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alerts_manager = AlertsManager()
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(
            title="🔔 التنبيهات", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["play", lambda x: self._start_monitoring()], ["stop", lambda x: self._stop_monitoring()], ["plus", lambda x: self._show_add_rule_dialog()]],
            elevation=4
        )
        layout.add_widget(toolbar)

        summary = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        self.critical_count = MDLabel(text="🔴 0", halign="center", font_style="H5")
        self.warning_count = MDLabel(text="🟡 0", halign="center", font_style="H5")
        self.info_count = MDLabel(text="🔵 0", halign="center", font_style="H5")
        summary.add_widget(self.critical_count)
        summary.add_widget(self.warning_count)
        summary.add_widget(self.info_count)
        layout.add_widget(summary)

        scroll = MDScrollView()
        self.alerts_list = MDList()
        scroll.add_widget(self.alerts_list)
        layout.add_widget(scroll)
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self._load_alerts(), 0.5)

    def _load_alerts(self):
        self.alerts_list.clear_widgets()
        demo_alerts = [
            {'severity': 'critical', 'message': "❌ جهاز المكتب غير متصل", 'time': "2024-01-20 15:30"},
            {'severity': 'warning', 'message': "⚠️ CPU مرتفع: 85%", 'time': "2024-01-20 15:25"},
            {'severity': 'info', 'message': "✅ إعادة تشغيل ناجحة", 'time': "2024-01-20 15:20"},
        ]
        critical = warning = info = 0
        for alert in demo_alerts:
            if alert['severity'] == 'critical':
                critical += 1
                color = "#F44336"
            elif alert['severity'] == 'warning':
                warning += 1
                color = "#FF9800"
            else:
                info += 1
                color = "#2196F3"
            item = ThreeLineListItem(
                text=f"[color={color}]{alert['message']}[/color]",
                secondary_text=f"الوقت: {alert['time']}"
            )
            self.alerts_list.add_widget(item)
        self.critical_count.text = f"🔴 {critical}"
        self.warning_count.text = f"🟡 {warning}"
        self.info_count.text = f"🔵 {info}"

    def _show_add_rule_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(300))
        name_field = MDTextField(hint_text="اسم القاعدة")
        metric_field = MDTextField(hint_text="المقياس (cpu/memory)")
        operator_field = MDTextField(hint_text="العامل (>, <)")
        threshold_field = MDTextField(hint_text="العتبة")
        content.add_widget(name_field)
        content.add_widget(metric_field)
        content.add_widget(operator_field)
        content.add_widget(threshold_field)
        dialog = MDDialog(
            title="➕ قاعدة تنبيه", type="custom", content_cls=content,
            buttons=[
                MDRaisedButton(text="إلغاء", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="إضافة", md_bg_color="#4CAF50", on_release=lambda x: self._add_rule(dialog, name_field, metric_field, operator_field, threshold_field)),
            ],
        )
        dialog.open()

    def _add_rule(self, dialog, name, metric, operator, threshold):
        rule_data = {
            'name': name.text, 'metric': metric.text,
            'operator': operator.text, 'threshold': threshold.text
        }
        self.alerts_manager.add_rule(rule_data)
        dialog.dismiss()
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("✅ تم إضافة القاعدة")

    def _start_monitoring(self):
        self.alerts_manager.start_monitoring()
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("🟢 بدأت المراقبة")

    def _stop_monitoring(self):
        self.alerts_manager.stop_monitoring()
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("⏹️ توقفت المراقبة")

    def _go_back(self):
        self.manager.current = "main"
