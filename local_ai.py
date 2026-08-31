#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""محرك الذكاء الاصطناعي المحلي"""

import os
import threading
import urllib.request
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
from kivymd.uix.dialog import MDDialog


class LocalAIModel:
    MODELS_DIR = "models"

    def __init__(self):
        self.model = None
        self.model_path = None
        self.is_loaded = False
        self.context_size = 2048
        self._ensure_models_dir()

    def _ensure_models_dir(self):
        if not os.path.exists(self.MODELS_DIR):
            os.makedirs(self.MODELS_DIR)

    def list_available_models(self):
        models = []
        if os.path.exists(self.MODELS_DIR):
            for file in os.listdir(self.MODELS_DIR):
                if file.endswith(('.gguf', '.bin')):
                    size_mb = os.path.getsize(os.path.join(self.MODELS_DIR, file)) / (1024 * 1024)
                    models.append({'name': file, 'path': os.path.join(self.MODELS_DIR, file), 'size_mb': round(size_mb, 2)})
        return models

    def load_model(self, model_path):
        try:
            from llama_cpp import Llama
            self.model = Llama(model_path=model_path, n_ctx=self.context_size, n_threads=4, n_batch=512, verbose=False)
            self.model_path = model_path
            self.is_loaded = True
            return True, "✅ تم التحميل"
        except ImportError:
            return False, "❌ llama_cpp غير مثبت"
        except Exception as e:
            return False, f"❌ خطأ: {str(e)}"

    def unload_model(self):
        self.model = None
        self.is_loaded = False
        self.model_path = None
        return True, "✅ تم إلغاء التحميل"

    def generate(self, prompt, max_tokens=512, temperature=0.7):
        if not self.is_loaded or self.model is None:
            return "❌ لا يوجد نموذج"
        try:
            system_prompt = "أنت خبير في MikroTik. أجب بالعربية."
            full_prompt = f"{system_prompt}\n\nالمستخدم: {prompt}\n\nالرد:"
            output = self.model(full_prompt, max_tokens=max_tokens, temperature=temperature, stop=["المستخدم:", "Human:"], echo=False)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            return f"❌ خطأ: {str(e)}"

    def generate_script(self, description):
        prompt = f"اكتب سكربت RouterOS:\n{description}\nاكتب السكربت فقط."
        return self.generate(prompt, max_tokens=1024, temperature=0.3)


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
                toolbar = MDTopAppBar(title="🧠 الذكاء المحلي", left_action_items=[["arrow-right", lambda x: self._go_back()]], elevation=4)
                layout.add_widget(toolbar)
                scroll = MDScrollView()
                content = MDBoxLayout(orientation="vertical", spacing=dp(15), padding=dp(15), size_hint_y=None)
                content.bind(minimum_height=content.setter('height'))

                self.status_card = MDCard(size_hint=(1, None), height=dp(80), padding=dp(15), elevation=2)
                self.status_label = MDLabel(text="⏹️ لا يوجد نموذج", halign="center", font_style="H5")
                self.status_card.add_widget(self.status_label)
                content.add_widget(self.status_card)

                content.add_widget(MDLabel(text="[b]📦 النماذج المتاحة[/b]", markup=True, font_style="H6"))
                self.models_list = MDList()
                content.add_widget(self.models_list)

                buttons_box = MDBoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
                buttons_box.add_widget(MDRaisedButton(text="🔄 تحديث", on_release=lambda x: self._refresh_models()))
                buttons_box.add_widget(MDRaisedButton(text="📥 تحميل", md_bg_color="#4CAF50", on_release=lambda x: self._show_download_dialog()))
                buttons_box.add_widget(MDRaisedButton(text="⏏️ إلغاء", md_bg_color="#F44336", on_release=lambda x: self._unload_model()))
                content.add_widget(buttons_box)

                content.add_widget(MDLabel(text="[b]⚙️ الإعدادات[/b]", markup=True, font_style="H6"))
                self.temp_slider = MDTextField(hint_text="درجة الحرارة", text="0.7", mode="rectangle")
                self.tokens_field = MDTextField(hint_text="الحد الأقصى", text="512", mode="rectangle")
                content.add_widget(self.temp_slider)
                content.add_widget(self.tokens_field)

                content.add_widget(MDLabel(text="[b]🧪 اختبار[/b]", markup=True, font_style="H6"))
                self.test_input = MDTextField(hint_text="اكتب سؤالاً...", multiline=True, mode="rectangle")
                content.add_widget(self.test_input)
                content.add_widget(MDRaisedButton(text="▶️ اختبار", md_bg_color="#9C27B0", on_release=self._test_model))
                self.test_result = MDLabel(text="", theme_text_color="Secondary", markup=True)
                content.add_widget(self.test_result)

                scroll.add_widget(content)
                layout.add_widget(scroll)
                self.add_widget(layout)
                Clock.schedule_once(lambda dt: self._refresh_models(), 0.5)

            def _refresh_models(self):
                self.models_list.clear_widgets()
                models = self.local_ai.list_available_models()
                if not models:
                    self.models_list.add_widget(OneLineListItem(text="لا توجد نماذج"))
                    return
                for model in models:
                    item = TwoLineListItem(text=f"📦 {model['name']}", secondary_text=f"{model['size_mb']} MB", on_release=lambda x, m=model: self._load_model(m['path']))
                    self.models_list.add_widget(item)

            def _load_model(self, path):
                self.status_label.text = "⏳ جاري التحميل..."
                def load():
                    success, msg = self.local_ai.load_model(path)
                    Clock.schedule_once(lambda dt: self._update_status(success, msg), 0)
                threading.Thread(target=load, daemon=True).start()

            def _update_status(self, success, msg):
                if success:
                    self.status_card.md_bg_color = "#E8F5E9"
                    self.status_label.text = "🟢 جاهز"
                else:
                    self.status_card.md_bg_color = "#FFEBEE"
                    self.status_label.text = msg
                from kivymd.app import MDApp
                MDApp.get_running_app().show_snackbar(msg, "success" if success else "error")

            def _unload_model(self):
                success, msg = self.local_ai.unload_model()
                self.status_card.md_bg_color = "#FFF3E0"
                self.status_label.text = "⏹️ لا يوجد نموذج"
                from kivymd.app import MDApp
                MDApp.get_running_app().show_snackbar(msg)

            def _show_download_dialog(self):
                content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, height=dp(200))
                info = MDLabel(text="📥 حمل نموذج GGUF من HuggingFace\nضعه في مجلد models/", theme_text_color="Secondary")
                content.add_widget(info)
                url_field = MDTextField(hint_text="رابط التحميل...", mode="rectangle")
                content.add_widget(url_field)
                dialog = MDDialog(title="📥 تحميل نموذج", type="custom", content_cls=content,
                    buttons=[
                        MDRaisedButton(text="إغلاق", on_release=lambda x: dialog.dismiss()),
                        MDRaisedButton(text="تحميل", md_bg_color="#4CAF50", on_release=lambda x: self._download_model(dialog, url_field.text)),
                    ],
                )
                dialog.open()

            def _download_model(self, dialog, url):
                dialog.dismiss()
                if not url:
                    return
                from kivymd.app import MDApp
                MDApp.get_running_app().show_snackbar("⏳ جاري التحميل...")
                def download():
                    try:
                        filename = os.path.basename(url)
                        filepath = os.path.join("models", filename)
                        urllib.request.urlretrieve(url, filepath)
                        Clock.schedule_once(lambda dt: self._refresh_models(), 0)
                        Clock.schedule_once(lambda dt: MDApp.get_running_app().show_snackbar("✅ تم التحميل"), 0)
                    except Exception as e:
                        Clock.schedule_once(lambda dt: MDApp.get_running_app().show_snackbar(f"❌ فشل: {str(e)}", "error"), 0)
                threading.Thread(target=download, daemon=True).start()

            def _test_model(self, instance):
                if not self.local_ai.is_loaded:
                    from kivymd.app import MDApp
                    MDApp.get_running_app().show_snackbar("❌ حمل نموذجاً أولاً", "error")
                    return
                prompt = self.test_input.text.strip()
                if not prompt:
                    return
                self.test_result.text = "⏳ جاري التفكير..."
                def test():
                    result = self.local_ai.generate(prompt, max_tokens=int(self.tokens_field.text or 512), temperature=float(self.temp_slider.text or 0.7))
                    Clock.schedule_once(lambda dt: self._show_test_result(result), 0)
                threading.Thread(target=test, daemon=True).start()

            def _show_test_result(self, result):
                self.test_result.text = f"[b]النتيجة:[/b]\n{result}"

            def _go_back(self):
                self.manager.current = "main"

        return LocalAISettingsScreen
