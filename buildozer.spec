[app]
title = Smart MikroTik
package.name = smartmikrotik
package.domain = com.hafez112
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,db,json,txt
version = 7.0.2
requirements = python3,kivy==2.3.0,kivymd==1.2.0,routeros-api,paramiko,requests,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
# This is the actual python-for-android branch; the bare date is not a branch.
p4a.branch = release-2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
