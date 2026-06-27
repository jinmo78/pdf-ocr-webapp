import io

import easyocr
import numpy as np
import streamlit as st
from PIL import Image


@st.cache_resource
def load_reader():
    return easyocr.Reader(["ko", "en"], gpu=False)


st.set_page_config(page_title="EasyOCR Demo", layout="wide")
st.title("🔍 이미지 OCR (EasyOCR)")
st.markdown("한국어·영어 이미지에서 텍스트를 추출합니다.")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📤 이미지 업로드")
    image_file = st.file_uploader(
        "이미지 파일을 선택하세요",
        type=["jpg", "jpeg", "png", "bmp", "gif", "webp"],
    )

    if image_file is not None:
        image = Image.open(image_file)
        st.image(image, caption=f"업로드: {image_file.name}", use_column_width=True)
        st.info(f"파일 크기: {image_file.size / 1024:.2f} KB")

        if st.button("🔍 OCR 시작", use_container_width=True):
            with st.spinner("OCR 처리 중... (첫 실행 시 모델 로딩으로 시간이 걸릴 수 있습니다)"):
                image_file.seek(0)
                img = Image.open(io.BytesIO(image_file.getvalue()))
                img_array = np.array(img)

                reader = load_reader()
                result_detailed = reader.readtext(img_array)
                result_simple = reader.readtext(img_array, detail=0)

                extracted_data = []
                for bbox, text, confidence in result_detailed:
                    extracted_data.append(
                        {
                            "text": text,
                            "confidence": float(confidence),
                        }
                    )

                st.session_state.ocr_result = {
                    "filename": image_file.name,
                    "extracted_text": " ".join(result_simple),
                    "detailed_results": extracted_data,
                    "total_detections": len(extracted_data),
                }
                st.success("✅ OCR 완료!")

with col2:
    st.subheader("📝 추출된 텍스트")

    if "ocr_result" in st.session_state:
        result = st.session_state.ocr_result

        c1, c2 = st.columns(2)
        with c1:
            st.metric("감지된 텍스트 수", result["total_detections"])
        with c2:
            name = result["filename"]
            st.metric("파일명", name[:30] + "..." if len(name) > 30 else name)

        st.text_area(
            "추출된 전체 텍스트",
            value=result["extracted_text"],
            height=300,
        )

        if result["detailed_results"]:
            st.markdown("**상세 결과 (신뢰도)**")
            for i, item in enumerate(result["detailed_results"], start=1):
                st.write(f"{i}. `{item['text']}` — {item['confidence']:.2%}")
    else:
        st.info("👈 왼쪽에서 이미지를 업로드하고 OCR을 시작하세요.")
