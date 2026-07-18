import os, json, uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

app = FastAPI(title="Gemini Document Analyser")

MAX_MB = 18
DOCS: dict[str, bytes] = {}   # demo-grade store; use S3 or disk for real

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_type": {"type": "string", "description": "invoice, contract, paper, report, …"},
        "title": {"type": "string"},
        "summary": {"type": "string", "description": "3-4 sentences"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                    "page": {"type": "integer"},
                },
                "required": ["label", "value", "page"],
            },
        },
        "dates": {"type": "array", "items": {"type": "string"}},
        "amounts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["doc_type", "title", "summary", "key_points", "entities"],
}


def as_part(pdf: bytes):
    return types.Part.from_bytes(data=pdf, mime_type="application/pdf")


@app.post("/api/analyse")
async def analyse(file: UploadFile = File(...)):
    pdf = await file.read()
    if len(pdf) > MAX_MB * 1024 * 1024:
        raise HTTPException(400, f"PDF is over the {MAX_MB} MB inline limit.")
    if not pdf.startswith(b"%PDF"):
        raise HTTPException(400, "That file is not a PDF.")

    doc_id = str(uuid.uuid4())
    DOCS[doc_id] = pdf

    resp = client.models.generate_content(
        model=MODEL,
        contents=[
            as_part(pdf),
            "Analyse this document. Give the page number where each entity appears. "
            "Extract only what is on the page — do not infer values that are not written.",
        ],
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=SUMMARY_SCHEMA,
        ),
    )
    data = json.loads(resp.text)
    data["doc_id"] = doc_id
    data["size_kb"] = round(len(pdf) / 1024)
    return data


@app.post("/api/ask")
def ask(doc_id: str = Form(...), question: str = Form(...)):
    pdf = DOCS.get(doc_id)
    if not pdf:
        raise HTTPException(404, "Upload a document first.")

    resp = client.models.generate_content(
        model=MODEL,
        contents=[
            as_part(pdf),
            f"Question: {question}\n\n"
            "Answer using only this document. Cite the page number for every claim. "
            "If the document does not contain the answer, say exactly: "
            "'That is not in this document.' Do not use outside knowledge.",
        ],
        config=types.GenerateContentConfig(temperature=0.1),
    )
    return {"answer": resp.text}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
