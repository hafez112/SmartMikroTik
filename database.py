#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إدارة قاعدة البيانات SQLite"""

import sqlite3
import os
import json
from datetime import datetime


class DatabaseManager:
    DB_NAME = "smart_mikrotik.db"

    def __init__(self):
        self.conn = None
        self._init_db()

    def _get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.DB_NAME)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, ip TEXT NOT NULL,
                username TEXT NOT NULL, password TEXT NOT NULL,
                port INTEGER DEFAULT 8728, model TEXT, version TEXT,
                status TEXT DEFAULT 'unknown', last_seen TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, content TEXT NOT NULL,
                device_id INTEGER, schedule TEXT, enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER, command TEXT NOT NULL,
                output TEXT, status TEXT,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_settings (
                id INTEGER PRIMARY KEY, api_key TEXT,
                api_url TEXT DEFAULT 'https://api.groq.com/openai/v1/chat/completions',
                model TEXT DEFAULT 'llama-3.1-70b-versatile',
                local_model_path TEXT, use_local INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER, name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            )
        ''')
        conn.commit()

    def add_device(self, device_data):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO devices (name, ip, username, password, port, model, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_data['name'], device_data['ip'], device_data['username'],
                device_data['password'], device_data.get('port', 8728),
                device_data.get('model', ''), device_data.get('status', 'unknown')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding device: {e}")
            return False

    def get_all_devices(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_device(self, device_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_device_status(self, device_id, status):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET status = ?, last_seen = ? WHERE id = ?
        ''', (status, datetime.now().isoformat(), device_id))
        conn.commit()

    def delete_device(self, device_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        conn.commit()

    def add_script(self, script_data):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scripts (name, content, device_id, schedule)
                VALUES (?, ?, ?, ?)
            ''', (
                script_data['name'], script_data['content'],
                script_data.get('device_id'), script_data.get('schedule')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding script: {e}")
            return False

    def get_scripts(self, device_id=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if device_id:
            cursor.execute("SELECT * FROM scripts WHERE device_id = ? OR device_id IS NULL", (device_id,))
        else:
            cursor.execute("SELECT * FROM scripts")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def log_command(self, device_id, command, output, status):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO command_logs (device_id, command, output, status)
            VALUES (?, ?, ?, ?)
        ''', (device_id, command, output, status))
        conn.commit()

    def get_ai_settings(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_settings WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO ai_settings (id) VALUES (1)")
            conn.commit()
            return self.get_ai_settings()
        return dict(row)

    def update_ai_settings(self, settings):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE ai_settings SET api_key = ?, api_url = ?, model = ?,
            local_model_path = ?, use_local = ? WHERE id = 1
        ''', (
            settings.get('api_key'), settings.get('api_url'), settings.get('model'),
            settings.get('local_model_path'), settings.get('use_local', 0)
        ))
        conn.commit()
