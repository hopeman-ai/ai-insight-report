"""
AI 기반 문서 분석 모듈

OpenAI 또는 Anthropic Claude API를 사용하여 다음을 수행한다:
1) 중요 문장 10개 추출
2) 과학기술 핵심 요약 (5~7문장)
3) 핵심 키워드 10개 추출
4) 경제적 시사점 5가지 생성
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# ── 환경변수 로드 ──
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _call_openai(prompt: str) -> str:
    """
    OpenAI API를 호출하여 응답 텍스트를 반환한다.
    """
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "당신은 과학기술 및 경제 분석 전문가입니다. 한국어로 답변하세요.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    return response.choices[0].message.content


def _call_claude(prompt: str) -> str:
    """
    Anthropic Claude API를 호출하여 응답 텍스트를 반환한다.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
        system="당신은 과학기술 및 경제 분석 전문가입니다. 한국어로 답변하세요.",
    )

    return response.content[0].text


def _call_ai(prompt: str) -> str:
    """
    설정된 AI 프로바이더에 따라 적절한 API를 호출한다.
    """
    if AI_PROVIDER == "claude":
        return _call_claude(prompt)
    else:
        return _call_openai(prompt)


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    """
    텍스트가 너무 길면 잘라낸다.
    API 토큰 제한을 방지하기 위한 안전장치.
    """
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n... (이하 생략)"
    return text


def extract_key_sentences(text: str) -> list[str]:
    """
    문서에서 중요 문장 10개를 추출한다.

    Args:
        text: 원본 문서 텍스트

    Returns:
        중요 문장 10개 리스트
    """
    prompt = f"""다음 문서에서 가장 중요한 문장 10개를 추출하세요.

규칙:
- 원문 그대로 추출 (의역 금지)
- 핵심 정보가 담긴 문장 위주
- 번호 없이 한 줄에 하나씩 출력
- JSON 배열 형식으로 출력: ["문장1", "문장2", ...]

문서:
{_truncate_text(text)}"""

    result = _call_ai(prompt)
    return _parse_json_list(result)


def generate_summary(text: str) -> str:
    """
    과학기술 핵심 요약을 생성한다 (5~7문장).

    Args:
        text: 원본 문서 텍스트

    Returns:
        요약 문자열
    """
    prompt = f"""다음 과학기술 문서를 5~7문장으로 핵심 요약하세요.

규칙:
- 기술의 핵심 원리와 특징을 포함
- 연구 결과 또는 성과를 반드시 포함
- 간결하고 명확한 문장으로 작성
- 일반인도 이해할 수 있는 수준으로 작성

문서:
{_truncate_text(text)}"""

    return _call_ai(prompt)


def extract_keywords(text: str) -> list[str]:
    """
    핵심 키워드 10개를 추출한다.

    Args:
        text: 원본 문서 텍스트

    Returns:
        키워드 10개 리스트
    """
    prompt = f"""다음 문서에서 핵심 키워드 10개를 추출하세요.

규칙:
- 과학기술 관련 전문 용어 위주
- 단어 또는 짧은 구문 형태
- JSON 배열 형식으로 출력: ["키워드1", "키워드2", ...]

문서:
{_truncate_text(text)}"""

    result = _call_ai(prompt)
    return _parse_json_list(result)


def generate_economic_insights(text: str) -> dict[str, str]:
    """
    경제적 시사점 5가지를 생성한다.

    다음 5개 관점에서 분석:
    1) 산업적 파급효과
    2) 시장 성장 가능성
    3) 투자 리스크
    4) 정책적 시사점
    5) 글로벌 경쟁 구도

    Args:
        text: 원본 문서 텍스트

    Returns:
        {관점: 시사점} 딕셔너리
    """
    prompt = f"""다음 과학기술 리포트를 기반으로
1) 산업적 파급효과
2) 시장 성장 가능성
3) 투자 리스크
4) 정책적 시사점
5) 글로벌 경쟁 구도
관점에서 간결하게 정리하라.

규칙:
- 각 항목을 2~3문장으로 작성
- 구체적인 근거를 문서에서 인용
- JSON 객체 형식으로 출력:
{{"산업적 파급효과": "...", "시장 성장 가능성": "...", "투자 리스크": "...", "정책적 시사점": "...", "글로벌 경쟁 구도": "..."}}

문서:
{_truncate_text(text)}"""

    result = _call_ai(prompt)
    return _parse_json_dict(result)


def _parse_json_list(text: str) -> list[str]:
    """
    AI 응답에서 JSON 배열을 파싱한다.
    코드블록(```)이 포함되어 있어도 처리한다.
    """
    # 코드블록 제거
    cleaned = text.strip()
    if "```" in cleaned:
        # ```json ... ``` 형태 처리
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("["):
                cleaned = part
                break

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass

    # JSON 파싱 실패 시 줄 단위로 분리
    lines = [
        line.strip().lstrip("0123456789.-) ").strip('"')
        for line in text.strip().split("\n")
        if line.strip() and not line.strip().startswith("```")
    ]
    return lines[:10] if lines else ["분석 결과를 파싱할 수 없습니다."]


def _parse_json_dict(text: str) -> dict[str, str]:
    """
    AI 응답에서 JSON 객체를 파싱한다.
    코드블록(```)이 포함되어 있어도 처리한다.
    """
    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                cleaned = part
                break

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        pass

    # JSON 파싱 실패 시 기본 구조 반환
    categories = [
        "산업적 파급효과",
        "시장 성장 가능성",
        "투자 리스크",
        "정책적 시사점",
        "글로벌 경쟁 구도",
    ]
    # 텍스트를 줄 단위로 분리하여 매칭 시도
    result = {}
    lines = text.strip().split("\n")
    for cat in categories:
        for line in lines:
            if cat in line:
                # "카테고리: 내용" 또는 "카테고리 - 내용" 형태
                content = line.split(cat, 1)[-1].strip().lstrip(":- ").strip()
                result[cat] = content
                break
        if cat not in result:
            result[cat] = "분석 결과를 파싱할 수 없습니다."

    return result


def analyze_document(text: str) -> dict:
    """
    문서를 종합 분석한다.

    4단계 분석을 순차적으로 수행:
    1) 중요 문장 추출
    2) 핵심 요약 생성
    3) 키워드 추출
    4) 경제적 시사점 생성

    Args:
        text: 원본 문서 텍스트

    Returns:
        {
            "key_sentences": [...],
            "summary": "...",
            "keywords": [...],
            "economic_insights": {...}
        }
    """
    key_sentences = extract_key_sentences(text)
    summary = generate_summary(text)
    keywords = extract_keywords(text)
    economic_insights = generate_economic_insights(text)

    return {
        "key_sentences": key_sentences,
        "summary": summary,
        "keywords": keywords,
        "economic_insights": economic_insights,
    }
