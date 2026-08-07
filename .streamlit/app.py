import base64
import html
import json
import os

import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# 1. Pengaturan Halaman & Favicon (WAJIB HANYA 1 KALI & PALING ATAS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Uslubly - Pengecek Teks Arab Akademik",
    page_icon="logo.webp",  # Favicon ikon tab browser
    layout="wide",
)

# ---------------------------------------------------------
# 1.5. Cek Parameter URL Rahasia (Sembunyikan Menu GitHub)
# ---------------------------------------------------------
query_params = st.query_params
is_admin = query_params.get("admin") == "true"

if not is_admin:
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {
            display: none !important;
        }
        #MainMenu {
            visibility: hidden !important;
        }
        footer {
            visibility: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# 2. CSS Kustom Utuh (Sudah Diperbaiki)
# ---------------------------------------------------------
st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)


# Function untuk membaca GIF lokal menjadi Base64
def get_base64_gif(gif_path):
    with open(gif_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


# ---------------------------------------------------------
# Header Utama: Logo GIF Tengah Atas & Hirarki Teks
# ---------------------------------------------------------
try:
    gif_base64 = get_base64_gif("logo_animasi.gif")
    logo_html = f'<img src="data:image/gif;base64,{gif_base64}" width="300" style="display: block; margin: 0 auto;">'
except Exception:
    logo_html = '<h1 style="text-align: center; color: #2e7d32;">Uslubly</h1>'

st.markdown(
    f"""
    <div style="text-align: center; padding-bottom: 10px;">
        {logo_html}
        <h3 style="margin-top: 15px; margin-bottom: 5px; color: #1b5e20; font-weight: 700; font-size: 22px;">
            ✨ Pengecek Tata Bahasa & Uslub Arab Akademik
        </h3>
        <p style="color: #666666; font-size: 15px; margin-top: 0;">
            Sempurnakan tata bahasa, imla', dan mufradat karya ilmiah Anda secara otomatis.
        </p>
    </div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Sidebar Pengaturan Mode
# ---------------------------------------------------------
st.sidebar.header("⚙️ Pengaturan Mode Analisis")

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input(
        "Masukkan Gemini API Key Anda:", type="password"
    )

uslub_mode = st.sidebar.radio(
    "Pilih Mode Uslub (Gaya Bahasa):",
    (
        "Uslub 'Ilmi (Akademik & Ilmiah)",
        "Uslub 'Adabi (Sastra / Puitis) [Tahap Pengembangan]",
    ),
    index=0,
)

enable_tashkil = st.sidebar.checkbox(
    "Gunakan Harakat Lengkap (التشكيل)", value=True
)

# ---------------------------------------------------------
# System Prompt
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Form Input & Eksekusi
# ---------------------------------------------------------
user_text = st.text_area(
    "Masukkan Teks Bahasa Arab Akademik di Sini:",
    height=160,
    placeholder="اكتب النص العربي هنا...",
)

if st.button("🔍 Menganalisis Teks"):
    if not api_key:
        st.error(
            "⚠️ API Key belum dikonfigurasi di Streamlit Secrets. Masukkan API Key di sidebar atau di pengaturannya!"
        )
    elif not user_text.strip():
        st.warning("⚠️ Masukkan teks Arab terlebih dahulu.")
    elif "Tahap Pengembangan" in uslub_mode:
        st.info(
            "ℹ️ Mode Uslub 'Adabi saat ini sedang dalam tahap pengembangan. Silakan gunakan mode **Uslub 'Ilmi (Akademik & Ilmiah)**."
        )
    else:
        with st.spinner(
            "Uslubly sedang menganalisis & menyempurnakan uslub teks Arab..."
        ):
            try:
                client = genai.Client(api_key=api_key)
                prompt_input = f"Gunakan Harakat Lengkap: {enable_tashkil}\nTeks Asli:\n{user_text}"

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt_input,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.0,
                    ),
                )

                result = json.loads(response.text)
                plain_corrected = result.get("corrected_plain_text", "")
                errors = result.get("errors", [])

                annotated_html = plain_corrected

                for err in errors:
                    corr_word = err.get("corrected_word", "").strip()
                    orig_word = err.get("original_word", "").strip()
                    cat = err.get("category", "Nahwu")
                    reason = err.get("reason_id", "")

                    if corr_word and corr_word in annotated_html:
                        tooltip_html = f'<span class="corrected-tooltip">{corr_word}<span class="tooltip-content"><span class="badge-cat">{cat}</span><br><strong>Kata Asal:</strong> <span style="color:#c62828; text-decoration:line-through;">{orig_word}</span><br><strong>Diubah Menjadi:</strong> <span style="color:#2e7d32; font-weight:bold;">{corr_word}</span><br><hr style="margin:6px 0; border:0.5px solid #e0e0e0;">💡 <strong>Alasan Perbaikan:</strong><br>{reason}</span></span>'
                        annotated_html = annotated_html.replace(
                            corr_word, tooltip_html, 1
                        )

                annotated_html = html.unescape(annotated_html)

                st.subheader("✨ Hasil Analisis Perbaikan Edukatif :")
                st.caption(
                    "Arahkan kursor atau sentuh kata bergaris bawah hijau untuk melihat alasan perbaikan."
                )
                st.markdown(
                    f'<div class="arabic-interactive-container" dir="rtl">{annotated_html}</div>',
                    unsafe_allow_html=True,
                )

                st.divider()

                st.subheader("📋 Salin Teks Perbaikan Polos:")
                st.text_area(
                    "Teks Polos",
                    value=plain_corrected,
                    height=120,
                    label_visibility="collapsed",
                )

            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses data: {e}")

# ---------------------------------------------------------
# Sidebar Kiri: Survei Kepuasan & Kotak Saran (Paling Bawah)
# ---------------------------------------------------------
st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <div style="background-color: #f0f7f4; padding: 10px; border-radius: 8px; border-left: 4px solid #1b5e20;">
        <p style="margin: 0; font-size: 13px; font-weight: bold; color: #1b5e20;">
            ⭐ Survei & Kotak Saran
        </p>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #555555;">
            Bantu kami mengembangkan Uslubly.<br>
            👉 <a href="https://forms.gle/DoAJD4pdNMd1eK9Z8" target="_blank" style="color: #1b5e20; font-weight: bold; text-decoration: underline;">Isi Form di Sini</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 6. Credit Line Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    '<div class="app-footer">© 2026 Uslubly • Ahmad Zakaria • BSA UIN Sunan Kalijaga</div>',
    unsafe_allow_html=True,
)