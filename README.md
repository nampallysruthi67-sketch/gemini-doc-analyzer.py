# Gemini Document Analyser

Send the whole PDF to a multimodal model — pages, tables, charts and all. No OCR pipeline, no chunking.

**7 of 10** — part of a GenAI project series. FastAPI backend, vanilla JS frontend.

## What it demonstrates

- Native multimodal PDF input: the model sees page layout, not extracted text
- Structured extraction against a schema
- Grounded Q&A that cites page numbers and refuses to guess

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
# add your key to .env  (skip if this project needs no key)
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Keys

| Key | Where to get it | Where it goes |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (free) | `.env` |

## Stack

FastAPI · google-genai (multimodal)

## How it works

Gemini accepts a PDF as raw bytes and renders each page as an image internally — so scanned pages, tables, and charts all work without a separate OCR step. This is the opposite approach to project 08 (RAG): here the whole document goes in the context window. That is simpler and more accurate, and it stops working past a few hundred pages. Knowing which approach to reach for is the actual lesson.

---
MIT
