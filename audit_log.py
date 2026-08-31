#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""سجل التدقيق الأمني"""

import json
from datetime import datetime, timedelta
from enum import Enum

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


class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"


class AuditLogger:
    def __init__(self):
        self.db = DatabaseManager()
        self._init_table()

    def _init_table(self):
        try:
            conn = self.db._get_connection()
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id INTEGER,
                    device_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    status TEXT
                )
            ''')
            conn.commit()
        except Exception as e:
            print(f"Audit init error: {e}")

    def log(self, level, category, action, user_id=None, device_id=None, details=None, ip_address=None, status=None):
        try:
            conn = self.db._get_connection()
            conn.execute('''
                INSERT INTO audit_logs (level, category, action, user_id, device_id, details, ip_address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                level.value if isinstance(level, AuditLevel) else level,
                category, action, user_id, device_id,
                json.dumps(details) if details else None,
                ip_address, status
            ))
            conn.commit()
        except Exception as e:
            print(f"Audit log error: {e}")

    def log_login(self, username, success=True, ip=None):
        self.log(
            AuditLevel.SUCCESS if success else AuditLevel.WARNING,
            "authentication", "login",
            details={'username': username, 'success': success},
            ip_address=ip, status="success" if success else "failed"
        )

    def log_device_access(self, device_id, device_name, action, user_id=None):
        self.log(
            AuditLevel.INFO, "device_access", action,
            user_id=user_id, device_id=device_id,
            details={'device_name': device_name}
        )

    def log_command(self, device_id, command, user_id=None):
        self.log(
            AuditLevel.INFO, "command", "execute",
            user_id=user_id, device_id=device_id,
            details={'command': command[:200]}
        )

    def get_logs(self, level=None, category=None, start_date=None, end_date=None, limit=100):
        try:
            conn = self.db._get_connection()
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            if level:
                query += " AND level = ?"
                params.append(level)
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    def clear_old_logs(self, days=30):
        try:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            conn = self.db._get_connection()
            conn.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff,))
            conn.commit()
            return True
        except:
            return False

    def get_stats(self):
        try:
            conn = self.db._get_connection()
            stats = {}
            cursor = conn.execute("SELECT COUNT(*) FROM audit_logs")
            stats['total'] = cursor.fetchone()[0]
            cursor = conn.execute("SELECT level, COUNT(*) FROM audit_logs GROUP BY level")
            stats['by_level'] = {row[0]: row[1] for row in cursor.fetchall()}
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE timestamp > ?", (yesterday,))
            stats['last_24h'] = cursor.fetchone()[0]
            return stats
        except:
            return {}


class AuditScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audit = AuditLogger()
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(
            title="🔒 سجل التدقيق", left_action_items=[["arrow-right", lambda x: self._go_back()]],
            right_action_items=[["refresh", lambda x: self._load_logs()], ["delete-sweep", lambda x: self._clear_old()]],
            elevation=4
        )
        layout.add_widget(toolbar)

        summary = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(10))
        self.total_label = MDLabel(text="📊 0", halign="center")
        self.critical_label = MDLabel(text="🔴 0", halign="center")
        self.warning_label = MDLabel(text="🟡 0", halign="center")
        self.today_label = MDLabel(text="📅 0", halign="center")
        summary.add_widget(self.total_label)
        summary.add_widget(self.critical_label)
        summary.add_widget(self.warning_label)
        summary.add_widget(self.today_label)
        layout.add_widget(summary)

        scroll = MDScrollView()
        self.logs_list = MDList()
        scroll.add_widget(self.logs_list)
        layout.add_widget(scroll)
        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self._load_logs(), 0.5)

    def _load_logs(self):
        self.logs_list.clear_widgets()
        logs = self.audit.get_logs(limit=50)
        stats = self.audit.get_stats()
        self.total_label.text = f"📊 {stats.get('total', 0)}"
        self.critical_label.text = f"🔴 {stats.get('by_level', {}).get('critical', 0)}"
        self.warning_label.text = f"🟡 {stats.get('by_level', {}).get('warning', 0)}"
        self.today_label.text = f"📅 {stats.get('last_24h', 0)}"
        colors = {'critical': '#F44336', 'error': '#F44336', 'warning': '#FF9800', 'info': '#2196F3', 'success': '#4CAF50'}
        for log in logs:
            color = colors.get(log.get('level', 'info'), '#2196F3')
            item = ThreeLineListItem(
                text=f"[color={color}]{log.get('level', 'info').upper()}[/color] | {log.get('action', 'N/A')}",
                secondary_text=f"الفئة: {log.get('category', 'N/A')} | {log.get('timestamp', 'N/A')}",
                tertiary_text=f"{str(log.get('details', ''))[:100]}"
            )
            self.logs_list.add_widget(item)

    def _clear_old(self):
        self.audit.clear_old_logs(30)
        self._load_logs()
        from kivymd.app import MDApp
        MDApp.get_running_app().show_snackbar("🗑️ تم المسح")

    def _go_back(self):
        self.manager.current = "main"
