"""
다중 데이터 소스 통합 수집기
"""
import logging
from datetime import datetime
import os
import json

from collector import NaverBlogCollector
from ajunews_collector import AjunewsCollector


class MultiSourceCollector:
    """여러 데이터 소스를 통합 관리하는 수집기"""

    def __init__(self, config):
        self.config = config
        self.data_sources_config = config.get('data_sources', {})
        self.logger = logging.getLogger(__name__)

        # 활성화된 수집기 초기화
        self.collectors = {}
        self._initialize_collectors()

    def _initialize_collectors(self):
        """활성화된 수집기 초기화"""
        # 네이버 블로그
        if self.data_sources_config.get('naver_blog', {}).get('enabled', False):
            try:
                self.collectors['naver_blog'] = NaverBlogCollector(self.config)
                self.logger.info("네이버 블로그 수집기 초기화 완료")
            except Exception as e:
                self.logger.error(f"네이버 블로그 수집기 초기화 실패: {e}")

        # 아주경제 곽재원 칼럼
        if self.data_sources_config.get('ajunews_column', {}).get('enabled', False):
            try:
                self.collectors['ajunews_column'] = AjunewsCollector(self.config)
                self.logger.info("아주경제 칼럼 수집기 초기화 완료")
            except Exception as e:
                self.logger.error(f"아주경제 칼럼 수집기 초기화 실패: {e}")

    def collect_all_sources(self, reference_date=None):
        """모든 활성화된 소스에서 데이터 수집"""
        self.logger.info("=" * 60)
        self.logger.info("다중 소스 데이터 수집 시작")
        self.logger.info("=" * 60)

        all_posts = []
        source_stats = {}

        for source_name, collector in self.collectors.items():
            self.logger.info(f"\n[{source_name}] 수집 시작")
            try:
                posts = collector.collect_posts(reference_date)

                # 소스 정보 추가
                source_config = self.data_sources_config.get(source_name, {})
                source_display_name = source_config.get('name', source_name)

                for post in posts:
                    post['data_source'] = source_name
                    post['source_display_name'] = source_display_name
                    if 'source' not in post:
                        post['source'] = source_display_name

                all_posts.extend(posts)
                source_stats[source_name] = len(posts)

                self.logger.info(f"[{source_name}] {len(posts)}개 수집 완료")

            except Exception as e:
                self.logger.error(f"[{source_name}] 수집 실패: {e}")
                source_stats[source_name] = 0

        # 통합 결과 저장
        self._save_combined_results(all_posts, source_stats, reference_date)

        self.logger.info("=" * 60)
        self.logger.info(f"전체 수집 완료: 총 {len(all_posts)}개")
        for source, count in source_stats.items():
            self.logger.info(f"  - {source}: {count}개")
        self.logger.info("=" * 60)

        return all_posts

    def _save_combined_results(self, all_posts, source_stats, reference_date=None):
        """통합 수집 결과 저장"""
        feeds_dir = self.config.get('storage', {}).get('feeds_dir', 'feeds')
        os.makedirs(feeds_dir, exist_ok=True)

        base_date = reference_date if reference_date else datetime.now()
        timestamp = base_date.strftime('%Y%m%d_%H%M%S')
        filename = f'combined_sources_{timestamp}.json'
        filepath = os.path.join(feeds_dir, filename)

        combined_data = {
            'collected_at': datetime.now().isoformat(),
            'reference_date': reference_date.isoformat() if reference_date else None,
            'total_count': len(all_posts),
            'source_stats': source_stats,
            'sources': list(source_stats.keys()),
            'posts': all_posts
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"통합 데이터 저장: {filepath}")


if __name__ == '__main__':
    # 테스트 실행
    import yaml
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Config 로드
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 통합 수집 실행
    collector = MultiSourceCollector(config)
    posts = collector.collect_all_sources()

    print(f"\n" + "=" * 60)
    print(f"수집 완료 요약")
    print("=" * 60)

    # 소스별 그룹화
    from collections import defaultdict
    by_source = defaultdict(list)
    for post in posts:
        by_source[post.get('source_display_name', 'Unknown')].append(post)

    for source, source_posts in by_source.items():
        print(f"\n[{source}] {len(source_posts)}개")
        for i, post in enumerate(source_posts[:3], 1):  # 최대 3개만 표시
            print(f"  {i}. {post['title'][:50]}...")
