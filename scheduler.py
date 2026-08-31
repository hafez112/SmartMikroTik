#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""نظام الجدولة الذكي"""

import threading
import time
from datetime import datetime, timedelta
from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField

from database import DatabaseManager
from mikrotik_api import MikroTikAPI


class ScheduledTask:
    def __init__(self, task_id, name, script_content, device_id, schedule_type, interval_minutes, enabled=True):
        self.task_id = task_id
        self.name = name
        self.script_content = script_content
        self.device_id = device_id
        self.schedule_type = schedule_type
        self.interval_minutes = interval_minutes
        self.enabled = enabled
        self.last_run = None
        self.next_run = datetime.now()
        self.running = False

    def should_run(self):
        if not self.enabled or self.running:
            return False
        return datetime.now() >= self.next_run

    def execute(self):
        self.running = True
        self.last_run = datetime.now()
        try:
            db = DatabaseManager()
            device = db.get_device(self.device_id)
            if device:
                api = MikroTikAPI()
                result = api._execute_ssh_command(device, self.script_content)
                success = True
            else:
                success = False
            if self.schedule_type == 'interval':
                self.next_run = self.last_run + timedelta(minutes=self.interval_minutes)
            elif self.schedule_type == 'daily':
                self.next_run = self.last_run + timedelta(days=1)
            self.running = False
            return success, result if success else ""
        except Exception as e:
            self.running = False
            return False, str(e)


class SchedulerManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tasks = {}
            cls._instance.running = False
            cls._instance.thread = None
        return cls._instance

    def add_task(self, task_data):
        task = ScheduledTask(
            task_id=task_data.get('id'), name=task_data['name'],
            script_content=task_data['script_content'], device_id=task_data['device_id'],
            schedule_type=task_data.get('schedule_type', 'interval'),
            interval_minutes=task_data.get('interval_minutes', 60),
            enabled=task_data.get('enabled', True)
        )
        self.tasks[task.task_id] = task
        return task

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _scheduler_loop(self):
        while self.running:
            for task in list(self.tasks.values()):
                if task.should_run():
                    def run_task(t=task):
                        success, output = t.execute()
                        print(f"Task {t.name}: {'Success' if success else 'Failed'}")
                    threading.Thread(target=run_task, daemon=True).start()
            time.sleep(30)


class SchedulerScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduler = SchedulerManager()
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(
            title="⏰ جدولة المهام", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["play", lambda x: self._start_scheduler()], ["stop", lambda x: self._stop_scheduler()], ["plus", lambda x: self._show_add_task_dialog()]],
            elevation=4
        )
        layout.add_widget(toolbar)

        self.status_card = MDCard(size_hint=(1, None), height=dp(60), padding=dp(15), elevation=2)
        self.status_label = MDLabel(text="⏹️ متوقفة", halign="center", theme_text_color="Primary", font_style="H6")
        self.status_card.add_widget(self.status_label)
        layout.add_widget(self.status_card)

        scroll = MDScrollView()
        self.tasks_list = MDList()
        scroll.add_widget(self.tasks_list)
        layout.add_widget(scroll)
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self._load_tasks(), 0.5)

    def _load_tasks(self):
        self.tasks_list.clear_widgets()
        default_tasks = [
            {'id': '1', 'name': 'نسخ احتياطي يومي', 'schedule_type': 'daily', 'interval_minutes': 1440, 'enabled': True, 'last_run': 'لم ينفذ'},
            {'id': '2', 'name': 'تنظيف السجلات', 'schedule_type': 'weekly', 'interval_minutes': 10080, 'enabled': True, 'last_run': '2024-01-15'},
        ]
        for task in default_tasks:
            status = "🟢" if task['enabled'] else "🔴"
            item = TwoLineListItem(text=f"{status} {task['name']}", secondary_text=f"النوع: {task['schedule_type']} | آخر تشغيل: {task['last_run']}")
            self.tasks_list.add_widget(item)

    def _show_add_task_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(350))
        name_field = MDTextField(hint_text="اسم المهمة")
        device_field = MDTextField(hint_text="رقم الجهاز")
        script_field = MDTextField(hint_text="محتوى السكربت", multiline=True)
        schedule_type = MDTextField(hint_text="النوع (interval/daily)")
        interval_field = MDTextField(hint_text="الفاصل (دقائق)", text="60")
        content.add_widget(name_field)
        content.add_widget(device_field)
        content.add_widget(script_field)
        content.add_widget(schedule_type)
        content.add_widget(interval_field)
        dialog = MDDialog(
            title="➕ مهمة جديدة", type="custom", content_cls=content,
            buttons=[
                MDRaisedButton(text="إلغاء", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="إضافة", md_bg_color="#4CAF50", on_release=lambda x: self._add_task(dialog, name_field, device_field, script_field, schedule_type, interval_field)),
            ],
        )
        dialog.open()

    def _add_task(self, dialog, name, device, script, schedule_type, interval):
        task_data = {
            'name': name.text, 'device_id': device.text,
            'script_content': script.text, 'schedule_type': schedule_type.text or 'interval',
            'interval_minutes': int(interval.text or 60), 'enabled': True
        }
        self.scheduler.add_task(task_data)
        dialog.dismiss()
        self._load_tasks()
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("✅ تم إضافة المهمة")

    def _start_scheduler(self):
        self.scheduler.start()
        self.status_card.md_bg_color = "#E8F5E9"
        self.status_label.text = "🟢 نشطة"
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("✅ بدأت الجدولة")

    def _stop_scheduler(self):
        self.scheduler.stop()
        self.status_card.md_bg_color = "#FFEBEE"
        self.status_label.text = "⏹️ متوقفة"
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("⏹️ توقفت الجدولة")

    def _go_back(self):
        self.manager.current = "main"
