import os
import sys
import time
import shutil
from playwright.sync_api import sync_playwright

# Konfigurasi
LOGIN_URL = "https://erp.bcslabs.tech/login"
SCREENSHOT_DIR = os.path.abspath("docs/images")
LOGIN_SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, "login_page.png")
ARTIFACT_LOGIN_PATH = r"C:\Users\IT-01\.gemini\antigravity-ide\brain\8f4fc532-1fb0-4f98-a27a-ae662dfe34b3\login_page.png"

def run():
    print("Memulai browser automation untuk mengambil screenshot halaman login baru...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1
        )
        page = context.new_page()

        print(f"Membuka halaman login terbaru: {LOGIN_URL}...")
        page.goto(LOGIN_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(3) # Tunggu asset frontend baru selesai rendering
        
        print("Mengambil screenshot halaman login baru...")
        page.screenshot(path=LOGIN_SCREENSHOT_PATH, full_page=True)
        print(f"Screenshot baru berhasil disimpan di {LOGIN_SCREENSHOT_PATH}")
        
        # Salin ke folder artifact untuk memperbarui Walkthrough
        try:
            shutil.copy(LOGIN_SCREENSHOT_PATH, ARTIFACT_LOGIN_PATH)
            print(f"Screenshot baru berhasil disalin ke folder artifact: {ARTIFACT_LOGIN_PATH}")
        except Exception as e:
            print(f"Gagal menyalin screenshot ke artifact: {e}")
            
        browser.close()

if __name__ == "__main__":
    run()
