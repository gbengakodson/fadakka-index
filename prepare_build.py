import os
import zipfile

# Files to include
files_to_include = [
    'main.py',
    'services/fadakka_engine.py',
    'services/nigerian_stocks.py',
    'services/__init__.py',
    'utils/__init__.py',
]

# Create zip
zip_name = 'fadakka_app_source.zip'
with zipfile.ZipFile(zip_name, 'w') as zf:
    for file in files_to_include:
        if os.path.exists(file):
            zf.write(file)
            print(f"Added: {file}")
        else:
            print(f"Missing: {file}")

print(f"\nCreated: {zip_name}")
print("\nUpload this zip to Google Colab!")