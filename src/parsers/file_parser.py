from pathlib import Path

from pypdf import PdfReader


def _parse_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _parse_image_ocr(file_path: str) -> str:
    import easyocr

    reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
    results = reader.readtext(file_path, detail=False)
    return "\n".join(results)


def parse_file(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path)
    elif suffix == ".txt":
        return _parse_txt(file_path)
    elif suffix in (".docx", ".doc"):
        return _parse_docx(file_path)
    elif suffix in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
        return _parse_image_ocr(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")
