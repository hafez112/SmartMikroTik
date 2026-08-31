#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""نظام الأمان المتقدم"""

import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class SecurityManager:
    def __init__(self):
        self.key_file = ".secret_key"
        self._key = None
        self._ensure_key()

    def _ensure_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self._key = f.read()
        else:
            self._key = Fernet.generate_key() if CRYPTO_AVAILABLE else os.urandom(32)
            with open(self.key_file, 'wb') as f:
                f.write(self._key)

    def encrypt(self, data):
        if not CRYPTO_AVAILABLE:
            return self._simple_encrypt(data)
        try:
            f = Fernet(self._key)
            return f.encrypt(data.encode()).decode()
        except:
            return self._simple_encrypt(data)

    def decrypt(self, encrypted_data):
        if not CRYPTO_AVAILABLE:
            return self._simple_decrypt(encrypted_data)
        try:
            f = Fernet(self._key)
            return f.decrypt(encrypted_data.encode()).decode()
        except:
            return self._simple_decrypt(encrypted_data)

    def _simple_encrypt(self, data):
        key = self._key[:16]
        result = []
        for i, char in enumerate(data):
            result.append(chr(ord(char) ^ ord(key[i % len(key)])))
        return base64.b64encode(''.join(result).encode()).decode()

    def _simple_decrypt(self, data):
        try:
            decoded = base64.b64decode(data).decode()
            key = self._key[:16]
            result = []
            for i, char in enumerate(decoded):
                result.append(chr(ord(char) ^ ord(key[i % len(key)])))
            return ''.join(result)
        except:
            return data

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt, pwd_hash.hex()

    def verify_password(self, password, salt, hash_value):
        _, computed_hash = self.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, hash_value)

    def generate_token(self, length=32):
        return secrets.token_urlsafe(length)

    def sanitize_input(self, user_input):
        if not isinstance(user_input, str):
            return ""
        dangerous = [';', '&', '|', '\`', '$', '<', '>', \'\\']
        for char in dangerous:
            user_input = user_input.replace(char, '')
        return user_input.strip()


class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.security = SecurityManager()
        self.sessions = {}
        self._init_auth_table()

    def _init_auth_table(self):
        try:
            conn = self.db._get_connection()
            conn.execute('''
                CREATE TABLE IF NOT EXISTS app_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            cursor = conn.execute("SELECT COUNT(*) FROM app_users")
            if cursor.fetchone()[0] == 0:
                salt, pwd_hash = self.security.hash_password("admin")
                conn.execute('''INSERT INTO app_users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)''', ('admin', pwd_hash, salt, 'admin'))
            conn.commit()
        except Exception as e:
            print(f"Auth init error: {e}")

    def authenticate(self, username, password):
        try:
            conn = self.db._get_connection()
            cursor = conn.execute("SELECT id, password_hash, salt, role, is_active FROM app_users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                return None, "اسم المستخدم غير موجود"
            if not user['is_active']:
                return None, "الحساب معطل"
            if self.security.verify_password(password, user['salt'], user['password_hash']):
                conn.execute("UPDATE app_users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user['id']))
                conn.commit()
                token = self.security.generate_token()
                self.sessions[token] = {'user_id': user['id'], 'username': username, 'role': user['role'], 'expires': datetime.now() + timedelta(hours=24)}
                return token, "success"
            else:
                return None, "كلمة المرور غير صحيحة"
        except Exception as e:
            return None, str(e)

    def verify_token(self, token):
        if token not in self.sessions:
            return None
        session = self.sessions[token]
        if datetime.now() > session['expires']:
            del self.sessions[token]
            return None
        return session

    def logout(self, token):
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

    def change_password(self, user_id, old_password, new_password):
        try:
            conn = self.db._get_connection()
            cursor = conn.execute("SELECT password_hash, salt FROM app_users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return False, "المستخدم غير موجود"
            if not self.security.verify_password(old_password, user['salt'], user['password_hash']):
                return False, "كلمة المرور الحالية غير صحيحة"
            salt, pwd_hash = self.security.hash_password(new_password)
            conn.execute("UPDATE app_users SET password_hash = ?, salt = ? WHERE id = ?", (pwd_hash, salt, user_id))
            conn.commit()
            return True, "تم تغيير كلمة المرور"
        except Exception as e:
            return False, str(e)

    def add_user(self, username, password, role='user'):
        try:
            salt, pwd_hash = self.security.hash_password(password)
            conn = self.db._get_connection()
            conn.execute('''INSERT INTO app_users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)''', (username, pwd_hash, salt, role))
            conn.commit()
            return True, "تم إضافة المستخدم"
        except Exception as e:
            return False, str(e)

    def get_users(self):
        try:
            conn = self.db._get_connection()
            cursor = conn.execute("SELECT id, username, role, created_at, last_login, is_active FROM app_users")
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    def delete_user(self, user_id):
        try:
            conn = self.db._get_connection()
            conn.execute("DELETE FROM app_users WHERE id = ?", (user_id,))
            conn.commit()
            return True
        except:
            return False
