import os
import zipfile
import glob

# Create assets folder if not exists
if not os.path.exists('assets'):
    os.makedirs('assets')

# All files to include
files_to_zip = [
    'main.py',
    'services/__init__.py',
    'services/fadakka_engine.py',
    'services/nigerian_stocks.py',
    'utils/__init__.py',
    'assets/icon.png',
    'assets/splash.png',
]

# Check which files exist
print("Checking files:")
for f in files_to_zip:
    if os.path.exists(f):
        print(f"  ✅ {f}")
    else:
        print(f"  ❌ MISSING: {f}")

# Create zip
zip_name = 'fadakka_full.zip'
with zipfile.ZipFile(zip_name, 'w') as zf:
    for f in files_to_zip:
        if os.path.exists(f):
            zf.write(f)
            print(f"Added: {f}")

print(f"\n✅ Created: {zip_name}")
print(f"Size: {os.path.getsize(zip_name)} bytes")
print("\nNow upload this file to Colab!")