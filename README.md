# AI 과학기술-경제 인사이트 분석기

PDF 또는 DOCX 문서를 업로드하면 AI가 자동으로 분석하여 다음 결과를 제공합니다:

1. **중요 문장 10개** 추출
2. **과학기술 핵심 요약** (5~7문장)
3. **핵심 키워드 10개** 추출
4. **경제적 시사점 5가지** (산업적 파급효과, 시장 성장 가능성, 투자 리스크, 정책적 시사점, 글로벌 경쟁 구도)

## 프로젝트 구조

```
ai-insight-report/
├── main.py                  # FastAPI 메인 앱 (문서 분석)
├── services/
│   ├── __init__.py
│   ├── extractor.py         # PDF/DOCX 텍스트 추출 모듈
│   └── analyzer.py          # AI 분석 모듈 (OpenAI / Claude)
├── templates/
│   └── upload.html          # 업로드 및 결과 페이지
├── static/
│   └── app.css              # 스타일시트
├── uploads/                 # 임시 업로드 디렉토리 (자동 생성)
├── .env.example             # 환경변수 템플릿
├── requirements.txt         # Python 의존성
└── README.md                # 이 파일
```

## 실행 방법

### 1. Python 설치 확인

Python 3.10 이상이 필요합니다.

```bash
python --version
```

### 2. 의존성 설치

```bash
cd ai-insight-report
pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
# .env.example을 .env로 복사
copy .env.example .env
```

`.env` 파일을 열어 API 키를 설정합니다:

```env
# OpenAI를 사용할 경우
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here

# Claude를 사용할 경우
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### 4. 서버 실행

```bash
python main.py
```

### 5. 웹 브라우저에서 접속

```
http://localhost:8000
```

## 사용법

1. 웹 페이지에서 PDF 또는 DOCX 파일을 업로드합니다.
2. "분석 시작" 버튼을 클릭합니다.
3. AI 분석이 완료되면 (약 1~2분) 결과가 화면에 표시됩니다.

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 메인 페이지 (업로드 폼) |
| POST | `/analyze` | 파일 분석 (HTML 응답) |
| POST | `/api/analyze` | 파일 분석 (JSON 응답) |

### API 호출 예시 (curl)

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@report.pdf"
```

## 기술 스택

- **백엔드**: FastAPI + Uvicorn
- **프론트엔드**: HTML + CSS (Jinja2 템플릿)
- **텍스트 추출**: PyPDF2 (PDF), python-docx (DOCX)
- **AI 분석**: OpenAI GPT-4o-mini 또는 Anthropic Claude

## 기존 앱 (web_app.py)

기존 Flask 기반 주간 리포트 뷰어는 별도로 유지됩니다:

```bash
python web_app.py  # http://localhost:5000
```
