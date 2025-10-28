import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# MediaWiki 설정 (환경 변수에서 읽기)
api_url = os.getenv("WIKI_API_URL")
username = os.getenv("WIKI_USERNAME")
password = os.getenv("WIKI_PASSWORD")

# 필수 환경 변수 확인
if not all([api_url, username, password]):
    raise ValueError(
        "환경 변수가 설정되지 않았습니다.\n"
        ".env 파일을 생성하고 다음 변수들을 설정하세요:\n"
        "- WIKI_API_URL\n"
        "- WIKI_USERNAME\n"
        "- WIKI_PASSWORD\n"
        "\n.env.example 파일을 참고하세요."
    )

# 세션 생성
session = requests.Session()


def login():
    """MediaWiki에 로그인"""
    print("로그인 중...")

    # 1. 로그인 토큰 가져오기
    params = {
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json"
    }

    response = session.get(api_url, params=params)
    data = response.json()

    if 'query' not in data or 'tokens' not in data['query']:
        print("로그인 토큰을 가져올 수 없습니다.")
        print(data)
        return False

    login_token = data['query']['tokens']['logintoken']

    # 2. 로그인 수행
    login_params = {
        "action": "login",
        "lgname": username,
        "lgpassword": password,
        "lgtoken": login_token,
        "format": "json"
    }

    response = session.post(api_url, data=login_params)
    data = response.json()

    if data['login']['result'] == 'Success':
        print("로그인 성공!")
        return True
    else:
        print(f"로그인 실패: {data['login']}")
        return False


def extract_page_title_from_url(url):
    """URL에서 페이지 제목 추출"""
    # URL 파싱
    parsed = urlparse(url)

    # /index.php/PageTitle 형식
    if '/index.php/' in parsed.path:
        title = parsed.path.split('/index.php/', 1)[1]
        return unquote(title)

    # /wiki/PageTitle 형식
    if '/wiki/' in parsed.path:
        title = parsed.path.split('/wiki/', 1)[1]
        return unquote(title)

    # 쿼리 파라미터에서 title 추출 (?title=PageTitle)
    if '?' in url:
        from urllib.parse import parse_qs
        query = parse_qs(parsed.query)
        if 'title' in query:
            return query['title'][0]

    return None


def get_page_content_with_sections(title):
    """페이지 내용과 섹션 구조 가져오기"""
    params = {
        "action": "parse",
        "page": title,
        "prop": "sections|wikitext",
        "format": "json"
    }

    response = session.get(api_url, params=params)
    data = response.json()

    if 'error' in data:
        print(f"  ✗ 오류: {data['error'].get('info', '알 수 없는 오류')}")
        return None, None

    if 'parse' not in data:
        return None, None

    sections = data['parse'].get('sections', [])
    wikitext = data['parse'].get('wikitext', {}).get('*', '')

    return sections, wikitext


def sanitize_filename(filename):
    """파일명으로 사용할 수 없는 문자 제거"""
    # 윈도우/리눅스에서 사용 불가능한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 공백을 언더스코어로 변경
    filename = filename.replace(' ', '_')
    # 연속된 언더스코어를 하나로
    filename = re.sub(r'_+', '_', filename)
    # 앞뒤 언더스코어 제거
    filename = filename.strip('_')
    return filename


def convert_wikitext_to_outline(title, sections, wikitext):
    """위키텍스트를 Outline 포맷으로 변환"""
    lines = []

    # 페이지 제목
    lines.append(f"# {title}")
    lines.append("")

    if not sections:
        # 섹션이 없는 경우 전체 내용 추가
        lines.append(wikitext)
    else:
        # 섹션별로 구조화
        wikitext_lines = wikitext.split('\n')

        for section in sections:
            level = int(section['level'])
            section_title = section['line']
            indent = "  " * (level - 1)

            # Outline 스타일 제목
            lines.append(f"{indent}- {section_title}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("")

        # 전체 내용도 포함
        lines.append(wikitext)

    return '\n'.join(lines)


def read_urls_from_file(filename='urls.txt'):
    """파일에서 URL 목록 읽기"""
    urls = []

    if not os.path.exists(filename):
        print(f"오류: '{filename}' 파일을 찾을 수 없습니다.")
        print(f"'{filename}' 파일을 생성하고 위키 페이지 URL을 한 줄에 하나씩 입력하세요.")
        return urls

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 빈 줄이나 주석 무시
            if not line or line.startswith('#'):
                continue
            urls.append(line)

    return urls


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("위키 페이지 → Outline 변환 도구")
    print("=" * 60)

    # 로그인
    if not login():
        print("로그인에 실패했습니다.")
        return

    # URL 목록 읽기
    urls = read_urls_from_file('urls.txt')

    if not urls:
        print("\n처리할 URL이 없습니다.")
        print("urls.txt 파일에 위키 페이지 URL을 추가하세요.")
        return

    print(f"\n총 {len(urls)}개의 URL을 처리합니다.")
    print("=" * 60)

    # result 폴더 생성
    result_dir = Path('result')
    result_dir.mkdir(exist_ok=True)

    # 각 URL 처리
    success_count = 0

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 처리 중: {url}")

        # URL에서 페이지 제목 추출
        page_title = extract_page_title_from_url(url)

        if not page_title:
            print(f"  ✗ URL에서 페이지 제목을 추출할 수 없습니다.")
            continue

        print(f"  페이지 제목: {page_title}")

        # 페이지 내용 가져오기
        sections, wikitext = get_page_content_with_sections(page_title)

        if wikitext is None:
            print(f"  ✗ 페이지를 가져올 수 없습니다.")
            continue

        # Outline 포맷으로 변환
        outline_content = convert_wikitext_to_outline(page_title, sections, wikitext)

        # 파일명 생성 (페이지 제목 기반)
        safe_filename = sanitize_filename(page_title)
        output_file = result_dir / f"{safe_filename}.txt"

        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(outline_content)

        print(f"  ✓ 저장 완료: {output_file}")
        success_count += 1

    # 완료 메시지
    print("\n" + "=" * 60)
    print(f"완료! {success_count}/{len(urls)}개의 페이지를 변환했습니다.")
    print(f"결과 파일 위치: {result_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
