"""
AI 인사이트 리포트 웹 뷰어
"""
from flask import Flask, render_template, send_file, abort
import os
import glob
from datetime import datetime
import markdown

app = Flask(__name__)

# 리포트 디렉토리 설정
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
FEEDS_DIR = os.path.join(os.path.dirname(__file__), 'feeds')

# 템플릿과 정적 파일 경로 설정
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
app.static_folder = os.path.join(os.path.dirname(__file__), 'static')


def get_report_list():
    """리포트 목록 가져오기"""
    reports = []

    # reports 디렉토리가 없으면 생성
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        return reports

    # 모든 .md 파일 찾기
    pattern = os.path.join(REPORTS_DIR, '*.md')
    report_files = glob.glob(pattern)

    for filepath in report_files:
        filename = os.path.basename(filepath)

        # 파일 정보 추출
        file_stat = os.stat(filepath)
        file_size = file_stat.st_size
        created_time = datetime.fromtimestamp(file_stat.st_mtime)

        # 파일에서 포스트 수 추출 (간단하게 첫 몇 줄 읽기)
        post_count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(500)
            if '총 포스트 수**:' in content:
                try:
                    line = [l for l in content.split('\n') if '총 포스트 수' in l][0]
                    post_count = int(line.split(':')[1].strip().replace('개', ''))
                except:
                    pass

        reports.append({
            'filename': filename,
            'title': filename.replace('_weekly_insight_report.md', '').replace('_', ' '),
            'created': created_time.strftime('%Y년 %m월 %d일 %H:%M'),
            'size': f"{file_size / 1024:.1f} KB",
            'post_count': post_count
        })

    # 파일명 기준 최신순 정렬 (YYYY-MM-DD 형식이므로 역순)
    reports.sort(key=lambda x: x['filename'], reverse=True)

    return reports


@app.route('/')
def index():
    """메인 페이지 - 리포트 목록"""
    reports = get_report_list()
    return render_template('index.html', reports=reports)


@app.route('/report/<filename>')
def view_report(filename):
    """리포트 보기"""
    # 보안: 경로 조작 방지
    if '..' in filename or '/' in filename or '\\' in filename:
        abort(404)

    filepath = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(filepath):
        abort(404)

    # Markdown 파일 읽기
    with open(filepath, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Markdown을 HTML로 변환
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'toc']
    )

    return render_template('report.html',
                         filename=filename,
                         content=html_content,
                         md_content=md_content)


@app.route('/download/<filename>')
def download_report(filename):
    """리포트 다운로드"""
    # 보안: 경로 조작 방지
    if '..' in filename or '/' in filename or '\\' in filename:
        abort(404)

    filepath = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(filepath):
        abort(404)

    return send_file(filepath, as_attachment=True)


if __name__ == '__main__':
    # 필요한 디렉토리 생성
    os.makedirs(app.template_folder, exist_ok=True)
    os.makedirs(app.static_folder, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("="*60)
    print("AI 인사이트 리포트 웹 뷰어 시작")
    print("="*60)
    print(f"\n웹 브라우저에서 접속: http://localhost:5000")
    print(f"리포트 디렉토리: {REPORTS_DIR}")
    print(f"\n종료하려면 Ctrl+C를 누르세요.\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
