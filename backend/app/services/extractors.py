import io
import os
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import tempfile
import subprocess
from typing import Tuple, Dict, Any
from ..utils import save_text_as_file
import openai
import math

# Configure openai externally via environment variable OPENAI_API_KEY
# set OPENAI_API_KEY in your environment or .env file

def extract_text_from_pdf(path: str) -> Dict[str, Any]:
    """
    Try to extract text using pdfplumber. If empty pages detected, fall back to OCR via pdf2image + pytesseract.
    Returns: dict with text, pages, ocr_used, confidences
    """
    full_text = []
    ocr_used = False
    confidences = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    full_text.append(text)
                else:
                    # OCR fallback for this page
                    ocr_used = True
                    # convert page to image and OCR
                    images = convert_from_path(path, first_page=i+1, last_page=i+1)
                    if images:
                        img = images[0]
                        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                        # aggregate text and compute average confidence
                        page_text_parts = []
                        confs = []
                        for j, t in enumerate(ocr_data['text']):
                            if t.strip():
                                page_text_parts.append(t)
                                try:
                                    conf = float(ocr_data['conf'][j])
                                except:
                                    conf = 0.0
                                confs.append(conf)
                        page_text = " ".join(page_text_parts)
                        full_text.append(page_text)
                        if confs:
                            confidences.append(sum(confs)/len(confs))
                        else:
                            confidences.append(0.0)
                    else:
                        full_text.append("")
                        confidences.append(0.0)
    except Exception as e:
        # fallback: try OCR on all pages
        ocr_used = True
        images = convert_from_path(path)
        for img in images:
            text = pytesseract.image_to_string(img)
            full_text.append(text)
    combined = "\n\n".join(full_text).strip()
    return {"text": combined, "ocr_used": ocr_used, "confidences": confidences}

def extract_text_from_image(path: str) -> Dict[str, Any]:
    img = Image.open(path)
    # use image_to_data to get confidences
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    words = []
    confs = []
    for i, w in enumerate(data.get("text", [])):
        if w.strip():
            words.append(w)
            try:
                confs.append(float(data.get("conf", [0]*len(data))[i]))
            except:
                pass
    text = " ".join(words)
    avg_conf = sum(confs)/len(confs) if confs else None
    return {"text": text, "confidence": avg_conf}

def extract_text_from_audio(path: str) -> Dict[str, Any]:
    """
    Uses OpenAI's transcription as default (if API key available).
    Fallback: raise error advising to install whisper / faster_whisper.
    """
    # Try OpenAI speech-to-text
    try:
        import openai, json
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        # uses openai python client (make sure version supports audio.transcribe)
        with open(path, "rb") as audio_file:
            # model "whisper-1" or designated model
            resp = openai.Audio.transcribe("whisper-1", audio_file)
            text = resp.get("text", "")
            return {"text": text, "meta": resp}
    except Exception as e:
        # Fallback: instruct user; raise so upper layer can inform
        raise RuntimeError(
            "Audio transcription via OpenAI failed or OPENAI_API_KEY not set. "
            "Install and use whisper/faster_whisper, or set OPENAI_API_KEY."
            f" (Inner error: {e})"
        )

def extract_text_from_text_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            t = f.read()
        return {"text": t}
    except Exception as e:
        return {"text": ""}
