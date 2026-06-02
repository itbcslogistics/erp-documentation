# 🔄 Alur Bisnis ERP BCS Logistics

Dokumen ini menjelaskan alur bisnis terintegrasi pada sistem ERP BCS Logistics, berfokus pada **Login Flow** dan **4 Modul Utama** yaitu: **Marketing, OCS (Operations Control System), Kasir, dan FMS (Fleet Management System)**.

---

## 1. Alur Login & Autentikasi (Login Flow)

Sistem menggunakan SvelteKit server-side authentication dengan HTTP-only Cookie (`auth_token`). Akses ke modul-modul dibatasi berdasarkan session token yang valid.

### Diagram Alur Login

```mermaid
sequenceDiagram
    autonumber
    actor User as "Pengguna / Staff"
    participant FE as "Frontend (/login)"
    participant Server as "SvelteKit Server (hooks.server.ts)"
    participant API as "Backend API (/api/v1/auth/login)"
    participant DB as "Database PostgreSQL"

    User->>FE: Input Email & Password
    FE->>Server: Kirim Form POST Request
    Server->>API: POST /api/v1/auth/login
    API->>DB: Validasi Kredensial & Role
    DB-->>API: Data Valid (User & Token)
    API-->>Server: "Response 200 OK (access_token & user info)"
    Server->>Server: Set HTTP-Only Cookie "auth_token"
    Server-->>FE: "Redirect ke Dashboard Utama (/)"
    FE->>User: "Tampilkan Dashboard dengan Akses Modul (Marketing, OCS, Kasir, FMS)"
```

---

## 2. Alur Bisnis Utama End-to-End (E2E Business Flow)

Alur bisnis ERP berpusat pada siklus hidup **Sales Order (SO)**, dimulai dari inisiasi oleh tim Marketing hingga penyelesaian keuangan oleh Kasir.

### Diagram Alur Utama (End-to-End)

```mermaid
flowchart TD
    %% Nodes
    Start(["Mulai"]) --> M1
    
    %% Marketing
    subgraph "Marketing Module"
        M1["Buat Sales Order<br/>Status: WAITING_UJO"]
        M3["Input Tarif & Kirim ke Customer<br/>Status: WAITING_CUSTOMER"]
        M4["Konfirmasi Customer Deal<br/>Status: READY_TO_DISPATCH"]
    end

    %% OCS
    subgraph "OCS Module"
        O1["Assign Unit & Driver + Input UJO<br/>Status: WAITING_TARIFF"]
        O2["Finalisasi Dispatch<br/>Status: DISPATCHED"]
        O3["Terima Surat Jalan & Input Realisasi<br/>Status: COMPLETED"]
    end

    %% Kasir
    subgraph "Kasir Module"
        K1["Pencairan Uang Jalan UJO<br/>ujo_payment_status = PAID"]
        K2["Pelunasan Biaya Tambahan<br/>closing_payment_status = PAID"]
    end

    %% Driver Execution
    subgraph "Driver Journey"
        D1["Ambil Unit & Jalan ke Origin (Loading)"]
        D2["Perjalanan ke Destination (Unloading)"]
        D3["Kembali ke Pool (Bawa Surat Jalan)"]
    end

    %% FMS Monitoring
    subgraph "FMS (Fleet Management System)"
        F1["Monitor Posisi Kendaraan & Live Map"]
        F2["Update Status Ketersediaan Unit"]
    end

    %% Flow Connections
    M1 --> O1
    O1 --> M3
    M3 --> M4
    M4 --> O2
    O2 --> K1
    K1 --> D1
    
    %% Driver Execution Cycle
    D1 --> D2
    D2 --> D3
    D3 --> O3
    
    %% Closing
    O3 --> K2
    K2 --> End(["Selesai"])

    %% Monitoring Links (Implicit)
    D1 -.-> F1
    D2 -.-> F1
    F2 -.-> M1
    F2 -.-> O1

    %% Styling
    classDef marketing fill:#ffe4e6,stroke:#f43f5e,stroke-width:2px,color:#881337
    classDef ocs fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e
    classDef kasir fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#064e3b
    classDef fms fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef driver fill:#fafaf9,stroke:#78716c,stroke-width:2px,color:#44403c
    classDef startEnd fill:#f5f5f4,stroke:#a8a29e,stroke-width:2px

    class M1,M3,M4 marketing
    class O1,O2,O3 ocs
    class K1,K2 kasir
    class D1,D2,D3 driver
    class F1,F2 fms
    class Start,End startEnd
```

---

## 3. Penjelasan Siklus Hidup Status Order (Sales Order Statuses)

Sistem melacak status order di tabel database `marketing.sales_order` dengan status transisi sebagai berikut:

| Status | Deskripsi | Modul Penanggung Jawab |
| :--- | :--- | :--- |
| `WAITING_UJO` | Order baru dibuat oleh Marketing, menunggu OCS menentukan Unit Truk, Supir, dan Uang Jalan (UJO). | **Marketing** (Inisiasi) |
| `WAITING_TARIFF` | OCS telah menetapkan Truk, Supir, dan input rincian UJO (Makan, Tol, Pokok). Menunggu Marketing menentukan tarif ke Customer. | **OCS** (Operational) |
| `WAITING_CUSTOMER` | Marketing telah mengisi nilai tarif penjualan ke Customer. Dokumen sedang ditinjau / menunggu persetujuan dari pihak Customer. | **Marketing** (Pricing) |
| `READY_TO_DISPATCH` | Customer menyetujui penawaran tarif. Order siap diberangkatkan oleh OCS. | **Marketing** (Confirmation) |
| `DISPATCHED` | OCS melakukan finalisasi dispatch. Permintaan bayar UJO terkirim ke Kasir. Truk mulai jalan. | **OCS** (Dispatch) |
| `COMPLETED` | Supir kembali membawa Surat Jalan. OCS melakukan closing dispatch dan menginput realisasi berat muatan & biaya tambahan. | **OCS** (Closing Dispatch) |
| `CANCELED` | Order dibatalkan oleh Marketing atau Customer. | **Marketing** / **System** |

---

## 4. Rincian Alur per Modul

Berikut adalah detail interaksi dan tanggung jawab spesifik pada masing-masing modul:

### A. Modul Marketing
Fokus utama Marketing adalah membuat pesanan, mengelola tarif untuk customer, dan memantau status persetujuan dari customer.

```mermaid
flowchart TD
    Start(["Mulai"]) --> A1["Pilih Customer"]
    A1 --> A2["Tentukan Rute: Origin & Destination"]
    A2 --> A3["Pilih Jenis Unit Truk"]
    A3 --> A4["Input Detail Muatan & Tanggal Kirim"]
    A4 --> A5[("Simpan Order Baru")]
    A5 --> A6["Status: WAITING_UJO"]
    A6 --> A7["Tunggu OCS Assign Unit & UJO"]
    A7 --> A8["Dapatkan Estimasi UJO dari OCS"]
    A8 --> A9["Input Tarif Penjualan ke Customer"]
    A9 --> A10["Kirim Quotation ke Customer"]
    A10 --> A11{"Customer Deal?"}
    A11 -- "Ya" --> A12["Konfirmasi Order"]
    A12 --> A13["Status: READY_TO_DISPATCH"]
    A11 -- "Tidak" --> A14["Batalkan / Edit Order"]
    A14 --> A15["Status: CANCELED"]

    %% Styling
    classDef marketing fill:#ffe4e6,stroke:#f43f5e,stroke-width:2px,color:#881337
    classDef db fill:#f5f5f4,stroke:#78716c,stroke-width:2px
    class A1,A2,A3,A4,A6,A7,A8,A9,A10,A11,A12,A13,A14,A15,Start marketing
    class A5 db
```

---

### B. Modul OCS (Operations Control System)
OCS berfokus pada operasional fisik: menetapkan kendaraan & supir, menghitung uang jalan (UJO), memantau kepulangan supir, dan melakukan pencatatan aktual pengiriman (surat jalan).

```mermaid
flowchart TD
    Start(["Terima Order WAITING_UJO"]) --> B1["Pilih Unit Truk & Driver yang Tersedia"]
    B1 --> B2["Input Komponen UJO:<br/>1. Uang Makan<br/>2. Uang Tol<br/>3. Uang Pokok"]
    B2 --> B3["Status berubah: WAITING_TARIFF"]
    B3 --> B4["Tunggu Marketing Deal dengan Customer"]
    B4 --> B5["Terima Notifikasi: READY_TO_DISPATCH"]
    B5 --> B6["Klik Tombol Finalize & Send UJO"]
    B6 --> B7["Status berubah: DISPATCHED"]
    B7 --> B8[("Kirim Data UJO ke Kasir")]
    B8 --> B9["Supir Jalan & Lakukan Pengiriman"]
    B9 --> B10["Supir Kembali & Serahkan Surat Jalan"]
    B10 --> B11["Klik Closing Dispatch"]
    B11 --> B12["Input Berat Aktual (Real Weight) & Beban Tambahan jika ada"]
    B12 --> B13["Status berubah: COMPLETED"]
    B13 --> B14[("Kirim Data Closing DN ke Kasir")]

    %% Styling
    classDef ocs fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e
    classDef db fill:#f5f5f4,stroke:#78716c,stroke-width:2px
    class Start,B1,B2,B3,B4,B5,B6,B7,B9,B10,B11,B12,B13 ocs
    class B8,B14 db
```

---

### C. Modul Kasir (Cash & Payment)
Kasir bertanggung jawab penuh terhadap aliran uang masuk dan keluar terkait operasional pengiriman (uang jalan supir dan penyelesaian biaya tambahan setelah closing).

```mermaid
flowchart TD
    Start(["Mulai"]) --> C1["Tinjau Antrean UJO di Fitur UJO"]
    C1 --> C2{"Apakah Dispatch Sudah Finalized?"}
    C2 -- "Belum" --> C3["Data Belum Ditampilkan di Kasir"]
    C2 -- "Sudah" --> C4["Tampilkan Data UJO dengan status UNPAID"]
    C4 --> C5["Klik Tombol Cairkan"]
    C5 --> C6["Serahkan Uang Jalan Fisik ke Supir"]
    C6 --> C7[("Update Database:<br/>ujo_payment_status = PAID")]

    %% Closing Section
    C7 --> C8["Tunggu OCS melakukan Closing Dispatch"]
    C8 --> C9["Tinjau Antrean Closing DN"]
    C9 --> C10["Periksa Selisih Tonnage & Beban Biaya Tambahan"]
    C10 --> C11["Klik Pelunasan / Closing DN"]
    C11 --> C12[("Update Database:<br/>closing_payment_status = PAID")]
    C12 --> End(["Selesai"])

    %% Styling
    classDef kasir fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#064e3b
    classDef db fill:#f5f5f4,stroke:#78716c,stroke-width:2px
    class Start,End,C1,C2,C3,C4,C5,C6,C8,C9,C10,C11 kasir
    class C7,C12 db
```

---

### D. Modul FMS (Fleet Management System)
FMS bertindak sebagai modul monitoring pasif dan manajemen aset. FMS melacak kondisi armada secara real-time dan mengelola data master armada.

```mermaid
flowchart TD
    Start(["Mulai"]) --> D1["Overview & Command Center"]
    D1 --> D2["Live Map: Lacak Lokasi GPS Truk Real-Time"]
    D1 --> D3["Route History: Riwayat Perjalanan Armada"]
    D1 --> D4["Master Unit & Driver: Kelola Ketersediaan & Status"]
    D1 --> D5["Maintenance & Service: Jadwal Oli, Ban, Sparepart"]
    D1 --> D6["Fuel & Expenses Tracking"]

    %% Hubungan ke modul lain
    D4 -.->|"Kirim info unit siap jalan"| Marketing["Marketing"]
    D4 -.->|"Kirim info unit siap jalan"| OCS["OCS"]

    %% Styling
    classDef fms fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    class Start,D1,D2,D3,D4,D5,D6,Marketing,OCS fms
```

---

## 5. Ringkasan Hubungan Antar Data di Database

Seluruh data transaksi di atas terhubung ke tabel `marketing.sales_order` sebagai tabel utama (single source of truth untuk transaksi pengiriman). Berikut skema hubungan kolomnya:

* **Truk & Supir** di-assign oleh **OCS** dan disimpan di:
  * `assigned_unit_id` (relasi ke tabel `fleet.unit`)
  * `assigned_driver_id` (relasi ke tabel `master.m_drivers`)
* **Uang Jalan Operasional (UJO)** di-input oleh **OCS**, dikonfirmasi **Marketing**, dan dicairkan oleh **Kasir**:
  * `ujo_makan` & `ujo_tol` (diset oleh OCS)
  * `estimated_ujo` (total uang jalan pokok + makan + tol)
  * `ujo_payment_status` (UNPAID -> PAID saat dicairkan Kasir)
* **Tarif Penjualan** diset oleh **Marketing**:
  * `tariff` (harga jual ke customer)
* **Closing / Kepulangan Truk** di-input oleh **OCS** dan dibayarkan oleh **Kasir**:
  * `real_weight` (berat aktual bongkar)
  * `extra_cost` & `extra_cost_desc` (tambahan biaya tak terduga di jalan)
  * `closing_payment_status` (UNPAID -> PAID setelah diselesaikan Kasir).
