import os
import re
import time
import markdown
from playwright.sync_api import sync_playwright

# Daftar modul dokumentasi sesuai urutan navigasi mkdocs.yml
DOCS_FILES = [
    ("Beranda", "docs/index.md"),
    ("Proposal & Latar Belakang", "docs/latar_belakang.md"),
    ("Dashboard Portal", "docs/dashboard.md"),
    ("Alur Bisnis ERP", "docs/alur_bisnis.md"),
    ("FMS (Fleet Management)", "docs/fms.md"),
    ("OCS (Operations Hub)", "docs/ocs.md"),
    ("HRIS (Human Capital)", "docs/hris.md"),
    ("Marketing (Growth Engine)", "docs/marketing.md"),
    ("PMS (Procurement)", "docs/pms.md"),
    ("Kasir (Cash & Payment)", "docs/kasir.md"),
    ("Finance (Economic Control)", "docs/finance.md"),
    ("DMS (Document Asset)", "docs/dms.md"),
    ("QHSE (Quality & Safety)", "docs/qhse.md")
]

PDF_OUTPUT = "Dokumentasi_Lengkap_ERP_BCS_Logistics.pdf"

def parse_github_alerts(text):
    """Mengubah sintaks GitHub Alerts (> [!NOTE] dll) menjadi kontainer HTML yang rapi."""
    lines = text.split('\n')
    new_lines = []
    in_alert = False
    alert_type = ""
    alert_content = []
    
    for line in lines:
        if line.strip().startswith('> [!NOTE]'):
            in_alert = True
            alert_type = "note"
            alert_content = []
        elif line.strip().startswith('> [!WARNING]'):
            in_alert = True
            alert_type = "warning"
            alert_content = []
        elif line.strip().startswith('> [!TIP]'):
            # Perlakukan tip seperti note demi konsistensi visual di PDF
            in_alert = True
            alert_type = "note"
            alert_content = []
        elif in_alert and line.strip().startswith('>'):
            content = line.strip()[1:].strip()
            alert_content.append(content)
        elif in_alert and not line.strip().startswith('>'):
            title = "CATATAN" if alert_type == "note" else "PERINGATAN"
            alert_html = f'<div class="alert alert-{alert_type}"><strong>{title}:</strong> {" ".join(alert_content)}</div>'
            new_lines.append(alert_html)
            new_lines.append(line)
            in_alert = False
        else:
            new_lines.append(line)
            
    if in_alert:
        title = "CATATAN" if alert_type == "note" else "PERINGATAN"
        alert_html = f'<div class="alert alert-{alert_type}"><strong>{title}:</strong> {" ".join(alert_content)}</div>'
        new_lines.append(alert_html)
        
    return '\n'.join(new_lines)

def run():
    print("Menggabungkan seluruh modul dokumentasi...")
    combined_body_html = ""
    
    for idx, (title, filepath) in enumerate(DOCS_FILES, 1):
        print(f" Memproses [{idx}/{len(DOCS_FILES)}] {title} ({filepath})...")
        if not os.path.exists(filepath):
            print(f"  Peringatan: File {filepath} tidak ditemukan, melewati...")
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            md_text = f.read()
            
        # Bersihkan tautan file lokal IDE agar bersih di PDF
        md_text = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+\)', r'\1', md_text)
        
        # Parsing Github Alerts
        md_text = parse_github_alerts(md_text)
        
        # Ekstraksi Mermaid diagram di setiap file
        mermaid_blocks = []
        def replace_mermaid(match):
            block = match.group(1).strip()
            mermaid_blocks.append(block)
            return f"<!-- MERMAID_PLACEHOLDER_{len(mermaid_blocks) - 1} -->"
            
        md_text_clean = re.sub(r'```mermaid\s*(.*?)\s*```', replace_mermaid, md_text, flags=re.DOTALL)
        
        # Konversi ke HTML
        html_segment = markdown.markdown(md_text_clean, extensions=['tables', 'fenced_code'])
        
        # Kembalikan diagram Mermaid ke div HTML
        for m_idx, block in enumerate(mermaid_blocks):
            placeholder = f"<!-- MERMAID_PLACEHOLDER_{m_idx} -->"
            html_segment = html_segment.replace(placeholder, f'<div class="mermaid">{block}</div>')
            
        # Bungkus segmen di dalam section agar setiap modul mulai dari halaman baru (page break)
        # H1 pertama di modul tersebut akan dipaksa mulai di halaman baru lewat CSS
        combined_body_html += f'<section class="doc-module">\n{html_segment}\n</section>\n'

    # Sesuaikan path gambar agar mengarah ke docs/images (karena html dibuat di folder root)
    print("Menyesuaikan path gambar screenshot...")
    combined_body_html = combined_body_html.replace('src="images/', 'src="docs/images/')

    # Susun Template HTML Dokumentasi Gabungan dengan Styling Premium
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Panduan & Dokumentasi Lengkap ERP BCS Logistics</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<!-- Import Mermaid JS -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>
    mermaid.initialize({{
        startOnLoad: true,
        theme: 'neutral',
        flowchart: {{ useMaxWidth: false, htmlLabels: true }}
    }});
</script>
<style>
    @page {{
        size: A4;
        margin: 25mm 20mm 25mm 20mm;
    }}
    body {{
        font-family: 'Inter', sans-serif;
        color: #0f172a;
        line-height: 1.6;
        font-size: 10.5pt;
        background-color: #ffffff;
    }}
    
    /* Cover Page */
    .cover-page {{
        height: 90vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        page-break-after: always;
        padding-top: 50px;
    }}
    .logo {{
        font-size: 18pt;
        font-weight: 700;
        color: #2563eb;
        letter-spacing: 2px;
        margin-bottom: 60px;
    }}
    .cover-title {{
        font-size: 24pt;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 20px;
        text-transform: uppercase;
        line-height: 1.3;
        max-width: 650px;
    }}
    .cover-subtitle {{
        font-size: 13pt;
        color: #475569;
        margin-bottom: 60px;
        max-width: 550px;
        font-weight: 400;
    }}
    .cover-meta {{
        font-size: 10.5pt;
        color: #334155;
        border-top: 2px solid #e2e8f0;
        padding-top: 30px;
        width: 80%;
        text-align: left;
        margin-top: auto;
    }}
    .cover-meta p {{
        margin: 6px 0;
    }}
    
    /* Module break - memaksa setiap file dokumen mulai di halaman baru */
    .doc-module {{
        page-break-before: always;
    }}
    .content > .doc-module:first-of-type {{
        page-break-before: avoid; /* Beranda (index) langsung setelah cover page */
    }}
    
    /* CSS Helper untuk mencegah heading yatim piatu (orphan heading) */
    .avoid-break {{
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }}
    
    /* Typography */
    h1 {{
        font-size: 18pt;
        color: #1e3a8a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 6px;
        margin-top: 30px;
        margin-bottom: 15px;
        page-break-after: avoid;
    }}
    h2 {{
        font-size: 14pt;
        color: #0f172a;
        margin-top: 25px;
        margin-bottom: 12px;
        page-break-after: avoid;
    }}
    h3 {{
        font-size: 11.5pt;
        color: #1e293b;
        margin-top: 20px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 12px;
        text-align: justify;
    }}
    ul, ol {{
        margin-top: 0;
        margin-bottom: 15px;
        padding-left: 20px;
    }}
    li {{
        margin-bottom: 6px;
    }}
    
    /* Gambar Screenshot Premium & Auto-fit */
    img {{
        max-width: 100%;
        max-height: 160mm; /* Batasi agar screenshot tinggi tidak menjorok ke halaman baru */
        object-fit: contain;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        margin: 15px 0;
        display: block;
        page-break-inside: avoid;
    }}
    
    /* Table Styling */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 9.5pt;
        page-break-inside: avoid;
    }}
    tr {{
        page-break-inside: avoid; /* Baris tabel tidak boleh terpotong di tengah halaman */
    }}
    th, td {{
        border: 1px solid #cbd5e1;
        padding: 8px 10px;
        text-align: left;
        vertical-align: top;
    }}
    th {{
        background-color: #f1f5f9;
        color: #0f172a;
        font-weight: 600;
    }}
    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    
    /* Alert / Blockquote Styling */
    .alert {{
        padding: 12px 15px;
        border-left: 4px solid;
        margin: 15px 0;
        border-radius: 4px;
        font-size: 10pt;
        page-break-inside: avoid;
    }}
    .alert-note {{
        background-color: #eff6ff;
        border-color: #2563eb;
        color: #1e40af;
    }}
    .alert-warning {{
        background-color: #fffbeb;
        border-color: #d97706;
        color: #92400e;
    }}
    
    /* Mermaid Diagram & Auto-scale */
    .mermaid {{
        display: flex;
        justify-content: center;
        margin: 25px 0;
        page-break-inside: avoid;
    }}
    .mermaid svg {{
        max-width: 100% !important; /* Mencegah bagan melebar memotong kertas kanan */
        height: auto !important;
    }}
</style>
</head>
<body>
    <div class="cover-page">
        <div class="logo">BCS LOGISTICS</div>
        <div class="cover-title">Panduan &amp; Dokumentasi Lengkap ERP BCS Logistics</div>
        <div class="cover-subtitle">Kompilasi Manual Pengguna, Analisis Alur Bisnis, dan Justifikasi Teknis Seluruh Modul ERP</div>
        <div class="cover-meta">
            <p><strong>Perihal:</strong> Buku Dokumentasi Resmi Penggunaan Sistem ERP</p>
            <p><strong>Diajukan Kepada:</strong> Dewan Direksi PT BCS Logistics</p>
            <p><strong>Dipersiapkan Oleh:</strong> Tim IT &amp; Pengembangan Sistem</p>
            <p><strong>Tanggal:</strong> Juni 2026</p>
            <p><strong>Status Dokumen:</strong> Consolidated Version 1.0 (Official)</p>
        </div>
    </div>
    
    <div class="content">
        {combined_body_html}
    </div>
</body>
</html>
"""

    # Post-processing HTML: Bungkus setiap Heading yang diikuti langsung oleh diagram Mermaid atau gambar 
    # di dalam kontainer <div class="avoid-break"> agar mereka terdorong bersamaan ke halaman berikutnya (mencegah orphan heading)
    print("Mencegah pemotongan diagram alur dan heading...")
    
    # 1. Bungkus heading diikuti oleh Mermaid diagram
    combined_body_html = re.sub(
        r'(<h[1-6][^>]*>.*?</h[1-6]>)\s*(<div class="mermaid">.*?</div>)',
        r'<div class="avoid-break">\1\2</div>',
        combined_body_html,
        flags=re.DOTALL
    )
    
    # 2. Bungkus heading diikuti oleh Gambar (dalam tag paragraph atau langsung img)
    combined_body_html = re.sub(
        r'(<h[1-6][^>]*>.*?</h[1-6]>)\s*(<p>\s*<img[^>]*>\s*</p>|<img[^>]*>)',
        r'<div class="avoid-break">\1\2</div>',
        combined_body_html,
        flags=re.DOTALL
    )

    temp_html_path = "temp_print_docs.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print("Menjalankan Playwright untuk ekspor Buku Dokumentasi PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Buka HTML lokal
        page.goto(f"file:///{os.path.abspath(temp_html_path)}")
        page.wait_for_load_state("domcontentloaded")
        
        # Tunggu 6 detik agar seluruh diagram Mermaid JS ter-render lengkap
        print("Menunggu seluruh diagram alur Mermaid selesai dirender...")
        time.sleep(6)
        
        # Cetak ke PDF
        print(f"Mencetak Buku Dokumentasi PDF: {PDF_OUTPUT}...")
        page.pdf(
            path=PDF_OUTPUT,
            format="A4",
            print_background=True,
            margin={
                "top": "25mm",
                "bottom": "25mm",
                "left": "20mm",
                "right": "20mm"
            }
        )
        browser.close()
        
    # Hapus file temp HTML
    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)
        
    print(f"Sukses! Buku Dokumentasi Lengkap PDF telah dibuat di: {PDF_OUTPUT}")

if __name__ == "__main__":
    run()
