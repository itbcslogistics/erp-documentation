import os
import sys
import time
from playwright.sync_api import sync_playwright

# Konfigurasi
LOGIN_URL = "https://erp.bcslabs.tech/login"
EMAIL = "acengsatu@gamil.com"
PASSWORD = "password123"
SCREENSHOT_DIR = os.path.abspath("docs/images")

# Pastikan folder screenshot ada
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def slugify(text):
    """Mengubah teks menjadi nama file yang valid."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text

def crawl_module_sidebar(page, module_name):
    """Mendalami dan mengambil screenshot dari semua submenu di sidebar modul."""
    print(f"[{module_name}] Mendeteksi sidebar navigasi...")
    time.sleep(4)  # Tunggu rendering sidebar
    
    # Ambil semua tautan di sidebar/navigasi modul
    # Di Laravel/Filament/modern apps, sidebar biasanya ada di aside atau nav atau kelas sidebar
    sidebar_links = page.evaluate("""() => {
        const links = [];
        // Cari elemen navigasi di sidebar
        const navElements = document.querySelectorAll('aside a, nav a, .sidebar a, [class*="sidebar"] a, [class*="nav"] a');
        navElements.forEach(a => {
            const href = a.getAttribute('href');
            const text = a.innerText.trim();
            if (href && !href.startsWith('#') && !href.includes('logout') && !href.includes('signout')) {
                if (text && !links.some(l => l.href === href)) {
                    links.push({ text: text, href: href });
                }
            }
        });
        
        // Jika tidak ketemu dengan selector khusus, ambil semua link yang berada di bagian kiri/atas layar
        if (links.length === 0) {
            const allAnchors = document.querySelectorAll('a');
            allAnchors.forEach(a => {
                const href = a.getAttribute('href');
                const text = a.innerText.trim();
                const rect = a.getBoundingClientRect();
                // Biasanya sidebar berada di sisi kiri (X < 300)
                if (href && rect.left < 300 && !href.startsWith('#') && !href.includes('logout') && !href.includes('signout')) {
                    if (text && !links.some(l => l.href === href)) {
                        links.push({ text: text, href: href });
                    }
                }
            });
        }
        return links;
    }""")
    
    print(f"[{module_name}] Ditemukan {len(sidebar_links)} submenu:")
    for idx, link in enumerate(sidebar_links, 1):
        print(f"  {idx}. {link['text']} -> {link['href']}")
        
    visited_urls = set()
    for link in sidebar_links:
        text = link["text"]
        href = link["href"]
        
        # Hindari duplikat
        if href in visited_urls:
            continue
        visited_urls.add(href)
        
        # Buat URL lengkap
        full_url = href if href.startswith("http") else f"https://erp.bcslabs.tech{href}"
        if "logout" in full_url.lower() or "signout" in full_url.lower():
            continue
            
        print(f"[{module_name}] Mengunjungi submenu: '{text}' -> {full_url}")
        try:
            page.goto(full_url)
            page.wait_for_load_state("networkidle")
            time.sleep(3) # Tunggu rendering tabel/data
            
            slug_menu = slugify(text)
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"{slugify(module_name)}_{slug_menu}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"[{module_name}] Screenshot submenu '{text}' disimpan di {screenshot_path}")
        except Exception as e:
            print(f"[{module_name}] Gagal mengunjungi submenu '{text}': {e}")

def run():
    print("Memulai browser automation menggunakan Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1
        )
        page = context.new_page()

        print(f"Membuka halaman login: {LOGIN_URL}...")
        page.goto(LOGIN_URL)
        page.wait_for_load_state("networkidle")
        
        # Ambil screenshot halaman login
        login_screenshot_path = os.path.join(SCREENSHOT_DIR, "login_page.png")
        page.screenshot(path=login_screenshot_path, full_page=True)
        print(f"Screenshot login disimpan di {login_screenshot_path}")

        # Isi form login
        try:
            email_input = page.locator('input[type="email"], input[name="email"], #email').first
            password_input = page.locator('input[type="password"], input[name="password"], #password').first
            
            email_input.fill(EMAIL)
            password_input.fill(PASSWORD)
            
            submit_btn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Masuk"), button:has-text("Sign in")').first
            submit_btn.click()
            print("Kredensial dikirim, menunggu halaman termuat...")
            time.sleep(5) # Tunggu rendering halaman dashboard
        except Exception as e:
            print(f"Error saat login: {e}")
            browser.close()
            return

        # Verifikasi keberhasilan login secara visual (apakah ada kata 'Welcome' atau 'FMS')
        content = page.content()
        if "Welcome" in content or "FMS" in content or "HRIS" in content:
            print("Berhasil Login!")
        else:
            print("Gagal Login. Silakan periksa kredensial atau halaman login.")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "login_failed.png"))
            browser.close()
            return

        # Ambil screenshot Dashboard Utama
        dashboard_screenshot_path = os.path.join(SCREENSHOT_DIR, "dashboard.png")
        page.screenshot(path=dashboard_screenshot_path, full_page=True)
        print(f"Screenshot Dashboard utama disimpan di {dashboard_screenshot_path}")

        # Daftar modul yang terdeteksi di Dashboard
        modules = [
            {"name": "FMS", "label": "FMS"},
            {"name": "OCS", "label": "OCS"},
            {"name": "HRIS", "label": "HRIS"},
            {"name": "Marketing", "label": "Marketing"},
            {"name": "PMS", "label": "PMS"},
            {"name": "Kasir", "label": "Kasir"},
            {"name": "Finance", "label": "Finance"},
            {"name": "DMS", "label": "DMS"},
            {"name": "QHSE", "label": "QHSE"}
        ]

        main_tab_url = page.url

        for mod in modules:
            name = mod["name"]
            label = mod["label"]
            print(f"\n========================================\nMemproses Modul: {name}\n========================================")
            
            # Kembali ke dashboard utama terlebih dahulu jika tidak di dashboard
            if page.url != main_tab_url:
                print(f"Kembali ke Dashboard Utama...")
                page.goto(main_tab_url)
                time.sleep(3)

            # Cari card modul di halaman dashboard
            # Kita bisa klik elemen teks modul atau card-nya
            try:
                # Cari elemen teks nama modul yang terlihat di dashboard
                module_element = page.locator(f"text={label}").first
                if not module_element.is_visible():
                    print(f"Modul {name} tidak terlihat di dashboard, melewati...")
                    continue
                
                print(f"Mengklik Modul {name}...")
                
                # Deteksi jika klik membuka tab baru
                with context.expect_page(timeout=10000) as new_page_info:
                    module_element.click()
                
                new_page = new_page_info.value
                new_page.wait_for_load_state("networkidle")
                time.sleep(4)
                
                print(f"Modul {name} terbuka di tab baru: {new_page.url}")
                
                # Ambil screenshot halaman utama modul
                screenshot_mod_path = os.path.join(SCREENSHOT_DIR, f"{slugify(name)}_main.png")
                new_page.screenshot(path=screenshot_mod_path, full_page=True)
                print(f"Screenshot utama modul {name} disimpan di {screenshot_mod_path}")
                
                # Crawl sidebar dari halaman baru tersebut
                crawl_module_sidebar(new_page, name)
                
                # Setelah selesai, tutup tab modul untuk menghemat memory
                new_page.close()
                print(f"Tab Modul {name} ditutup.")
            except Exception as e:
                # Jika tidak membuka tab baru, mungkin ia merubah URL di tab saat ini
                print(f"Modul {name} tidak membuka tab baru atau terjadi error: {e}")
                print("Mencoba klik langsung dan crawl di tab yang sama...")
                try:
                    # Refresh dashboard
                    page.goto(main_tab_url)
                    time.sleep(3)
                    
                    module_element = page.locator(f"text={label}").first
                    module_element.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(4)
                    
                    # Ambil screenshot halaman utama modul
                    screenshot_mod_path = os.path.join(SCREENSHOT_DIR, f"{slugify(name)}_main.png")
                    page.screenshot(path=screenshot_mod_path, full_page=True)
                    print(f"Screenshot utama modul {name} disimpan di {screenshot_mod_path}")
                    
                    # Crawl sidebar
                    crawl_module_sidebar(page, name)
                except Exception as ex:
                    print(f"Gagal memproses modul {name} di tab yang sama: {ex}")

        browser.close()
        print("\nProses crawling seluruh modul ERP selesai dengan sukses!")

if __name__ == "__main__":
    run()
