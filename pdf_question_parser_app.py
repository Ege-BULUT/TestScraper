# pdf_question_parser_app.py
import fitz  # PyMuPDF
import io
import base64
import pandas as pd
from PIL import Image
import streamlit as st
from pdfminer.high_level import extract_text
from streamlit_paste_button import paste_image_button

st.set_page_config(page_title="PDF Soru Tablosu", layout="wide")
st.title("\U0001F4D8 Limits PDF'ten Soru Tablosu Oluştur")

if 'question_data' not in st.session_state:
    st.session_state.question_data = []

uploaded_file = st.file_uploader("\U0001F4C4 PDF dosyasını yükle", type=["pdf"])

if uploaded_file:
    uploaded_file.seek(0)
    text = extract_text(uploaded_file)

    def get_questions(start, end, level):
        lines = text[start:end].splitlines()
        return [
            {
                "Module": "AP®",
                "Lesson": "Maths",
                "Topic": "Limits",
                "Image": st.session_state.question_data[i]["Image"] if i < len(st.session_state.question_data) else "",
                "Answer": line.strip().split()[-1] if line.strip() else "",
                "Answer Description": st.session_state.question_data[i]["Answer Description"] if i < len(st.session_state.question_data) else "",
                "Level": level
            }
            for i, line in enumerate(lines) if line.strip().endswith(('A', 'B', 'C', 'D'))
        ]

    # Sıralı başlık aralıklarına göre tüm soruları topla
    sections = [
        ("Easy Questions", "Easy"),
        ("Medium Questions", "Medium"),
        ("Hard Questions", "Hard"),
        ("Very Hard Questions", "Very Hard")
    ]

    section_indices = [(text.find(title), level) for title, level in sections if text.find(title) != -1]
    section_indices.sort()
    section_indices.append((len(text), None))  # Metin sonu

    combined_data = []
    for i in range(len(section_indices) - 1):
        start_idx, level = section_indices[i]
        end_idx, _ = section_indices[i + 1]
        combined_data += get_questions(start_idx, end_idx, level)

    st.session_state.question_data = combined_data

if st.session_state.question_data:
    st.markdown("### \U0001F4C8 Excel Önizleme")
    placeholder = st.empty()

    st.markdown("### ✏️ Sorular ve Görsel Ekle")

    for i, q in enumerate(st.session_state.question_data):
        with st.expander(f"**Soru {i + 1}**", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Module:** {q['Module']}")
                st.write(f"**Lesson:** {q['Lesson']}")
                st.write(f"**Topic:** {q['Topic']}")
                st.write(f"**Answer:** {q['Answer']}")
                st.write(f"**Level:** {q['Level']}")

            with col2:
                pasted_img = paste_image_button(label="\U0001F4CB Soru Görseli", key=f"qimg_{i}")
                if pasted_img and pasted_img.image_data:
                    buf = io.BytesIO()
                    pasted_img.image_data.save(buf, format="PNG")
                    img_bytes = buf.getvalue()
                    st.session_state.question_data[i]["Image"] = base64.b64encode(img_bytes).decode("utf-8")
                    st.image(img_bytes, caption="Soru Görseli", width=80)

                pasted_desc = paste_image_button(label="\U0001F4CB Cevap Açıklaması Görseli", key=f"adesc_{i}")
                if pasted_desc and pasted_desc.image_data:
                    buf2 = io.BytesIO()
                    pasted_desc.image_data.save(buf2, format="PNG")
                    desc_bytes = buf2.getvalue()
                    st.session_state.question_data[i]["Answer Description"] = base64.b64encode(desc_bytes).decode("utf-8")
                    st.image(desc_bytes, caption="Cevap Açıklaması Görseli", width=80)

    df_preview = pd.DataFrame(st.session_state.question_data)
    placeholder.dataframe(df_preview, use_container_width=True)

    if st.button("\U0001F4E5 Excel çıktısını indir"):
        df = pd.DataFrame(st.session_state.question_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        st.download_button(
            label="İndir",
            data=output.getvalue(),
            file_name="soru_tablosu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )