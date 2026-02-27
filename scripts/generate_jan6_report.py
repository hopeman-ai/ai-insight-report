"""
2026년 1월 6일 기준 리포트 생성 스크립트
"""
from datetime import datetime
from main import main

if __name__ == "__main__":
    # 1월 6일 기준으로 리포트 생성
    reference_date = datetime(2026, 1, 6, 23, 59, 59)

    print(f"\n{'='*60}")
    print(f"1월 6일 기준 리포트 생성")
    print(f"기준 날짜: {reference_date.strftime('%Y년 %m월 %d일')}")
    print(f"수집 범위: 2025년 12월 30일 ~ 2026년 1월 6일")
    print(f"{'='*60}\n")

    main(reference_date)
