"""
네이버 블로그 포스트 수집기
RSS 피드와 웹 스크래핑을 결합하여 포스트 수집
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import json
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NaverBlogCollector:
    def __init__(self, config):
        self.config = config
        # 새로운 config 구조 지원
        if 'data_sources' in config and 'naver_blog' in config['data_sources']:
            self.blog_config = config['data_sources']['naver_blog']
        elif 'blog' in config:
            self.blog_config = config['blog']
        else:
            raise ValueError("네이버 블로그 설정을 찾을 수 없습니다")

        self.collection_config = config.get('collection', {})
        self.storage_config = config.get('storage', {})

    def collect_posts(self, reference_date=None):
        """RSS 피드에서 포스트 목록을 가져오고 웹 스크래핑으로 상세 정보 수집

        Args:
            reference_date: 기준 날짜 (datetime 객체). None이면 현재 날짜 사용
        """
        logger.info("네이버 블로그 포스트 수집 시작")

        # 1. RSS 피드에서 포스트 목록 가져오기
        rss_posts = self._fetch_rss_feed()

        # 2. 최근 1주일 이내 포스트 필터링
        recent_posts = self._filter_recent_posts(rss_posts, reference_date)

        # 3. 각 포스트의 상세 내용 스크래핑
        detailed_posts = []
        max_posts = self.blog_config.get('max_posts', self.collection_config.get('max_posts_per_source', 20))
        for i, post in enumerate(recent_posts[:max_posts]):
            logger.info(f"포스트 수집 중 ({i+1}/{min(len(recent_posts), max_posts)}): {post['title']}")
            try:
                detailed_post = self._scrape_post_detail(post)
                if detailed_post:
                    detailed_posts.append(detailed_post)
                time.sleep(1)  # 서버 부하 방지
            except Exception as e:
                logger.error(f"포스트 수집 실패 ({post['link']}): {str(e)}")
                continue

        logger.info(f"총 {len(detailed_posts)}개 포스트 수집 완료")

        # 4. 수집한 데이터 저장
        self._save_collected_data(detailed_posts, reference_date)

        return detailed_posts

    def _fetch_rss_feed(self):
        """RSS 피드에서 포스트 목록 가져오기"""
        logger.info(f"RSS 피드 가져오기: {self.blog_config['rss_url']}")

        try:
            feed = feedparser.parse(self.blog_config['rss_url'])
            posts = []

            for entry in feed.entries:
                post = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')
                }
                posts.append(post)

            logger.info(f"RSS 피드에서 {len(posts)}개 항목 발견")
            return posts

        except Exception as e:
            logger.error(f"RSS 피드 가져오기 실패: {str(e)}")
            return []

    def _filter_recent_posts(self, posts, reference_date=None):
        """최근 N일 이내 포스트만 필터링

        Args:
            posts: 포스트 리스트
            reference_date: 기준 날짜. None이면 현재 날짜 사용
        """
        days_lookback = self.blog_config.get('days_lookback', self.collection_config.get('days_lookback', 7))
        base_date = reference_date if reference_date else datetime.now()
        cutoff_date = base_date - timedelta(days=days_lookback)

        logger.info(f"기준 날짜: {base_date.strftime('%Y-%m-%d')}, 수집 범위: {cutoff_date.strftime('%Y-%m-%d')} ~ {base_date.strftime('%Y-%m-%d')}")

        recent_posts = []
        for post in posts:
            try:
                # 날짜 파싱
                if post['published']:
                    post_date = date_parser.parse(post['published'])
                    # timezone-aware datetime을 naive로 변환
                    if post_date.tzinfo:
                        post_date = post_date.replace(tzinfo=None)

                    # cutoff_date 이후, base_date 이전 포스트만 포함
                    if cutoff_date <= post_date <= base_date:
                        recent_posts.append(post)
            except Exception as e:
                logger.warning(f"날짜 파싱 실패 ({post['title']}): {str(e)}")
                # 날짜 파싱 실패시에도 포함
                recent_posts.append(post)

        logger.info(f"최근 {days_lookback}일 이내 포스트: {len(recent_posts)}개")
        return recent_posts

    def _scrape_post_detail(self, post):
        """웹 스크래핑으로 포스트 상세 내용 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(post['link'], headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 네이버 블로그 본문 추출 (iframe 내부 또는 직접 접근)
            # 여러 선택자를 시도
            content = ""

            # 방법 1: se-main-container 클래스 (스마트에디터 ONE)
            se_container = soup.find('div', class_='se-main-container')
            if se_container:
                content = se_container.get_text(strip=True, separator='\n')

            # 방법 2: post-view 클래스
            if not content:
                post_view = soup.find('div', {'id': 'postViewArea'}) or soup.find('div', class_='post-view')
                if post_view:
                    content = post_view.get_text(strip=True, separator='\n')

            # 방법 3: RSS summary 사용
            if not content:
                content = post['summary']

            # 포스트 상세 정보 구성
            detailed_post = {
                'title': post['title'],
                'link': post['link'],
                'published': post['published'],
                'content': content[:5000],  # 최대 5000자로 제한
                'collected_at': datetime.now().isoformat()
            }

            return detailed_post

        except Exception as e:
            logger.error(f"포스트 스크래핑 실패 ({post['link']}): {str(e)}")
            # 스크래핑 실패시 RSS 정보만 반환
            return {
                'title': post['title'],
                'link': post['link'],
                'published': post['published'],
                'content': post['summary'],
                'collected_at': datetime.now().isoformat()
            }

    def _save_collected_data(self, posts, reference_date=None):
        """수집한 데이터를 JSON 파일로 저장"""
        feeds_dir = self.storage_config['feeds_dir']
        os.makedirs(feeds_dir, exist_ok=True)

        base_date = reference_date if reference_date else datetime.now()
        timestamp = base_date.strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(feeds_dir, f'collected_posts_{timestamp}.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

        logger.info(f"수집 데이터 저장 완료: {filename}")


if __name__ == "__main__":
    # 테스트용 코드
    import yaml

    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    collector = NaverBlogCollector(config)
    posts = collector.collect_posts()

    print(f"\n수집 완료: {len(posts)}개 포스트")
    for i, post in enumerate(posts[:3], 1):
        print(f"\n{i}. {post['title']}")
        print(f"   링크: {post['link']}")
        print(f"   날짜: {post['published']}")
        print(f"   내용 길이: {len(post['content'])}자")
