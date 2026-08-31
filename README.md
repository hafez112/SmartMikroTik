# 🤖 Smart MikroTik Manager v7.0

النظام الذكي الشامل لإدارة أجهزة **MikroTik** مع ذكاء اصطناعي محلي وخارجي.

![Version](https://img.shields.io/badge/version-7.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![Kivy](https://img.shields.io/badge/kivy-2.3.0-orange)

## ✨ المميزات

| الميزة | الوصف |
|--------|-------|
| 📡 **التحكم الكامل** | إدارة أجهزة MikroTik عبر API و SSH |
| 💻 **موجه أوامر متقدم** | CLI ذكي مع إكمال تلقائي وسجل |
| 🧠 **ذكاء اصطناعي** | محلي (llama.cpp) وخارجي (Groq/OpenAI) |
| 📊 **مراقبة حية** | رسوم بيانية لـ CPU/RAM/الشبكة |
| 📝 **سكربتات** | محرر + سكربتات جاهزة + توليد ذكي |
| ⏰ **جدولة** | مهام تلقائية دورية |
| 🔔 **تنبيهات** | إشعارات فورية عند المشاكل |
| 💾 **نسخ احتياطي** | تصدير واستيراد الإعدادات |
| 📈 **تقارير** | تقارير شاملة قابلة للتصدير |
| 🔧 **أدوات شبكة** | Ping, Port Scan, DNS Lookup |
| 🔒 **أمان متقدم** | تشفير + مصادقة + سجل تدقيق |

## 🚀 التثبيت السريع

```bash
# 1. تثبيت المتطلبات
pip install -r requirements.txt

# 2. تشغيل التطبيق
python main.py
```

## 📱 بناء APK

### الطريقة 1: GitHub Actions (موصى بها)
1. اذهب إلى [Actions](../../actions)
2. اضغط **Build APK**
3. اضغط **Run workflow**
4. انتظر 15-30 دقيقة
5. حمل APK من **Artifacts**

### الطريقة 2: محلياً في Termux
```bash
pkg install python python-pip git clang cmake -y
pip install buildozer cython
buildozer android debug
```

## 📂 هيكل المشروع

```
SmartMikroTik/
├── main.py                  # التطبيق الرئيسي
├── database.py              # قاعدة البيانات
├── mikrotik_api.py          # API الاتصال
├── ai_assistant.py          # المساعد الذكي
├── scripts_manager.py       # إدارة السكربتات
├── backup_manager.py        # النسخ الاحتياطي
├── device_detail_screen.py  # تفاصيل الجهاز
├── advanced_cli.py          # موجه الأوامر
├── monitor_screen.py        # المراقبة الحية
├── script_editor.py         # محرر السكربتات
├── scheduler.py             # نظام الجدولة
├── alerts.py                # التنبيهات
├── local_ai.py              # الذكاء المحلي
├── settings_screen.py       # الإعدادات
├── reports.py               # التقارير
├── network_tools.py         # أدوات الشبكة
├── performance.py           # تحسين الأداء
├── help_screen.py           # دليل الاستخدام
├── security.py              # الأمان
├── audit_log.py             # سجل التدقيق
├── requirements.txt         # المتطلبات
└── buildozer.spec           # إعدادات APK
```

## 🔐 الأمان

- تشفير كلمات المرور بـ PBKDF2-HMAC-SHA256
- جلسات مصادقة مع انتهاء صلاحية
- سجل تدقيق كامل لجميع العمليات
- تنظيف المدخلات من الأحرف الخطرة

## 📄 الترخيص

MIT License - مفتوح المصدر

---

<div dir="rtl">

**تم التطوير بواسطة:** hafez112

**الإصدار:** 7.0.0

</div>
