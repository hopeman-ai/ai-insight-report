"""
곽재원의 Now&Future 칼럼 수집기 (아주경제)
"""
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re
import time
import logging


class AjunewsCollector:
    """아주경제 곽재원 칼럼 수집기"""

    def __init__(self, config):
        self.config = config
        self.source_config = config.get('data_sources', {}).get('ajunews_column', {})
        self.base_url = self.source_config.get('base_url', 'https://www.ajunews.com')
        self.max_posts = self.source_config.get('max_posts', 10)
        self.year_filter = self.source_config.get('year_filter', 2025)
        self.feeds_dir = config.get('storage', {}).get('feeds_dir', 'feeds')

        self.logger = logging.getLogger(__name__)

        # 캐시 파일 경로
        self.cache_file = os.path.join(self.feeds_dir, 'ajunews_url_cache.json')

        # 알려진 기사 URL 목록 (웹 검색 결과 기반)
        # 실제 운영시 정기적으로 업데이트 필요
        self.known_urls = [
            "https://www.ajunews.com/view/20251217160834163",  # 2025-12
            "https://www.ajunews.com/view/20251124072337005",  # 2025-11
            "https://www.ajunews.com/view/20250925081655847",  # 2025-09
            "https://www.ajunews.com/view/20251020092112653",  # 2025-10
            "https://www.ajunews.com/view/20250825082808870",  # 2025-08
            "https://www.ajunews.com/view/20250716103132938",  # 2025-07
            "https://www.ajunews.com/view/20250514085620201",  # 2025-05
            "https://www.ajunews.com/view/20250114095600305",  # 2025-01
        ]

    def collect_posts(self, reference_date=None):
        """칼럼 수집"""
        self.logger.info("곽재원 Now&Future 칼럼 수집 시작")

        # 캐시된 URL 목록 로드
        url_list = self._load_or_generate_url_list()

        posts = []
        for url in url_list[:self.max_posts * 2]:  # 여유있게 가져오기
            try:
                post = self._scrape_article(url)
                if post and self._is_valid_post(post):
                    posts.append(post)
                    self.logger.info(f"수집 완료: {post['title']}")

                    if len(posts) >= self.max_posts:
                        break

                # 요청 간 딜레이 (서버 부하 방지)
                time.sleep(1)

            except Exception as e:
                self.logger.warning(f"기사 수집 실패 ({url}): {e}")
                continue

        self.logger.info(f"총 {len(posts)}개 칼럼 수집 완료")

        # 수집 결과 저장
        self._save_posts(posts)

        return posts

    def _load_or_generate_url_list(self):
        """캐시된 URL 목록 로드 또는 생성"""
        # 캐시 파일이 있고 최신이면 사용
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    cache_date = datetime.fromisoformat(cache.get('updated', '2000-01-01'))
                    if datetime.now() - cache_date < timedelta(days=1):
                        self.logger.info("캐시된 URL 목록 사용")
                        return cache.get('urls', self.known_urls)
            except Exception as e:
                self.logger.warning(f"캐시 로드 실패: {e}")

        # 캐시가 없거나 오래되었으면 알려진 URL 사용
        self.logger.info("기본 URL 목록 사용")
        return self.known_urls

    def _scrape_article(self, url):
        """개별 기사 스크래핑"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # JSON-LD 구조화 데이터 추출
        json_ld = self._extract_json_ld(soup)

        # 제목
        title = self._extract_title(soup, json_ld)

        # 칼럼명 확인 (제목에 "곽재원의 Now&Future"가 포함되어야 함)
        if not self._is_now_future_column(title):
            self.logger.debug(f"Now&Future 칼럼이 아님: {title}")
            return None

        # 작성자 추출 (제목에서 추출 가능)
        author = "곽재원"

        # 날짜
        published_date = self._extract_date(soup, json_ld)

        # 태그
        tags = self._extract_tags(soup)

        # 본문
        content = self._extract_content(soup)

        return {
            'title': title,
            'url': url,
            'author': author,
            'published': published_date,
            'tags': tags,
            'content': content,
            'source': '곽재원의 Now&Future (아주경제)'
        }

    def _extract_json_ld(self, soup):
        """JSON-LD 구조화 데이터 추출"""
        try:
            script = soup.find('script', type='application/ld+json')
            if script:
                return json.loads(script.string)
        except:
            pass
        return {}

    def _extract_title(self, soup, json_ld):
        """제목 추출"""
        # JSON-LD에서 먼저 시도
        if json_ld.get('headline'):
            return json_ld['headline']

        # meta 태그에서 시도
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')

        # h1 태그에서 시도
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        return ""

    def _extract_author(self, soup, json_ld):
        """작성자 추출"""
        # JSON-LD에서 먼저 시도
        if json_ld.get('author'):
            authors = json_ld['author']
            if isinstance(authors, list) and len(authors) > 0:
                return authors[0].get('name', '')
            elif isinstance(authors, dict):
                return authors.get('name', '')

        # meta 태그에서 시도
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            return author_meta.get('content', '')

        return ""

    def _extract_date(self, soup, json_ld):
        """날짜 추출"""
        # JSON-LD에서 먼저 시도
        if json_ld.get('datePublished'):
            return json_ld['datePublished']

        # meta 태그에서 시도
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            return date_meta.get('content', '')

        return datetime.now().isoformat()

    def _extract_tags(self, soup):
        """태그 추출"""
        tags = []

        # .tag-link 클래스 찾기
        tag_links = soup.find_all('a', class_='tag-link')
        for tag_link in tag_links:
            tag_text = tag_link.get_text(strip=True)
            if tag_text and tag_text.startswith('#'):
                tags.append(tag_text[1:])  # # 제거
            elif tag_text:
                tags.append(tag_text)

        return tags

    def _extract_content(self, soup):
        """본문 추출"""
        # #articleBody에서 추출
        article_body = soup.find(id='articleBody')
        if article_body:
            # 이미지와 광고 제거
            for tag in article_body.find_all(['script', 'style', 'iframe', 'ins']):
                tag.decompose()

            return article_body.get_text(separator='\n', strip=True)

        # article 태그에서 시도
        article = soup.find('article')
        if article:
            return article.get_text(separator='\n', strip=True)

        return ""

    def _is_now_future_column(self, title):
        """Now&Future 칼럼인지 확인"""
        patterns = [
            r'\[곽재원의\s*Now&Future\]',
            r'\[곽재원의\s*Now\s*&\s*Future\]',
            r'곽재원의\s*Now&Future',
        ]

        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True

        return False

    def _is_valid_post(self, post):
        """유효한 포스트인지 확인 (연도 필터링)"""
        try:
            published = post.get('published', '')
            if published:
                # ISO 8601 형식 파싱
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                return pub_date.year == self.year_filter
        except Exception as e:
            self.logger.warning(f"날짜 파싱 실패: {e}")

        return True  # 파싱 실패시 포함

    def _save_posts(self, posts):
        """수집 결과 저장"""
        os.makedirs(self.feeds_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ajunews_kwak_{timestamp}.json'
        filepath = os.path.join(self.feeds_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'source': '곽재원의 Now&Future (아주경제)',
                'collected_at': datetime.now().isoformat(),
                'count': len(posts),
                'posts': posts
            }, f, ensure_ascii=False, indent=2)

        self.logger.info(f"데이터 저장 완료: {filepath}")


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

    # 수집 실행
    collector = AjunewsCollector(config)
    posts = collector.collect_posts()

    print(f"\n수집 완료: {len(posts)}개")
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. {post['title']}")
        print(f"   날짜: {post['published']}")
        print(f"   태그: {', '.join(post['tags'])}")
