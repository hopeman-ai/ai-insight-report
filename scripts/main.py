"""
AI 인사이트 리포트 생성 메인 스크립트
"""
import os
import sys
import yaml
import logging
from datetime import datetime

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from collector import NaverBlogCollector
from analyzer import PostAnalyzer
from report_generator import ReportGenerator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'insight_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    """설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def main(reference_date=None):
    """메인 실행 함수

    Args:
        reference_date: 기준 날짜 (datetime 객체). None이면 현재 날짜 사용
    """
    logger.info("="*60)
    logger.info("AI 인사이트 리포트 생성 시작")
    logger.info("="*60)

    try:
        # 1. 설정 로드
        logger.info("Step 1/4: 설정 파일 로드")
        config = load_config()
        logger.info(f"대상 블로그: {config['blog']['name']}")
        logger.info(f"수집 기준: 최근 {config['collection']['days_lookback']}일, 최대 {config['collection']['max_posts']}개 포스트")
        if reference_date:
            logger.info(f"기준 날짜: {reference_date.strftime('%Y-%m-%d')}")

        # 2. 포스트 수집
        logger.info("\nStep 2/4: 블로그 포스트 수집")
        collector = NaverBlogCollector(config)
        posts = collector.collect_posts(reference_date)

        if not posts:
            logger.warning("수집된 포스트가 없습니다. 프로그램을 종료합니다.")
            return

        logger.info(f"✓ {len(posts)}개 포스트 수집 완료")

        # 3. AI 분석 (분류 + 요약)
        logger.info("\nStep 3/4: 키워드 기반 분석 (주제 분류 및 요약)")
        analyzer = PostAnalyzer(config)
        analyzed_posts = analyzer.analyze_posts(posts)
        categorized_posts = analyzer.categorize_posts(analyzed_posts)
        logger.info(f"✓ {len(analyzed_posts)}개 포스트 분석 완료")
        logger.info(f"✓ {len(categorized_posts)}개 카테고리로 분류")

        # 4. 리포트 생성
        logger.info("\nStep 4/4: Markdown 리포트 생성")
        generator = ReportGenerator(config)
        report_path = generator.generate_report(categorized_posts, reference_date)
        logger.info(f"✓ 리포트 생성 완료: {report_path}")

        # 완료 메시지
        logger.info("\n" + "="*60)
        logger.info("모든 작업이 성공적으로 완료되었습니다!")
        logger.info("="*60)
        logger.info(f"\n📊 결과 요약:")
        logger.info(f"  - 수집된 포스트: {len(posts)}개")
        logger.info(f"  - 분석된 포스트: {len(analyzed_posts)}개")
        logger.info(f"  - 카테고리 수: {len(categorized_posts)}개")
        logger.info(f"  - 리포트 파일: {os.path.abspath(report_path)}")

        # 카테고리별 통계
        logger.info(f"\n📈 카테고리별 분포:")
        for category, posts_list in sorted(categorized_posts.items()):
            logger.info(f"  - {category}: {len(posts_list)}개")

        logger.info(f"\n✨ 생성된 리포트를 확인하세요: {os.path.abspath(report_path)}")

    except KeyboardInterrupt:
        logger.info("\n\n사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
