[app]
title = Smart MikroTik
package.name = smartmikrotik
package.domain = com.yourcompany
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json,txt
version = 7.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,routeros-api,paramiko,requests,cryptography,bcrypt,pillow,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
android.allow_backup = True
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
