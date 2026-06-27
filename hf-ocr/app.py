import gradio as gr
import numpy as np

from receipt_parser import format_receipt_items, parse_receipt_items, receipt_items_to_json

reader = None


def get_reader():
    global reader
    if reader is None:
        import easyocr

        reader = easyocr.Reader(["ko", "en"], gpu=False)
    return reader


def run_ocr(image, receipt_mode=False):
    if image is None:
        return "이미지를 업로드해 주세요.", "", "[]"

    img_array = np.array(image)
    ocr = get_reader()
    result_detailed = ocr.readtext(img_array)
    result_simple = ocr.readtext(img_array, detail=0)

    full_text = " ".join(result_simple)
    details = "\n".join(
        f"{i + 1}. {text} — {confidence:.2%}"
        for i, (_, text, confidence) in enumerate(result_detailed)
    )

    if not details:
        details = "텍스트가 감지되지 않았습니다."

    receipt_items = parse_receipt_items(result_detailed) if receipt_mode else []
    receipt_text = format_receipt_items(receipt_items) if receipt_mode else ""
    receipt_json = receipt_items_to_json(receipt_items)

    return full_text, details, receipt_text if receipt_mode else receipt_json


demo = gr.Interface(
    fn=run_ocr,
    inputs=[
        gr.Image(type="pil", label="이미지 업로드"),
        gr.Checkbox(label="영수증에서 상품명·금액만 추출", value=False),
    ],
    outputs=[
        gr.Textbox(label="추출된 전체 텍스트", lines=8),
        gr.Textbox(label="상세 결과 (신뢰도)", lines=10),
        gr.Textbox(label="상품명 · 금액", lines=8),
    ],
    title="EasyOCR 한국어·영어",
    description="한국어·영어 이미지에서 텍스트를 추출합니다. 영수증 모드를 켜면 상품명과 금액만 추출합니다.",
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
