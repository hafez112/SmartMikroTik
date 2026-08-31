#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إدارة النسخ الاحتياطي"""

import os
import json
from datetime import datetime
from database import DatabaseManager


class BackupManager:
    BACKUP_DIR = "backups"

    def __init__(self):
        self.db = DatabaseManager()
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        if not os.path.exists(self.BACKUP_DIR):
            os.makedirs(self.BACKUP_DIR)

    def create_backup(self, device, name=None):
        try:
            from mikrotik_api import MikroTikAPI
            api = MikroTikAPI()
            config = api.export_config(device)
            backup_name = name or f"backup_{device['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            local_path = os.path.join(self.BACKUP_DIR, f"{backup_name}.rsc")
            with open(local_path, 'w') as f:
                f.write(config)
            conn = self.db._get_connection()
            conn.execute('''
                INSERT INTO backups (device_id, name, content) VALUES (?, ?, ?)
            ''', (device['id'], backup_name, config))
            conn.commit()
            return {'success': True, 'name': backup_name, 'path': local_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def export_config(self, device, format='rsc'):
        try:
            from mikrotik_api import MikroTikAPI
            api = MikroTikAPI()
            if format == 'rsc':
                config = api.export_config(device)
                filename = f"export_{device['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.rsc"
            else:
                return {'success': False, 'error': 'صيغة غير مدعومة'}
            filepath = os.path.join(self.BACKUP_DIR, filename)
            with open(filepath, 'w') as f:
                f.write(config)
            return {'success': True, 'filename': filename, 'path': filepath}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def list_backups(self, device_id=None):
        try:
            conn = self.db._get_connection()
            if device_id:
                cursor = conn.execute("SELECT * FROM backups WHERE device_id = ? ORDER BY created_at DESC", (device_id,))
            else:
                cursor = conn.execute("SELECT * FROM backups ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    def delete_backup(self, backup_id):
        try:
            conn = self.db._get_connection()
            conn.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
            conn.commit()
            return True
        except:
            return False
