import os
import re
import time
import markdown
from playwright.sync_api import sync_playwright

MD_FILE = "docs/latar_belakang.md"
PDF_OUTPUT = "Proposal_Migrasi_ERP_BCS_Logistics.pdf"

def parse_github_alerts(text):
    """Mengubah sintaks GitHub Alerts (> [!NOTE] dll) menjadi kontainer HTML yang rapi."""
    # Pattern untuk blockquote yang mengandung alert
    # Contoh:
    # > [!NOTE]
    # > Isi catatan baris 1
    # > Isi catatan baris 2
    
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
        elif in_alert and line.strip().startswith('>'):
            # Ambil isi teks setelah karakter '>'
            content = line.strip()[1:].strip()
            alert_content.append(content)
        elif in_alert and not line.strip().startswith('>'):
            # Alert berakhir, render ke HTML div
            title = "CATATAN" if alert_type == "note" else "PERINGATAN"
            alert_html = f'<div class="alert alert-{alert_type}"><strong>{title}:</strong> {" ".join(alert_content)}</div>'
            new_lines.append(alert_html)
            new_lines.append(line)
            in_alert = False
        else:
            new_lines.append(line)
            
    # Jika file berakhir saat masih di dalam blok alert
    if in_alert:
        title = "CATATAN" if alert_type == "note" else "PERINGATAN"
        alert_html = f'<div class="alert alert-{alert_type}"><strong>{title}:</strong> {" ".join(alert_content)}</div>'
        new_lines.append(alert_html)
        
    return '\n'.join(new_lines)

def run():
    print("Membaca file Markdown...")
    if not os.path.exists(MD_FILE):
        print(f"Error: File {MD_FILE} tidak ditemukan.")
        return
        
    with open(MD_FILE, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Bersihkan / hapus metadata link file lokal agar PDF terlihat rapi dan formal
    # Contoh: [hooks.server.ts](file:///Users/...) -> hooks.server.ts
    md_text = re.sub(r'\[([^\]]+)\]\(file:///[^\)]+\)', r'\1', md_text)

    # Parsing GitHub alerts khusus
    md_text = parse_github_alerts(md_text)

    # Ekstraksi Blok Mermaid sebelum Markdown merendernya menjadi escape HTML codeblock
    mermaid_blocks = []
    def replace_mermaid(match):
        block = match.group(1).strip()
        mermaid_blocks.append(block)
        return f"<!-- MERMAID_PLACEHOLDER_{len(mermaid_blocks) - 1} -->"
        
    md_text_clean = re.sub(r'```mermaid\s*(.*?)\s*```', replace_mermaid, md_text, flags=re.DOTALL)

    # Konversi Markdown ke HTML (kecuali blok Mermaid yang sudah di-placeholder)
    print("Mengonversi Markdown ke HTML...")
    html_body = markdown.markdown(md_text_clean, extensions=['tables', 'fenced_code'])

    # Kembalikan blok Mermaid mentah ke dalam kontainer div dengan class="mermaid"
    for idx, block in enumerate(mermaid_blocks):
        placeholder = f"<!-- MERMAID_PLACEHOLDER_{idx} -->"
        html_body = html_body.replace(placeholder, f'<div class="mermaid">{block}</div>')

    # Susun HTML Lengkap dengan CSS Cetak A4 Premium
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Proposal Migrasi ERP BCS Logistics</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<!-- Import Mermaid JS untuk merender flowchart secara dinamis -->
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
        margin: 0; /* Biarkan Playwright menangani margin halaman secara penuh */
    }}
    body {{
        font-family: 'Inter', sans-serif;
        color: #0f172a;
        line-height: 1.6;
        font-size: 10.5pt;
        background-color: #ffffff;
    }}
    
    /* Cover Page - Didesain khusus muat penuh dalam 1 halaman A4 */
    .cover-page {{
        page-break-after: always;
        page-break-inside: avoid;
        text-align: center;
        padding-top: 30mm;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        height: 235mm; /* Tinggi maksimal area cetak A4 setelah dikurangi margin */
    }}
    .logo {{
        font-size: 16pt;
        font-weight: 700;
        color: #2563eb;
        letter-spacing: 2px;
        margin-bottom: 25mm;
    }}
    .cover-title {{
        font-size: 24pt;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 8mm;
        text-transform: uppercase;
        line-height: 1.3;
    }}
    .cover-subtitle {{
        font-size: 12pt;
        color: #475569;
        margin-bottom: 35mm;
        font-weight: 400;
    }}
    .cover-meta {{
        font-size: 10pt;
        color: #334155;
        border-top: 2px solid #e2e8f0;
        padding-top: 10mm;
        text-align: left;
        width: 100%;
        margin-top: auto; /* Tarik metadata ke bagian bawah halaman sampul */
    }}
    .cover-meta p {{
        margin: 4px 0;
    }}
    
    /* Content Typography */
    .content {{
        padding-top: 10mm;
    }}
    h1 {{
        font-size: 18pt;
        color: #1e3a8a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 6px;
        margin-top: 30px;
        margin-bottom: 15px;
        page-break-after: avoid;
        page-break-before: always;
    }}
    .content > h1:first-of-type {{
        page-break-before: avoid; /* H1 pertama langsung setelah cover page */
    }}
    h2 {{
        font-size: 13.5pt;
        color: #0f172a;
        margin-top: 25px;
        margin-bottom: 10px;
        page-break-after: avoid;
    }}
    h3 {{
        font-size: 11pt;
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
    
    /* Table Styling */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 9.5pt;
        page-break-inside: avoid;
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
    
    /* Mermaid Diagram */
    .mermaid {{
        display: flex;
        justify-content: center;
        margin: 25px 0;
        page-break-inside: avoid;
    }}
    
    /* Utility */
    .avoid-break {{
        page-break-inside: avoid;
    }}
</style>
</head>
<body>
    <div class="cover-page">
        <div class="logo">BCS LOGISTICS</div>
        <div class="cover-title">Proposal Migrasi Sistem & Justifikasi Teknis ERP</div>
        <div class="cover-subtitle">Menggantikan Sistem Legacy CodeIgniter 2 & 3 Menuju Arsitektur ERP Terintegrasi</div>
        <div class="cover-meta">
            <p><strong>Perihal:</strong> Justifikasi Teknis dan Operasional Migrasi Sistem</p>
            <p><strong>Diajukan Kepada:</strong> Dewan Direksi BCS Logistics</p>
            <p><strong>Dipersiapkan Oleh:</strong> Tim IT & Pengembangan Sistem</p>
            <p><strong>Tanggal:</strong> Juni 2026</p>
            <p><strong>Status Dokumen:</strong> Final (Ready for Submission)</p>
        </div>
    </div>
    
    <div class="content">
        {html_body}
    </div>
</body>
</html>
"""

    temp_html_path = "temp_print.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print("Menjalankan browser automation (Playwright) untuk ekspor PDF...")
    with sync_playwright() as p:
        # Jalankan headless browser Chromium
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Buka HTML lokal
        page.goto(f"file:///{os.path.abspath(temp_html_path)}")
        page.wait_for_load_state("domcontentloaded")
        
        # Tunggu 4 detik agar Mermaid JS menyelesaikan render SVG diagram alir secara visual
        print("Menunggu rendering diagram alur Mermaid...")
        time.sleep(4)
        
        # Cetak ke PDF
        print(f"Mencetak ke PDF: {PDF_OUTPUT}...")
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
        
    print(f"Sukses! File PDF resmi telah berhasil dibuat di: {PDF_OUTPUT}")

if __name__ == "__main__":
    run()
