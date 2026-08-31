#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""المساعد الذكي - AI محلي وخارجي"""

import os
import json
import requests
from database import DatabaseManager


class AIAssistant:
    def __init__(self):
        self.db = DatabaseManager()
        self.settings = self.db.get_ai_settings()
        self.local_model = None
        self._init_local_model()

    def _init_local_model(self):
        if self.settings.get('use_local') and self.settings.get('local_model_path'):
            try:
                from llama_cpp import Llama
                self.local_model = Llama(
                    model_path=self.settings['local_model_path'],
                    n_ctx=2048, n_threads=4
                )
            except ImportError:
                print("llama_cpp not installed")
            except Exception as e:
                print(f"Error loading local model: {e}")

    def ask(self, question, context=None):
        system_prompt = """أنت مساعد ذكي متخصص في أجهزة MikroTik وشبكات الاتصالات.
يمكنك مساعدة المستخدم في كتابة سكربتات RouterOS وحل مشاكل الشبكات.
أجب باللغة العربية ما لم يطلب المستخدم غير ذلك."""
        full_prompt = f"{system_prompt}\n\nسؤال المستخدم: {question}"
        if context:
            full_prompt += f"\n\nسياق الجهاز:\n{context}"
        if self.local_model and self.settings.get('use_local'):
            return self._ask_local(full_prompt)
        return self._ask_external(full_prompt)

    def _ask_local(self, prompt):
        try:
            output = self.local_model(prompt, max_tokens=512, temperature=0.7, stop=["User:", "Human:"])
            return output['choices'][0]['text'].strip()
        except Exception as e:
            return f"خطأ في النموذج المحلي: {str(e)}"

    def _ask_external(self, prompt):
        api_key = self.settings.get('api_key')
        api_url = self.settings.get('api_url', 'https://api.groq.com/openai/v1/chat/completions')
        model = self.settings.get('model', 'llama-3.1-70b-versatile')
        if not api_key:
            return "⚠️ لم يتم إعداد مفتاح API."
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "أنت مساعد ذكي متخصص في MikroTik. أجب بالعربية."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7, "max_tokens": 1024
            }
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return f"❌ خطأ في الاتصال بـ API: {str(e)}"
        except Exception as e:
            return f"❌ خطأ: {str(e)}"

    def generate_script(self, description, device_type="mikrotik"):
        prompt = f"""اكتب سكربت RouterOS للمطلوب التالي:
{description}
اكتب السكربت فقط بدون أي شرح إضافي."""
        return self.ask(prompt)

    def analyze_config(self, config_text):
        prompt = f"""حلل هذه الإعدادات وأعطِ توصيات لتحسين الأمان والأداء:
{config_text[:2000]}
قدم التحليل بالنقاط."""
        return self.ask(prompt)

    def troubleshoot(self, error_message, device_info=None):
        context = f"معلومات الجهاز: {device_info}" if device_info else ""
        prompt = f"""سياق: {context}
رسالة الخطأ: {error_message}
ما هي المشكلة المحتملة وكيفية حلها؟"""
        return self.ask(prompt)
