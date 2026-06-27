import gradio as gr
import numpy as np

reader = None


def get_reader():
    global reader
    if reader is None:
        import easyocr

        reader = easyocr.Reader(["ko", "en"], gpu=False)
    return reader


def run_ocr(image):
    if image is None:
        return "이미지를 업로드해 주세요.", ""

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

    return full_text, details


demo = gr.Interface(
    fn=run_ocr,
    inputs=gr.Image(type="pil", label="이미지 업로드"),
    outputs=[
        gr.Textbox(label="추출된 전체 텍스트", lines=8),
        gr.Textbox(label="상세 결과 (신뢰도)", lines=10),
    ],
    title="EasyOCR 한국어·영어",
    description="한국어·영어 이미지에서 텍스트를 추출합니다.",
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
