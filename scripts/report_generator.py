"""
Markdown 형식의 주간 인사이트 리포트 생성기
"""
import os
from datetime import datetime
import logging
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.report_config = config['report']

    def generate_report(self, categorized_posts, reference_date=None):
        """카테고리별로 분류된 포스트로 Markdown 리포트 생성

        Args:
            categorized_posts: 카테고리별로 분류된 포스트 딕셔너리
            reference_date: 리포트 기준 날짜. None이면 현재 날짜 사용
        """
        logger.info("Markdown 리포트 생성 시작")

        # 리포트 내용 생성
        report_content = self._create_report_content(categorized_posts, reference_date)

        # 파일로 저장
        report_path = self._save_report(report_content, reference_date)

        logger.info(f"리포트 생성 완료: {report_path}")
        return report_path

    def _create_report_content(self, categorized_posts, reference_date=None):
        """리포트 내용 생성"""
        lines = []

        # 헤더
        base_date = reference_date if reference_date else datetime.now()
        report_date = base_date.strftime(self.report_config['date_format'])
        lines.append(f"# 과학기술 & AI 주간 인사이트 리포트")
        lines.append(f"")
        lines.append(f"**생성 날짜**: {report_date}")
        lines.append(f"")

        # 통계 요약
        total_posts = sum(len(posts) for posts in categorized_posts.values())
        lines.append(f"## 📊 요약")
        lines.append(f"")
        lines.append(f"- **총 포스트 수**: {total_posts}개")
        lines.append(f"- **분석 기간**: 최근 7일")
        lines.append(f"- **카테고리 수**: {len(categorized_posts)}개")
        lines.append(f"")

        # 카테고리별 분포
        lines.append(f"### 카테고리별 분포")
        lines.append(f"")
        for category in sorted(categorized_posts.keys()):
            count = len(categorized_posts[category])
            lines.append(f"- **{category}**: {count}개")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

        # 카테고리별 상세 내용
        # 카테고리 순서 정의
        category_order = ['AI 기술', '과학 기술', '연구 개발', '산업 동향', '정책 및 규제', '기타']
        sorted_categories = [cat for cat in category_order if cat in categorized_posts]
        # 정의되지 않은 카테고리 추가
        sorted_categories.extend([cat for cat in categorized_posts if cat not in category_order])

        for category in sorted_categories:
            posts = categorized_posts[category]
            if not posts:
                continue

            # 카테고리 아이콘
            icon = self._get_category_icon(category)
            lines.append(f"## {icon} {category}")
            lines.append(f"")

            # 날짜순 정렬 (최신순)
            sorted_posts = sorted(posts, key=lambda p: self._parse_date(p.get('published', '')), reverse=True)

            for i, post in enumerate(sorted_posts, 1):
                # 포스트 제목
                lines.append(f"### {i}. {post['title']}")
                lines.append(f"")

                # 메타 정보
                pub_date = self._format_date(post.get('published', ''))
                lines.append(f"**발행일**: {pub_date}")
                lines.append(f"")

                # 요약
                lines.append(f"**요약**:")
                lines.append(f"> {post['summary']}")
                lines.append(f"")

                # 링크
                lines.append(f"🔗 [원문 보기]({post['link']})")
                lines.append(f"")
                lines.append(f"---")
                lines.append(f"")

        # 푸터
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"*이 리포트는 AI를 활용하여 자동 생성되었습니다.*")
        lines.append(f"")
        lines.append(f"*생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return '\n'.join(lines)

    def _get_category_icon(self, category):
        """카테고리별 아이콘 반환"""
        icons = {
            'AI 기술': '🤖',
            '과학 기술': '🔬',
            '산업 동향': '📈',
            '연구 개발': '🔍',
            '정책 및 규제': '📋',
            '기타': '📌'
        }
        return icons.get(category, '📄')

    def _parse_date(self, date_str):
        """날짜 문자열을 datetime 객체로 변환"""
        try:
            return date_parser.parse(date_str)
        except:
            return datetime.min

    def _format_date(self, date_str):
        """날짜를 보기 좋은 형식으로 포맷"""
        try:
            dt = date_parser.parse(date_str)
            return dt.strftime('%Y년 %m월 %d일')
        except:
            return date_str

    def _save_report(self, content, reference_date=None):
        """리포트를 파일로 저장"""
        output_dir = self.report_config['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        # 파일명 생성
        base_date = reference_date if reference_date else datetime.now()
        timestamp = base_date.strftime(self.report_config['date_format'])
        filename = f"{timestamp}_weekly_insight_report.md"
        filepath = os.path.join(output_dir, filename)

        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # 웹 뷰어용 폴더에도 복사
        try:
            import shutil
            web_reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
            os.makedirs(web_reports_dir, exist_ok=True)
            web_filepath = os.path.join(web_reports_dir, filename)
            shutil.copy2(filepath, web_filepath)
            logger.info(f"웹 뷰어용 리포트 복사: {web_filepath}")
        except Exception as e:
            logger.warning(f"웹 뷰어용 리포트 복사 실패: {e}")

        return filepath


if __name__ == "__main__":
    # 테스트용 코드
    import yaml

    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 테스트 데이터
    test_categorized = {
        'AI 기술': [
            {
                'title': 'GPT-4 신기능 발표',
                'summary': 'OpenAI가 GPT-4의 멀티모달 기능을 공개했습니다. 이미지와 텍스트를 동시에 처리할 수 있습니다.',
                'link': 'https://example.com/1',
                'published': '2024-01-10',
                'category': 'AI 기술'
            }
        ],
        '과학 기술': [
            {
                'title': '새로운 양자컴퓨터 개발',
                'summary': 'IBM이 1000큐비트 양자컴퓨터를 개발했습니다. 기존 대비 10배 향상된 성능을 보입니다.',
                'link': 'https://example.com/2',
                'published': '2024-01-09',
                'category': '과학 기술'
            }
        ]
    }

    generator = ReportGenerator(config)
    report_path = generator.generate_report(test_categorized)

    print(f"\n테스트 리포트 생성 완료: {report_path}")

    # 생성된 리포트 내용 출력
    with open(report_path, 'r', encoding='utf-8') as f:
        print("\n리포트 내용:")
        print(f.read())
