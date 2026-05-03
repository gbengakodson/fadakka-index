[app]
title = Fadakka Index
package.name = fadakkaindex
package.domain = com.fadakka
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.1.1,yfinance==0.2.36,pandas==2.1.4,numpy==1.26.2,plyer==2.1.0,pillow==10.1.0,requests==2.31.0,matplotlib==3.8.2
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 1
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,POST_NOTIFICATIONS,VIBRATE
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 30
android.gradle_dependencies = 
android.arch = arm64-v8a
android.allow_backup = True
android.presplash_color = #0A0A0F
android.presplash = assets/splash.png
android.icon = assets/icon.png
android.notification_icon = assets/icon.png
ios.kivy_version = 2.3.0