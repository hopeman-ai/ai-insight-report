"""
1월 6일 날짜로 표시되는 리포트 생성 스크립트
(현재 데이터 사용, 파일명과 리포트 제목만 1월 6일로 표시)
"""
from datetime import datetime, timedelta
from main import main
import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from collector import NaverBlogCollector
from analyzer import PostAnalyzer
from report_generator import ReportGenerator
import yaml
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


if __name__ == "__main__":
    # 1월 6일을 리포트 날짜로 사용 (파일명용)
    report_date = datetime(2026, 1, 6)

    print(f"\n{'='*60}")
    print(f"1월 6일 리포트 생성")
    print(f"리포트 날짜: {report_date.strftime('%Y년 %m월 %d일')}")
    print(f"데이터: 현재 수집 가능한 최신 포스트 사용")
    print(f"{'='*60}\n")

    try:
        # 설정 로드
        config = load_config()

        # 1. 포스트 수집 (현재 기준)
        logger.info("Step 1/4: 블로그 포스트 수집")
        collector = NaverBlogCollector(config)
        posts = collector.collect_posts()  # reference_date 없이 현재 데이터 수집

        if not posts:
            logger.warning("수집된 포스트가 없습니다.")
            sys.exit(1)

        logger.info(f"✓ {len(posts)}개 포스트 수집 완료")

        # 2. AI 분석
        logger.info("\nStep 2/4: 키워드 기반 분석")
        analyzer = PostAnalyzer(config)
        analyzed_posts = analyzer.analyze_posts(posts)
        categorized_posts = analyzer.categorize_posts(analyzed_posts)
        logger.info(f"✓ {len(analyzed_posts)}개 포스트 분석 완료")

        # 3. 리포트 생성 (1월 6일 날짜로)
        logger.info("\nStep 3/4: Markdown 리포트 생성 (1월 6일 기준)")
        generator = ReportGenerator(config)
        report_path = generator.generate_report(categorized_posts, report_date)
        logger.info(f"✓ 리포트 생성 완료: {report_path}")

        logger.info("\n" + "="*60)
        logger.info("1월 6일 리포트 생성 완료!")
        logger.info("="*60)
        logger.info(f"\n📊 결과:")
        logger.info(f"  - 포스트 수: {len(posts)}개")
        logger.info(f"  - 카테고리 수: {len(categorized_posts)}개")
        logger.info(f"  - 리포트 파일: {os.path.abspath(report_path)}")

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)
