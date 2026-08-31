#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إدارة السكربتات والجدولة"""

import json
from datetime import datetime, timedelta
from database import DatabaseManager


class ScriptsManager:
    def __init__(self):
        self.db = DatabaseManager()

    def create_script(self, name, content, device_id=None, schedule=None):
        script_data = {'name': name, 'content': content, 'device_id': device_id, 'schedule': schedule}
        return self.db.add_script(script_data)

    def run_script(self, script_id, device_id=None):
        scripts = self.db.get_scripts()
        script = next((s for s in scripts if s['id'] == script_id), None)
        if not script:
            return False, "السكربت غير موجود"
        target_device = device_id or script.get('device_id')
        if not target_device:
            return False, "لم يتم تحديد جهاز"
        from mikrotik_api import MikroTikAPI
        api = MikroTikAPI()
        device = self.db.get_device(target_device)
        if not device:
            return False, "الجهاز غير موجود"
        try:
            result = api.execute_command(device, script['content'])
            self.db.log_command(target_device, script['content'], result, 'success')
            return True, result
        except Exception as e:
            self.db.log_command(target_device, script['content'], str(e), 'error')
            return False, str(e)

    def get_preset_scripts(self):
        return [
            {'name': 'إعادة تشغيل يومية', 'description': 'إعادة تشغيل الجهاز كل يوم',
             'content': '/system scheduler add name="daily-reboot" start-time=03:00:00 interval=1d on-event="/system reboot" policy=reboot'},
            {'name': 'نسخ احتياطي يومي', 'description': 'نسخ احتياطي يومي',
             'content': '/system backup save name=([/system identity get name] . "-backup-")'},
            {'name': 'تنظيف السجلات', 'description': 'مسح السجلات القديمة',
             'content': '/log print where topics~"info" file=log.txt; /file remove log.txt'},
            {'name': 'مراقبة الحرارة', 'description': 'التحقق من درجة الحرارة',
             'content': ':local temp [/system health get temperature]; :if ($temp > 70) do={/tool e-mail send to="admin@example.com" subject="Alert" body=$temp}'},
            {'name': 'حظر IP مشبوه', 'description': 'حظر عناوين IP',
             'content': '/ip firewall filter add chain=input action=drop src-address-list=ssh_blacklist comment="Drop SSH brute force"'},
            {'name': 'تسريع DNS', 'description': 'إعداد DNS Cache',
             'content': '/ip dns set allow-remote-requests=yes cache-size=2048KiB max-udp-packet-size=4096'},
        ]
