#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""واجهة برمجة تطبيقات MikroTik"""

import routeros_api
import paramiko
import socket
from datetime import datetime


class MikroTikAPI:
    def __init__(self):
        self.connections = {}

    def connect_api(self, device):
        try:
            connection = routeros_api.RouterOsApiPool(
                device['ip'], username=device['username'],
                password=device['password'], port=device.get('port', 8728),
                plaintext_login=True
            )
            api = connection.get_api()
            self.connections[device['id']] = connection
            return api
        except Exception as e:
            raise Exception(f"فشل الاتصال بـ API: {str(e)}")

    def connect_ssh(self, device):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                device['ip'], username=device['username'],
                password=device['password'], port=device.get('ssh_port', 22), timeout=10
            )
            self.connections[f"ssh_{device['id']}"] = client
            return client
        except Exception as e:
            raise Exception(f"فشل الاتصال بـ SSH: {str(e)}")

    def test_connection(self, device):
        try:
            api = self.connect_api(device)
            resource = api.get_resource('/system/resource')
            info = resource.get()[0]
            return {
                'status': 'online', 'model': info.get('board-name', 'Unknown'),
                'version': info.get('version', 'Unknown'),
                'uptime': info.get('uptime', 'Unknown'),
                'cpu_load': info.get('cpu-load', '0'),
                'free_memory': info.get('free-memory', '0')
            }
        except Exception as e:
            return {'status': 'offline', 'error': str(e)}

    def execute_command(self, device, command):
        try:
            api = self.connect_api(device)
            parts = command.split()
            base_cmd = parts[0] if parts else ""

            if base_cmd == "ping" and len(parts) > 1:
                ping = api.get_resource('/ping')
                result = ping.call(address=parts[1], count=parts[2] if len(parts) > 2 else "4")
                return "\n".join([str(r) for r in result])
            elif command == "system resource print":
                resource = api.get_resource('/system/resource')
                result = resource.get()[0]
                return self._format_dict(result)
            elif command == "ip address print":
                addresses = api.get_resource('/ip/address')
                result = addresses.get()
                return self._format_list(result, ['address', 'network', 'interface'])
            elif command == "interface print":
                interfaces = api.get_resource('/interface')
                result = interfaces.get()
                return self._format_list(result, ['name', 'type', 'mtu', 'running'])
            elif command == "ip hotspot user print":
                users = api.get_resource('/ip/hotspot/user')
                result = users.get()
                return self._format_list(result, ['name', 'profile', 'disabled'])
            else:
                return self._execute_ssh_command(device, command)
        except Exception as e:
            return f"خطأ: {str(e)}"

    def _format_dict(self, data):
        output = ""
        for key, value in data.items():
            output += f"[color=#2196F3]{key}[/color]: {value}\n"
        return output

    def _format_list(self, data, keys):
        if not data:
            return "لا توجد بيانات"
        output = ""
        for i, item in enumerate(data, 1):
            output += f"[b]#{i}[/b] "
            for key in keys:
                if key in item:
                    output += f"[color=#FF9800]{key}[/color]={item[key]} "
            output += "\n"
        return output

    def _execute_ssh_command(self, device, command):
        try:
            client = self.connect_ssh(device)
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            client.close()
            if error:
                return f"خطأ: {error}"
            return output
        except Exception as e:
            return f"فشل SSH: {str(e)}"

    def get_interfaces(self, device):
        try:
            api = self.connect_api(device)
            interfaces = api.get_resource('/interface')
            return interfaces.get()
        except:
            return []

    def get_dhcp_leases(self, device):
        try:
            api = self.connect_api(device)
            dhcp = api.get_resource('/ip/dhcp-server/lease')
            return dhcp.get()
        except:
            return []

    def get_hotspot_users(self, device):
        try:
            api = self.connect_api(device)
            users = api.get_resource('/ip/hotspot/user')
            return users.get()
        except:
            return []

    def add_hotspot_user(self, device, username, password, profile="default"):
        try:
            api = self.connect_api(device)
            users = api.get_resource('/ip/hotspot/user')
            users.add(name=username, password=password, profile=profile)
            return True
        except Exception as e:
            raise e

    def remove_hotspot_user(self, device, username):
        try:
            api = self.connect_api(device)
            users = api.get_resource('/ip/hotspot/user')
            user = users.get(name=username)
            if user:
                users.remove(id=user[0]['id'])
                return True
            return False
        except Exception as e:
            raise e

    def reboot(self, device):
        try:
            api = self.connect_api(device)
            system = api.get_resource('/system')
            system.call('reboot')
            return True
        except Exception as e:
            raise e

    def backup_config(self, device, name=None):
        try:
            api = self.connect_api(device)
            backup = api.get_resource('/system/backup')
            backup_name = name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup.call('save', name=backup_name)
            return backup_name
        except Exception as e:
            raise e

    def export_config(self, device):
        try:
            client = self.connect_ssh(device)
            stdin, stdout, stderr = client.exec_command('/export')
            config = stdout.read().decode('utf-8')
            client.close()
            return config
        except Exception as e:
            raise e

    def disconnect(self, device_id):
        if device_id in self.connections:
            try:
                self.connections[device_id].disconnect()
                del self.connections[device_id]
            except:
                pass
        ssh_key = f"ssh_{device_id}"
        if ssh_key in self.connections:
            try:
                self.connections[ssh_key].close()
                del self.connections[ssh_key]
            except:
                pass

    def disconnect_all(self):
        for key in list(self.connections.keys()):
            try:
                if key.startswith('ssh_'):
                    self.connections[key].close()
                else:
                    self.connections[key].disconnect()
            except:
                pass
        self.connections.clear()
