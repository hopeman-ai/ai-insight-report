"""
AI 과학기술-경제 인사이트 분석 웹앱

FastAPI 기반 백엔드
- PDF/DOCX 파일 업로드
- 텍스트 추출 → AI 분석 → 결과 출력
"""

import os
import uuid
import shutil

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services.extractor import extract_text
from services.analyzer import analyze_document

# ── 경로 설정 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── FastAPI 앱 초기화 ──
app = FastAPI(
    title="AI 과학기술-경제 인사이트 분석기",
    description="PDF/DOCX 문서를 업로드하면 AI가 자동으로 분석합니다.",
    version="1.0.0",
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지 (업로드 폼)"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/analyze")
async def analyze(request: Request, file: UploadFile = File(...)):
    """
    파일 업로드 → 텍스트 추출 → AI 분석 → 결과 반환

    지원 형식: .pdf, .docx
    """
    # 1) 파일 확장자 검증
    filename = file.filename or "unknown"
    if not filename.lower().endswith((".pdf", ".docx")):
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": "PDF 또는 DOCX 파일만 업로드할 수 있습니다.",
            },
        )

    # 2) 임시 파일 저장
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 3) 텍스트 추출
        text = extract_text(file_path, filename)

        if not text.strip():
            return templates.TemplateResponse(
                "upload.html",
                {
                    "request": request,
                    "error": "문서에서 텍스트를 추출할 수 없습니다. 이미지 기반 PDF는 지원하지 않습니다.",
                },
            )

        # 4) AI 분석 수행
        result = analyze_document(text)

        # 5) 결과 페이지 렌더링
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "filename": filename,
                "text_preview": text[:500] + ("..." if len(text) > 500 else ""),
                "text_length": len(text),
                "key_sentences": result["key_sentences"],
                "summary": result["summary"],
                "keywords": result["keywords"],
                "economic_insights": result["economic_insights"],
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": str(e)},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": f"분석 중 오류가 발생했습니다: {str(e)}"},
        )
    finally:
        # 임시 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/api/analyze")
async def api_analyze(file: UploadFile = File(...)):
    """
    REST API 엔드포인트 (JSON 응답)
    프론트엔드 외 외부 시스템 연동용
    """
    filename = file.filename or "unknown"
    if not filename.lower().endswith((".pdf", ".docx")):
        return JSONResponse(
            status_code=400,
            content={"error": "PDF 또는 DOCX 파일만 업로드할 수 있습니다."},
        )

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        text = extract_text(file_path, filename)

        if not text.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "문서에서 텍스트를 추출할 수 없습니다."},
            )

        result = analyze_document(text)

        return JSONResponse(content={
            "filename": filename,
            "text_length": len(text),
            "key_sentences": result["key_sentences"],
            "summary": result["summary"],
            "keywords": result["keywords"],
            "economic_insights": result["economic_insights"],
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"분석 중 오류 발생: {str(e)}"},
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  AI 과학기술-경제 인사이트 분석기")
    print("  http://localhost:8000 에서 접속하세요")
    print("=" * 60)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
