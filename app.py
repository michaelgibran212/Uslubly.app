import os
import json
import html
import streamlit as st
from google import genai
from google.genai import types

# 1. Konfigurasi Halaman & CSS Presisi
st.set_page_config(page_title="Uslubly - Pengecek Teks Arab Akademik", layout="wide")

st.markdown("""
    <style>
    /* 1. INPUT TEXTAREA & TEXTAREA HASIL SALIN (RATA KANAN PERFECT) */
    div[data-testid="stTextArea"] textarea {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Amiri', 'Traditional Arabic', serif !important;
        font-size: 20px !important;
        line-height: 1.8 !important;
        cursor: text !important;
    }

    /* 2. CONTAINER HASIL INTERAKTIF */
    .arabic-interactive-container {
        font-family: 'Amiri', 'Traditional Arabic', 'Scheherazade New', serif;
        font-size: 26px;
        direction: rtl !important;
        text-align: right !important;
        line-height: 2.5 !important;
        background-color: #f1f8e9;
        padding: 25px;
        border-radius: 12px;
        border-right: 6px solid #2e7d32;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        unicode-bidi: isolate;
        word-break: keep-all;
    }

    /* 3. KATA YANG DIPERBAIKI (HIGHLIGHT HIJAU ELEGANT) */
    .corrected-tooltip {
        position: relative;
        display: inline !important;
        background-color: #c8e6c9;
        border-bottom: 3px solid #2e7d32;
        color: #1b5e20;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        margin: 0 2px !important;
        direction: rtl !important;
    }

    /* 4. POPOVER BOX MELAYANG (TEKS INDONESIA LTR) */
    .corrected-tooltip .tooltip-content {
        visibility: hidden;
        width: 280px;
        background-color: #ffffff;
        color: #333333;
        text-align: left !important;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 999;
        bottom: 130%;
        right: 50%;
        transform: translateX(50%);
        box-shadow: 0px 4px 18px rgba(0,0,0,0.25);
        border: 1.5px solid #2e7d32;
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 13px;
        direction: ltr !important;
        line-height: 1.4;
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
        white-space: normal !important;
    }

    .corrected-tooltip .tooltip-content::after {
        content: "";
        position: absolute;
        top: 100%;
        right: 50%;
        margin-right: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #2e7d32 transparent transparent transparent;
    }

    .corrected-tooltip:hover .tooltip-content {
        visibility: visible;
        opacity: 1;
    }

    .badge-cat {
        background-color: #2e7d32;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 4px;
    }

    /* 5. FOOTER CREDIT LINE (ELEGANT & SUBTLE) */
    .app-footer {
        text-align: center;
        color: #888888;
        font-size: 12px;
        padding: 20px 0 10px 0;
        font-family: system-ui, -apple-system, sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Header Ringkas: Logo Animasi GIF (HTML Render) + Deskripsi
# ---------------------------------------------------------
col_logo, col_desc = st.columns([2, 5])

with col_logo:
    # Menggunakan HTML img agar GIF dipaksa berputar terus di browser
    st.markdown(
        '<img src="app/static/logo_animasi.gif" width="180">', 
        unsafe_allow_html=True
    )
    # ATAU jika file GIF ada di folder utama repositori:
    # st.image("logo_animasi.gif", width=180)

with col_desc:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("✨ **Pengecek Tata Bahasa & Uslub Arab Akademik**")
    st.write("Sempurnakan tata bahasa, imla', dan mufradat karya ilmiah Anda secara otomatis.")
# ---------------------------------------------------------

# 2. Sidebar Pengaturan Mode
st.sidebar.header("⚙️ Pengaturan Mode Analisis")

# MENGAMBIL API KEY DARI SECRETS STREAMLIT / ENV AUTOMATIS
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

# Opsi Cadangan Manual di Sidebar (Hanya tampil jika Secrets Streamlit tidak terdeteksi)
if not api_key:
    api_key = st.sidebar.text_input("Masukkan Gemini API Key Anda:", type="password")

uslub_mode = st.sidebar.radio(
    "Pilih Mode Uslub (Gaya Bahasa):",
    ("Uslub 'Ilmi (Akademik & Ilmiah)", "Uslub 'Adabi (Sastra / Puitis) [Tahap Pengembangan]"),
    index=0
)

enable_tashkil = st.sidebar.checkbox("Gunakan Harakat Lengkap (التشكيل)", value=True)

# 3. System Prompt Super Kritis + Validasi Uslub Akademik
SYSTEM_PROMPT = """
Kamu adalah Uslubly, pakar & penyunting Bahasa Arab Akademik tingkat tinggi yang dirancang dan dikurasi oleh Ahmad Zakaria.
Tugas Kamu: Menganalisis teks Arab masukan secara SANGAT KRITIS, MENYELURUH, dan DETAIL (meliputi Nahwu, Shorof, Imla', Pilihan Kata/Mufradat, dan Uslub Akademik 'Ilmi).

Lakukan koreksi mendalam terhadap:
1. Kesalahan Nahwu & Shorof (I'rab, Harakat, Dhomir).
2. Kesalahan Imla' (Hamzah, Ta' Marbuthah, Alif Maqshurah).
3. Pemilihan Kata & Uslub 'Ilmi: Ganti kata-kata biasa/pasaran dengan mufradat akademik yang fashih dan baku.
4. Struktur Kalimat: Perbaiki susunan klausa agar mengalir secara ilmiah.

Format JSON WAJIB:
{
  "corrected_plain_text": "Teks Arab hasil penyuntingan sempurna dengan harakat lengkap",
  "errors": [
    {
      "id": "ERR_1",
      "original_word": "kata_atau_frasa_satu_dua_kata_yang_diubah",
      "corrected_word": "kata_atau_frasa_hasil_perbaikan_yang_persis_ada_di_corrected_plain_text",
      "category": "Imla' / Nahwu / Shorof / Uslub 'Ilmi",
      "reason_id": "Alasan perbaikan akademis yang detail dalam Bahasa Indonesia"
    }
  ]
}

Aturan Penting:
1. Analisislah secara KRITIS dan DETEKSI SEMUA ketidaksempurnaan uslub/tata bahasa.
2. Nilai 'corrected_word' HARUS MERUPAKAN STRINGS SAMA PERSIS dengan potongan teks pada 'corrected_plain_text' (termasuk harakatnya) agar highlight terpasang sempurna.
3. Khusus untuk kategori "Uslub 'Ilmi", pada bagian 'reason_id', Kamu WAJIB menyertakan:
   - Alasan mengapa frasa asli kurang baku/akademis.
   - Contoh penggunaannya dalam literatur/jurnal ilmiah Arab baku sebagai patokan validasi.
"""

# 4. Form Input
user_text = st.text_area("Masukkan Teks Bahasa Arab Akademik di Sini:", height=160, placeholder="اكتب النص العربي هنا...")

# 5. Eksekusi Analisis
if st.button("🔍 Menganalisis Teks"):
    if not api_key:
        st.error("⚠️ API Key belum dikonfigurasi di Streamlit Secrets. Masukkan API Key di sidebar atau di pengaturannya!")
    elif not user_text.strip():
        st.warning("⚠️ Masukkan teks Arab terlebih dahulu.")
    elif "Tahap Pengembangan" in uslub_mode:
        st.info("ℹ️ Mode Uslub 'Adabi saat ini sedang dalam tahap pengembangan. Silakan gunakan mode **Uslub 'Ilmi (Akademik & Ilmiah)**.")
    else:
        with st.spinner("Uslubly sedang menganalisis & menyempurnakan uslub teks Arab..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt_input = f"Gunakan Harakat Lengkap: {enable_tashkil}\nTeks Asli:\n{user_text}"
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt_input,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.0
                    )
                )
                
                result = json.loads(response.text)
                plain_corrected = result.get("corrected_plain_text", "")
                errors = result.get("errors", [])

                # Penyusunan HTML Interaktif
                annotated_html = plain_corrected

                for err in errors:
                    corr_word = err.get("corrected_word", "").strip()
                    orig_word = err.get("original_word", "").strip()
                    cat = err.get("category", "Nahwu")
                    reason = err.get("reason_id", "")

                    if corr_word and corr_word in annotated_html:
                        tooltip_html = f'<span class="corrected-tooltip">{corr_word}<span class="tooltip-content"><span class="badge-cat">{cat}</span><br><strong>Kata Asal:</strong> <span style="color:#c62828; text-decoration:line-through;">{orig_word}</span><br><strong>Diubah Menjadi:</strong> <span style="color:#2e7d32; font-weight:bold;">{corr_word}</span><br><hr style="margin:6px 0; border:0.5px solid #e0e0e0;">💡 <strong>Alasan Perbaikan:</strong><br>{reason}</span></span>'
                        annotated_html = annotated_html.replace(corr_word, tooltip_html, 1)

                annotated_html = html.unescape(annotated_html)

                # Hasil Tampilan Interaktif
                st.subheader("✨ Hasil Analisis Perbaikan Edukatif :")
                st.caption("Arahkan kursor atau sentuh kata bergaris bawah hijau untuk melihat alasan perbaikan.")
                st.markdown(f'<div class="arabic-interactive-container" dir="rtl">{annotated_html}</div>', unsafe_allow_html=True)
                
                st.divider()
                
                # Hasil Teks Polos untuk Disalin
                st.subheader("📋 Salin Teks Perbaikan Polos:")
                st.text_area(
                    "Teks Polos", 
                    value=plain_corrected, 
                    height=120, 
                    label_visibility="collapsed"
                )

            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses data: {e}")

# 6. Credit Line Footer
st.markdown("---")
st.markdown('<div class="app-footer">© 2026 Uslubly • Ahmad Zakaria</div>', unsafe_allow_html=True)