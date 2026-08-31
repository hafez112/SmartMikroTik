#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""دليل الاستخدام التفاعلي"""

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.expansionpanel import MDExpansionPanel, MDExpansionPanelThreeLine
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout


class Tab(MDFloatLayout, MDTabsBase):
    pass


class HelpScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_ui()

    def _setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        toolbar = MDTopAppBar(title="❓ دليل الاستخدام", left_action_items=[["arrow-right", lambda x: self._go_back()]], elevation=4)
        layout.add_widget(toolbar)
        tabs = MDTabs()

        start_tab = Tab(title="البداية")
        self._setup_start_guide(start_tab)
        tabs.add_widget(start_tab)

        cmds_tab = Tab(title="الأوامر")
        self._setup_commands_guide(cmds_tab)
        tabs.add_widget(cmds_tab)

        about_tab = Tab(title="حول")
        self._setup_about(about_tab)
        tabs.add_widget(about_tab)

        layout.add_widget(tabs)
        self.add_widget(layout)

    def _setup_start_guide(self, tab):
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        steps = [
            {'title': '1️⃣ إضافة جهاز', 'content': 'اضغط على زر "+" في شاشة الأجهزة. أدخل IP والبيانات. المنفذ الافتراضي 8728.'},
            {'title': '2️⃣ الاتصال', 'content': 'اضغط على أيقونة الاتصال بجانب الجهاز أو انتقل للتفاصيل.'},
            {'title': '3️⃣ موجه الأوامر', 'content': 'استخدم شاشة "الأوامر". اكتب "help" للمساعدة.'},
            {'title': '4️⃣ المساعد الذكي', 'content': 'انتقل لشاشة "ذكي" واسأل أي سؤال.'},
            {'title': '5️⃣ السكربتات', 'content': 'استخدم محرر السكربتات لكتابة وتشغيل سكربتات RouterOS.'},
            {'title': '6️⃣ المراقبة', 'content': 'شاشة "المراقبة" تعرض إحصائيات حية. فعّل التنبيهات.'},
        ]
        for step in steps:
            panel = MDExpansionPanel(
                content=MDLabel(text=step['content'], theme_text_color="Secondary", size_hint_y=None),
                panel_cls=MDExpansionPanelThreeLine(text=step['title'], secondary_text="اضغط للتفاصيل", tertiary_text="")
            )
            content.add_widget(panel)
        scroll.add_widget(content)
        tab.add_widget(scroll)

    def _setup_commands_guide(self, tab):
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        commands = [
            ("system resource print", "عرض موارد النظام"),
            ("ip address print", "عرض عناوين IP"),
            ("ip route print", "عرض جدول التوجيه"),
            ("interface print", "عرض الواجهات"),
            ("ip firewall filter print", "عرض قواعد الفايروول"),
            ("ip hotspot user print", "عرض مستخدمي الهوتسبوت"),
            ("user print", "عرض مستخدمي النظام"),
            ("log print", "عرض السجلات"),
            ("ping 8.8.8.8", "اختبار الاتصال"),
            ("system backup save", "نسخ احتياطي"),
            ("export", "تصدير الإعدادات"),
        ]
        for cmd, desc in commands:
            card = MDCard(size_hint=(1, None), height=dp(60), padding=dp(10), elevation=1)
            box = MDBoxLayout(orientation="vertical")
            box.add_widget(MDLabel(text=f"[font=RobotoMono-Regular]{cmd}[/font]", markup=True, theme_text_color="Primary", font_style="Subtitle1"))
            box.add_widget(MDLabel(text=desc, theme_text_color="Secondary", font_style="Caption"))
            card.add_widget(box)
            content.add_widget(card)
        scroll.add_widget(content)
        tab.add_widget(scroll)

    def _setup_about(self, tab):
        layout = MDBoxLayout(orientation="vertical", padding=dp(30), spacing=dp(20))
        layout.add_widget(MDLabel(text="[b]🤖 Smart MikroTik[/b]", markup=True, halign="center", font_style="H3", theme_text_color="Primary"))
        layout.add_widget(MDLabel(text="النظام الذكي لإدارة أجهزة MikroTik\nمع ذكاء اصطناعي محلي وخارجي", halign="center", theme_text_color="Secondary"))
        layout.add_widget(MDLabel(text="الإصدار 7.0", halign="center", font_style="H6"))
        features = MDLabel(
            text="[b]المميزات:[/b]\n✓ التحكم في MikroTik\n✓ موجه أوامر متقدم\n✓ ذكاء اصطناعي\n✓ مراقبة حية\n✓ سكربتات وجدولة\n✓ تنبيهات\n✓ نسخ احتياطي\n✓ تقارير\n✓ أدوات شبكة\n✓ أمان متقدم",
            markup=True, halign="center"
        )
        layout.add_widget(features)
        layout.add_widget(MDLabel(text="© 2024 Smart MikroTik\nمفتوح المصدر - MIT", halign="center", theme_text_color="Hint", font_style="Caption"))
        tab.add_widget(layout)

    def _go_back(self):
        self.manager.current = "main"
