"""
키워드 기반 포스트 분석기 (PoC용 - API 불필요)
- 주제 자동 분류
- 핵심 내용 요약
"""
import os
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PostAnalyzer:
    def __init__(self, config):
        self.config = config

        # 카테고리별 키워드 정의
        self.category_keywords = {
            'AI 기술': [
                'AI', '인공지능', '머신러닝', '딥러닝', 'LLM', 'GPT', 'ChatGPT',
                '생성형', '신경망', '학습', '알고리즘', '데이터', '모델',
                'transformer', 'neural', 'machine learning', 'deep learning',
                '언어모델', 'AGI', '자연어처리', 'NLP', '컴퓨터비전', 'CV'
            ],
            '과학 기술': [
                '과학', '물리', '화학', '생물', '우주', '천문', '양자',
                '나노', '신소재', '바이오', '유전', 'DNA', 'RNA', '단백질',
                '입자', '분자', '원자', '실험', '연구소', '발견',
                '의학', '치료', '질병', '백신', '암', '세포'
            ],
            '산업 동향': [
                '기업', '시장', '투자', '매출', '수익', '주가', '상장',
                'IPO', 'M&A', '인수', '합병', '스타트업', '벤처',
                '산업', '업계', '비즈니스', '경영', '전략', 'CEO',
                '제품', '출시', '서비스', '플랫폼'
            ],
            '연구 개발': [
                '연구', '개발', '논문', '저널', '학회', '발표', '특허',
                '실험', '테스트', '프로토타입', 'R&D', '연구원', '박사',
                '대학', '연구소', '랩', 'laboratory', '혁신', '기술개발'
            ],
            '정책 및 규제': [
                '정책', '규제', '법', '법률', '정부', '국회', '의회',
                '가이드라인', '지침', '규정', '제도', '법안', '개정',
                '허가', '승인', '인증', '표준', '안전', '보안'
            ]
        }

    def analyze_posts(self, posts):
        """모든 포스트 분석 (분류 + 요약)"""
        logger.info(f"{len(posts)}개 포스트 분석 시작 (키워드 기반)")

        analyzed_posts = []
        for i, post in enumerate(posts):
            logger.info(f"분석 중 ({i+1}/{len(posts)}): {post['title']}")
            try:
                analysis = self._analyze_single_post(post)
                analyzed_post = {
                    **post,
                    'category': analysis['category'],
                    'summary': analysis['summary']
                }
                analyzed_posts.append(analyzed_post)
            except Exception as e:
                logger.error(f"포스트 분석 실패 ({post['title']}): {str(e)}")
                # 분석 실패시 기본값 사용
                analyzed_posts.append({
                    **post,
                    'category': '기타',
                    'summary': self._create_simple_summary(post['content'])
                })

        logger.info(f"분석 완료: {len(analyzed_posts)}개 포스트")
        return analyzed_posts

    def _analyze_single_post(self, post):
        """단일 포스트 분석"""
        # 1. 카테고리 분류
        category = self._classify_category(post)

        # 2. 요약 생성
        summary = self._create_simple_summary(post['content'])

        return {
            'category': category,
            'summary': summary
        }

    def _classify_category(self, post):
        """키워드 기반 카테고리 분류"""
        text = (post['title'] + ' ' + post['content']).lower()

        # 각 카테고리별 매칭 점수 계산
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # 제목에서 발견시 가중치 2배
                if keyword.lower() in post['title'].lower():
                    score += 2
                # 본문에서 발견시 가중치 1배
                if keyword.lower() in post['content'].lower():
                    score += 1
            scores[category] = score

        # 가장 높은 점수의 카테고리 선택
        if max(scores.values()) > 0:
            category = max(scores, key=scores.get)
            logger.debug(f"'{post['title']}' -> {category} (점수: {scores[category]})")
            return category
        else:
            return '기타'

    def _create_simple_summary(self, content):
        """간단한 요약 생성 (첫 2-3문장)"""
        if not content:
            return "내용을 확인할 수 없습니다."

        # 문장 분리 (마침표, 느낌표, 물음표 기준)
        sentences = re.split(r'[.!?]\s+', content)

        # 빈 문장 제거 및 너무 짧은 문장 필터링
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            # 문장 분리 실패시 앞부분 200자 사용
            return content[:200].strip() + '...'

        # 처음 2-3문장 선택 (최대 300자)
        summary_sentences = []
        total_length = 0

        for sentence in sentences[:5]:  # 최대 5문장까지 검토
            if total_length + len(sentence) > 300:
                break
            summary_sentences.append(sentence)
            total_length += len(sentence)
            if len(summary_sentences) >= 2:  # 최소 2문장
                break

        if summary_sentences:
            summary = '. '.join(summary_sentences) + '.'
            return summary
        else:
            return content[:200].strip() + '...'

    def categorize_posts(self, analyzed_posts):
        """분석된 포스트를 카테고리별로 그룹화"""
        categorized = {}

        for post in analyzed_posts:
            category = post['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(post)

        # 카테고리별 포스트 수 로그
        for category, posts in categorized.items():
            logger.info(f"카테고리 '{category}': {len(posts)}개 포스트")

        return categorized


if __name__ == "__main__":
    # 테스트용 코드
    import yaml

    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 테스트 데이터
    test_posts = [
        {
            'title': 'GPT-4의 새로운 기능 소개',
            'content': 'OpenAI가 GPT-4의 새로운 멀티모달 기능을 발표했습니다. 이미지와 텍스트를 동시에 처리할 수 있게 되었습니다. 이는 인공지능 기술의 큰 진보입니다.',
            'link': 'https://example.com/1',
            'published': '2024-01-01'
        },
        {
            'title': '양자컴퓨터의 최신 연구 동향',
            'content': 'IBM이 새로운 양자컴퓨터 프로세서를 개발했습니다. 기존 대비 10배 향상된 큐비트 성능을 보입니다. 양자역학의 원리를 활용한 혁신적인 기술입니다.',
            'link': 'https://example.com/2',
            'published': '2024-01-02'
        }
    ]

    analyzer = PostAnalyzer(config)
    analyzed = analyzer.analyze_posts(test_posts)

    print("\n분석 결과:")
    for post in analyzed:
        print(f"\n제목: {post['title']}")
        print(f"카테고리: {post['category']}")
        print(f"요약: {post['summary']}")
