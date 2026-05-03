# ============================================
# FADAKKA INDEX - Google Colab APK Builder
# ============================================

# STEP 1: Install dependencies
!pip install buildozer cython
!sudo apt update
!sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# STEP 2: Upload your files
from google.colab import files
print("Upload your fadakka_app_source.zip file...")
uploaded = files.upload()

# STEP 3: Extract files
import zipfile
import os

with zipfile.ZipFile('fadakka_app_source.zip', 'r') as zf:
    zf.extractall('fadakka_app')

os.chdir('fadakka_app')
print("Files extracted:")
!ls -la

# STEP 4: Create buildozer.spec
spec_content = """
[app]
title = Fadakka Index
package.name = fadakkaindex
package.domain = com.fadakka
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.1.1,yfinance==0.2.36,pandas==2.1.4,numpy==1.26.2,plyer==2.1.0,pillow==10.1.0,requests==2.31.0,matplotlib==3.8.2
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,POST_NOTIFICATIONS,VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.arch = arm64-v8a
android.allow_backup = True
android.presplash_color = #0A0A0F

[buildozer]
log_level = 2
warn_on_root = 1
"""

with open('buildozer.spec', 'w') as f:
    f.write(spec_content)

print("buildozer.spec created!")

# STEP 5: Build APK (this takes 15-30 minutes)
print("\nStarting APK build... This will take 15-30 minutes.")
print("Please be patient!\n")

!buildozer android debug

# STEP 6: Download the APK
print("\nBuild complete! Downloading APK...")
from google.colab import files
import glob

apk_files = glob.glob('bin/*.apk')
if apk_files:
    for apk in apk_files:
        files.download(apk)
    print("APK downloaded! Install on your Android phone.")
else:
    print("APK not found. Check build errors above.")