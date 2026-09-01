[app]
title = Smart MikroTik
package.name = smartmikrotik
package.domain = com.yourcompany
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json,txt
version = 7.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,routeros-api,paramiko,requests,cryptography,bcrypt,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.python_version = 3.11
p4a.local_recipes = 

[buildozer]
log_level = 2
warn_on_root = 1
