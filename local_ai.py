#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""واجهة الذكاء المحلي الاختيارية؛ لا تتطلب llama-cpp أثناء بناء APK."""

import os
import threading

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem, OneLineListItem
from kivymd.uix.toolbar import MDTopAppBar


class LocalAIModel:
    MODELS_DIR = "models"

    def __init__(self):
        self.model = None
        self.model_path = None
        self.is_loaded = False
        self.context_size = 2048
        os.makedirs(self.MODELS_DIR, exist_ok=True)

    def list_available_models(self):
        result = []
        for filename in os.listdir(self.MODELS_DIR):
            path = os.path.join(self.MODELS_DIR, filename)
            if filename.endswith((".gguf", ".bin")) and os.path.isfile(path):
                result.append({"name": filename, "path": path, "size_mb": round(os.path.getsize(path) / 1048576, 2)})
        return result

    def load_model(self, path):
        try:
            from llama_cpp import Llama
        except ImportError:
            return False, "❌ الذكاء المحلي غير متاح في APK الحالي"
        try:
            self.model = Llama(model_path=path, n_ctx=self.context_size, n_threads=4, n_batch=512, verbose=False)
            self.model_path = path
            self.is_loaded = True
            return True, "✅ تم تحميل النموذج"
        except Exception as exc:
            return False, f"❌ فشل تحميل النموذج: {exc}"

    def unload_model(self):
        self.model = None
        self.model_path = None
        self.is_loaded = False
        return True, "✅ تم إلغاء التحميل"

    def generate(self, prompt, max_tokens=512, temperature=0.7):
        if not self.is_loaded or self.model is None:
            return "❌ لا يوجد نموذج محمل"
        try:
            system_prompt = "أنت خبير MikroTik. أجب بالعربية."
            full_prompt = f"{system_prompt}\n\nالمستخدم: {prompt}\n\nالرد:"
            result = self.model(full_prompt, max_tokens=max_tokens, temperature=temperature, stop=["المستخدم:", "Human:"], echo=False)
            return result["choices"][0]["text"].strip()
        except Exception as exc:
            return f"❌ خطأ: {exc}"


class LocalAIScreen:
    @staticmethod
    def get_ui():
        class LocalAISettingsScreen(MDScreen):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.local_ai = LocalAIModel()
                self._setup_ui()

            def _setup_ui(self):
                layout = MDBoxLayout(orientation="vertical")
                layout.add_widget(MDTopAppBar(title="🧠 الذكاء المحلي", left_action_items=[["arrow-right", lambda x: self._go_back()]]))
                scroll = MDScrollView()
                content = MDBoxLayout(orientation="vertical", spacing=dp(15), padding=dp(15), size_hint_y=None)
                content.bind(minimum_height=content.setter("height"))
                self.status_card = MDCard(size_hint=(1, None), height=dp(80), padding=dp(15), elevation=2)
                self.status_label = MDLabel(text="⏹️ لا يوجد نموذج", halign="center", font_style="H5")
                self.status_card.add_widget(self.status_label)
                content.add_widget(self.status_card)
                content.add_widget(MDLabel(text="[b]📦 النماذج المتاحة[/b]", markup=True, font_style="H6"))
                self.models_list = MDList()
                content.add_widget(self.models_list)
                actions = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
                actions.add_widget(MDRaisedButton(text="🔄 تحديث", on_release=lambda x: self._refresh_models()))
                actions.add_widget(MDRaisedButton(text="⏏️ إلغاء", on_release=lambda x: self._unload_model()))
                content.add_widget(actions)
                self.test_input = MDTextField(hint_text="اكتب سؤالاً...", multiline=True, mode="rectangle")
                content.add_widget(self.test_input)
                content.add_widget(MDRaisedButton(text="▶️ اختبار", on_release=self._test_model))
                self.test_result = MDLabel(text="", markup=True)
                content.add_widget(self.test_result)
                scroll.add_widget(content)
                layout.add_widget(scroll)
                self.add_widget(layout)
                Clock.schedule_once(lambda dt: self._refresh_models(), 0.5)

            def _refresh_models(self):
                self.models_list.clear_widgets()
                models = self.local_ai.list_available_models()
                if not models:
                    self.models_list.add_widget(OneLineListItem(text="لا توجد نماذج محلية"))
                for model in models:
                    self.models_list.add_widget(TwoLineListItem(text=f"📦 {model['name']}", secondary_text=f"{model['size_mb']} MB", on_release=lambda x, m=model: self._load_model(m["path"])))

            def _load_model(self, path):
                self.status_label.text = "⏳ جاري التحميل..."
                def worker():
                    ok, message = self.local_ai.load_model(path)
                    Clock.schedule_once(lambda dt: self._update_status(ok, message), 0)
                threading.Thread(target=worker, daemon=True).start()

            def _update_status(self, ok, message):
                self.status_label.text = "🟢 جاهز" if ok else message
                from kivymd.app import MDApp
                MDApp.get_running_app().show_snackbar(message, "success" if ok else "error")

            def _unload_model(self):
                _, message = self.local_ai.unload_model()
                self.status_label.text = "⏹️ لا يوجد نموذج"
                from kivymd.app import MDApp
                MDApp.get_running_app().show_snackbar(message)

            def _test_model(self, instance):
                if not self.local_ai.is_loaded:
                    from kivymd.app import MDApp
                    MDApp.get_running_app().show_snackbar("❌ حمل نموذجاً أولاً", "error")
                    return
                prompt = self.test_input.text.strip()
                if prompt:
                    self.test_result.text = "[b]النتيجة:[/b]\n" + self.local_ai.generate(prompt)

            def _go_back(self):
                self.manager.current = "main"

        return LocalAISettingsScreen
