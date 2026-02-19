import os

path = os.path.join('backend', 'app', 'providers', 'ollama_provider.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''                else:
                    try:
                        text_parts.append(
                            f"--- File: {f.filename} ---\\n"
                            f"{f.content.decode('utf-8')}\\n"
                            f"--- End: {f.filename} ---"
                        )
                    except UnicodeDecodeError:
                        text_parts.append(f"[Binary file: {f.filename}]")'''

new = '''                else:
                    extracted = None
                    # Try PDF text extraction first
                    if f.filename.lower().endswith(".pdf"):
                        extracted = self._extract_pdf_text(f.content, f.filename)
                    # Try docx extraction
                    elif f.filename.lower().endswith(".docx"):
                        extracted = self._extract_docx_text(f.content, f.filename)
                    if extracted:
                        text_parts.append(extracted)
                    else:
                        try:
                            text_parts.append(
                                f"--- File: {f.filename} ---\\n"
                                f"{f.content.decode('utf-8')}\\n"
                                f"--- End: {f.filename} ---"
                            )
                        except UnicodeDecodeError:
                            text_parts.append(f"[Binary file: {f.filename}, could not extract text]")'''

if old in content:
    content = content.replace(old, new)
else:
    print("ERROR: Could not find file handling block")
    exit(1)

# Add helper methods before the register line
old2 = '''ProviderRegistry.register("ollama", OllamaProvider)'''

new2 = '''    @staticmethod
    def _extract_pdf_text(content: bytes, filename: str) -> str | None:
        """Extract text from PDF bytes using pdfplumber or PyPDF2."""
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages.append(f"[Page {i+1}]\\n{text}")
                if pages:
                    return f"--- File: {filename} ---\\n" + "\\n\\n".join(pages) + f"\\n--- End: {filename} ---"
        except ImportError:
            pass
        except Exception:
            pass
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages.append(f"[Page {i+1}]\\n{text}")
            if pages:
                return f"--- File: {filename} ---\\n" + "\\n\\n".join(pages) + f"\\n--- End: {filename} ---"
        except ImportError:
            pass
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_docx_text(content: bytes, filename: str) -> str | None:
        """Extract text from DOCX bytes."""
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            if paragraphs:
                return f"--- File: {filename} ---\\n" + "\\n".join(paragraphs) + f"\\n--- End: {filename} ---"
        except ImportError:
            pass
        except Exception:
            pass
        return None


ProviderRegistry.register("ollama", OllamaProvider)'''

if old2 in content:
    content = content.replace(old2, new2)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK: PDF/DOCX extraction added to OllamaProvider")
else:
    print("ERROR: Could not find register line")
