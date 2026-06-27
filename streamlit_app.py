import os
import re
import json
import tempfile

import streamlit as st
import requests
from PIL import Image
import io

from receipt_parser import format_receipt_items

# FastAPI 서버 URL 설정 (로컬 기본값, Render에서는 환경 변수로 주입)
def normalize_fastapi_url(url: str) -> str:
    if not url:
        return "http://localhost:8002"
    if not url.startswith("http"):
        url = f"https://{url}"
    hostname = url.split("://", 1)[1].split("/")[0]
    if "." not in hostname:
        url = f"https://{hostname}.onrender.com"
    return url.rstrip("/")


FASTAPI_URL = normalize_fastapi_url(os.getenv("FASTAPI_URL", "http://localhost:8002"))

HF_OCR_URL = os.getenv("HF_OCR_URL", "")


def get_hf_space_id(url: str) -> str:
    if "/spaces/" in url:
        return url.rstrip("/").split("/spaces/")[-1]
    return url.strip("/")


@st.cache_resource
def get_hf_ocr_client(space_id: str):
    from gradio_client import Client

    hf_token = os.getenv("HF_TOKEN") or None
    return Client(space_id, hf_token=hf_token)


def run_ocr_via_hf_space(image_file, space_url: str, receipt_mode: bool = False) -> dict:
    from gradio_client import handle_file

    space_id = get_hf_space_id(space_url)
    client = get_hf_ocr_client(space_id)

    suffix = os.path.splitext(image_file.name)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_file.getvalue())
        tmp_path = tmp.name

    predict_result = client.predict(
        handle_file(tmp_path),
        receipt_mode,
        api_name="/predict",
    )

    if len(predict_result) == 3:
        full_text, details, receipt_output = predict_result
    else:
        full_text, details = predict_result
        receipt_output = ""

    detections = [
        line for line in details.splitlines()
        if line.strip() and re.match(r"^\d+\.", line.strip())
    ]

    receipt_items = []
    receipt_text = ""
    if receipt_mode:
        if receipt_output.strip().startswith("["):
            try:
                receipt_items = json.loads(receipt_output)
                receipt_text = format_receipt_items(receipt_items)
            except json.JSONDecodeError:
                receipt_text = receipt_output
        else:
            receipt_text = receipt_output

    return {
        "success": True,
        "filename": image_file.name,
        "extracted_text": full_text,
        "detailed_results": [{"text": line} for line in detections],
        "total_detections": len(detections),
        "details_text": details,
        "receipt_items": receipt_items,
        "receipt_text": receipt_text,
        "source": "huggingface",
    }

# 페이지 설정
st.set_page_config(
    page_title="PDF & OCR 웹앱",
    layout="wide"
)

# 제목
st.title("📄 PDF 파싱 & 이미지 OCR 웹앱")
st.markdown("---")

# ==================== PDF 파싱 섹션 ====================
st.header("1️⃣ PDF 파싱 (PyPDF2)")

# 1:2 비율로 컬럼 생성
pdf_col1, pdf_col2 = st.columns([1, 2])

with pdf_col1:
    st.subheader("📤 PDF 파일 업로드")
    
    # PDF 파일 업로더
    pdf_file = st.file_uploader(
        "PDF 파일을 선택하세요",
        type=['pdf'],
        key="pdf_uploader"
    )
    
    if pdf_file is not None:
        st.success(f"✅ 파일 선택됨: {pdf_file.name}")
        st.info(f"파일 크기: {pdf_file.size / 1024:.2f} KB")
        
        # 파싱 버튼
        if st.button("📋 PDF 파싱 시작", key="parse_pdf_btn", use_container_width=True):
            
            with st.spinner("PDF 파싱 중..."):
                # FastAPI로 파일 전송
                files = {
                    "file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")
                }
                ########################################
                ### 필수과제 1-(1): streamlit -> fastapi로 사용자가 업로드한 pdf 파일 파싱 요청
                response = requests.post(f"{FASTAPI_URL}/parse-pdf", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    # 세션 스테이트에 저장
                    st.session_state.pdf_result = result
                    st.success("✅ PDF 파싱 완료!")
                else:
                    st.error(f"❌ 오류 발생: {response.json().get('detail', '알 수 없는 오류')}")
                ########################################

with pdf_col2:
    st.subheader("📝 추출된 텍스트")
    
    # 세션 스테이트에 저장된 결과 표시
    if 'pdf_result' in st.session_state:
        result = st.session_state.pdf_result
        
        # 정보 표시
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("총 페이지 수", result['total_pages'])
        with col_b:
            st.metric("추출된 문자 수", result['text_length'])
        with col_c:
            st.metric("파일명", result['filename'][:20] + "..." if len(result['filename']) > 20 else result['filename'])
        
        st.markdown("---")
        
        # 탭으로 전체 텍스트와 페이지별 보기 구분
        tab1, tab2 = st.tabs(["📄 전체 텍스트", "📑 페이지별 보기"])
        
        with tab1:
            # 전체 텍스트 표시
            st.text_area(
                "추출된 전체 텍스트",
                value=result['extracted_text'],
                height=400,
                key="pdf_full_text"
            )
        
        with tab2:
            ########################################
            ### 필수과제 1-(3): 페이지별 텍스트 표시
            for page_info in result['pages']:
                with st.expander(f"페이지 {page_info['page_number']}", expanded=(page_info['page_number'] == 1)):
                    st.text_area(
                        f"Page {page_info['page_number']} 내용",
                        value=page_info['text'],
                        height=200,
                        key=f"pdf_page_{page_info['page_number']}"
                    )
            
            ########################################
    else:
        st.info("👈 왼쪽에서 PDF 파일을 업로드하고 파싱을 시작하세요.")

st.markdown("---")
st.markdown("")

# ==================== 이미지 OCR 섹션 ====================
st.header("2️⃣ 이미지 OCR (EasyOCR)")

if HF_OCR_URL:
    st.info(
        f"OCR은 Render API 대신 **Hugging Face Space**에 직접 연결합니다. "
        f"Space: [{get_hf_space_id(HF_OCR_URL)}]({HF_OCR_URL})"
    )

# 1:2 비율로 컬럼 생성
ocr_col1, ocr_col2 = st.columns([1, 2])

with ocr_col1:
    st.subheader("📤 이미지 파일 업로드")
    
    # 이미지 파일 업로더
    image_file = st.file_uploader(
        "이미지 파일을 선택하세요",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp'],
        key="image_uploader"
    )
    
    if image_file is not None:
        # 이미지 미리보기
        image = Image.open(image_file)
        st.image(image, caption=f"업로드된 이미지: {image_file.name}", use_column_width=True)
        
        st.success(f"✅ 파일 선택됨: {image_file.name}")
        st.info(f"파일 크기: {image_file.size / 1024:.2f} KB")

        receipt_mode = st.checkbox(
            "🧾 영수증에서 상품명·금액만 추출",
            value=False,
            key="receipt_mode",
        )
        
        # OCR 버튼
        if st.button("🔍 이미지 OCR 시작", key="ocr_image_btn", use_container_width=True):
            with st.spinner(
                "Hugging Face Space에서 OCR 처리 중..."
                if HF_OCR_URL
                else "이미지 OCR 처리 중... (처음 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다)"
            ):
                image_file.seek(0)

                ########################################
                ### 필수과제 2-(1): streamlit -> fastapi로 사용자가 업로드한 이미지 파일 파싱 요청
                try:
                    if HF_OCR_URL:
                        result = run_ocr_via_hf_space(image_file, HF_OCR_URL, receipt_mode)
                    else:
                        files = {
                            "file": (image_file.name, image_file.getvalue(), f"image/{image_file.type}")
                        }
                        response = requests.post(f"{FASTAPI_URL}/ocr-image", files=files)

                        if response.status_code == 200:
                            result = response.json()
                        elif response.status_code == 503:
                            st.warning(response.json().get("detail", "OCR은 Hugging Face Space에서 이용하세요."))
                            result = None
                        else:
                            st.error(f"❌ 오류 발생: {response.json().get('detail', '알 수 없는 오류')}")
                            result = None

                    if result:
                        st.session_state.ocr_result = result
                        st.success("✅ OCR 처리 완료!")
                except Exception as exc:
                    st.error(f"❌ OCR 연동 오류: {exc}")
                ########################################

with ocr_col2:
    st.subheader("📝 추출된 텍스트")
    
    # 세션 스테이트에 저장된 결과 표시
    if 'ocr_result' in st.session_state:
        result = st.session_state.ocr_result
        
        # 정보 표시
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("감지된 텍스트 수", result['total_detections'])
        with col_b:
            st.metric("파일명", result['filename'][:30] + "..." if len(result['filename']) > 30 else result['filename'])
        
        if result.get("receipt_items"):
            st.markdown("**🧾 상품명 · 금액**")
            st.dataframe(result["receipt_items"], use_container_width=True)
        elif result.get("receipt_text"):
            st.text_area(
                "상품명 · 금액",
                value=result["receipt_text"],
                height=180,
                key="ocr_receipt_text",
            )

        with st.expander("전체 OCR 텍스트 보기"):
            st.text_area(
                "추출된 전체 텍스트",
                value=result['extracted_text'],
                height=200,
                key="ocr_full_text"
            )

            if result.get("details_text"):
                st.text_area(
                    "상세 결과 (신뢰도)",
                    value=result["details_text"],
                    height=160,
                    key="ocr_details_text",
                )
    else:
        st.info("👈 왼쪽에서 이미지 파일을 업로드하고 OCR을 시작하세요.")

