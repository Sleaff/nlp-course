from fastapi import FastAPI, File, HTTPException, UploadFile
import os
import logging
from markitdown import MarkItDown
from docling.document_converter import DocumentConverter
import tempfile
import spacy
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# python -m spacy download en_core_web_sm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

logger.info("Initializing AI Models (Docling & spaCy)...")
try:
    converter = DocumentConverter() 
    
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("sentencizer") # Adds rule-based splitting for extra accuracy
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    raise

def run_conversion(temp_path: str):
    """Sync wrapper for Docling to be run in a thread pool."""
    result = converter.convert(temp_path)
    return result.document.export_to_markdown()

def simple_sentence_tokenizer(text: str):
    text = ' '.join(text.split())
    parts = text.split('. ')
    
    sentences = []
    for i, part in enumerate(parts):
        if part.strip():
            if i < len(parts) - 1:
                sentences.append(part + '.')
            else:
                sentences.append(part if part.endswith('.') else part)
    
    return sentences

def sentence_tokenizer(text: str):
    text = ' '.join(text.split())
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences

@app.post("/v1/extract-sentences-marker")
async def send_message_marker(pdf_file: UploadFile = File(...)):
    try:
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info(f"Processing uploaded file: {pdf_file.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await pdf_file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name

            converter = PdfConverter(
                artifact_dict=create_model_dict(),
            )
            rendered = converter(temp_pdf_path)
            text, _, images = text_from_rendered(rendered)
            print(text)

            sentences = sentence_tokenizer(text)
        
            logger.info(f"PDF converted to sentences successfully: {len(sentences)} sentences extracted")
        
            os.unlink(temp_pdf_path)

            return {"sentences": sentences}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Uses Docling and SpaCy
@app.post("/v1/extract-sentences-docling")
async def send_message_docling(pdf_file: UploadFile = File(...)):
    try:
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info(f"Processing uploaded file: {pdf_file.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await pdf_file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name
        
        converter = DocumentConverter()
        doc = converter.convert(temp_pdf_path).document

        text = doc.export_to_markdown()
        logger.info(f"PDF converted to markdown successfully with Docling")
        
        sentences = sentence_tokenizer(text)
        
        logger.info(f"PDF converted to sentences successfully: {len(sentences)} sentences extracted")
        logger.info(f"All sentences extracted: \n{sentences}")

        os.unlink(temp_pdf_path)
        
        return {"sentences": sentences}
    


    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Uses MarkItDown and SpaCy
@app.post("/v1/extract-sentences-markitdown")
async def send_message_markitdown(pdf_file: UploadFile = File(...)):
    try:
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        logger.info(f"Processing uploaded file: {pdf_file.filename}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            content = await pdf_file.read()
            temp_pdf.write(content)
            temp_pdf_path = temp_pdf.name
        
        md = MarkItDown()
        result = md.convert(temp_pdf_path)
        
        text = result.text_content
        sentences = sentence_tokenizer(text)
        
        logger.info(f"PDF converted to sentences successfully: {len(sentences)} sentences extracted")
        logger.info(f"All sentences extracted: \n{sentences}")

        os.unlink(temp_pdf_path)
        
        return {"sentences": sentences}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

