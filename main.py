import os
import requests
from collections import defaultdict
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

# 네임스페이스 이름 매핑 (일반적인 MediaWiki 네임스페이스)
NAMESPACE_NAMES = {
    0: "Main (문서)",
    1: "Talk (토론)",
    2: "User (사용자)",
    3: "User talk (사용자 토론)",
    4: "Project",
    5: "Project talk",
    6: "File (파일)",
    7: "File talk",
    8: "MediaWiki",
    9: "MediaWiki talk",
    10: "Template (틀)",
    11: "Template talk",
    12: "Help (도움말)",
    13: "Help talk",
    14: "Category (카테고리)",
    15: "Category talk"
}

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

def get_page_content(title):
    """특정 페이지의 내용 가져오기"""
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json"
    }

    response = session.get(api_url, params=params)
    data = response.json()

    if 'query' not in data or 'pages' not in data['query']:
        return None

    pages = data['query']['pages']
    page_id = list(pages.keys())[0]

    if page_id == '-1':
        return None

    if 'revisions' not in pages[page_id]:
        return None

    return pages[page_id]['revisions'][0]['slots']['main']['*']


def check_sidebar_and_navigation():
    """사이드바 및 내비게이션 관련 페이지들 확인"""
    print("\n위키의 내비게이션 구조를 확인하는 중...")

    pages_to_check = [
        "MediaWiki:Sidebar",
        "MediaWiki:Navigation",
        "목차",
        "분류",
        "위키 구조"
    ]

    found_pages = {}

    for page_title in pages_to_check:
        content = get_page_content(page_title)
        if content:
            found_pages[page_title] = content
            print(f"  ✓ '{page_title}' 페이지 발견")

    return found_pages


def get_all_pages_with_info():
    """모든 페이지의 상세 정보 가져오기 (제목, 네임스페이스, 카테고리)"""
    pages = []

    params = {
        "action": "query",
        "generator": "allpages",
        "gaplimit": "50",  # 카테고리 정보도 가져오므로 배치 크기 줄임
        "prop": "categories|info",
        "cllimit": "max",
        "clshow": "!hidden",  # 숨겨진 카테고리 제외
        "format": "json"
    }

    print("문서 목록과 상세 정보를 가져오는 중...")

    while True:
        response = session.get(api_url, params=params)
        data = response.json()

        # 에러 체크
        if 'error' in data:
            print(f"API 에러: {data['error']}")
            break

        if 'query' not in data or 'pages' not in data['query']:
            if 'query' not in data:
                print("응답에 query가 없습니다.")
            break

        for page_id, page_data in data['query']['pages'].items():
            page_info = {
                'title': page_data['title'],
                'namespace': page_data['ns'],
                'categories': []
            }

            # 카테고리 정보 추출
            if 'categories' in page_data:
                for cat in page_data['categories']:
                    # 'Category:' 접두어 제거
                    cat_name = cat['title'].replace('Category:', '')
                    page_info['categories'].append(cat_name)

            pages.append(page_info)

        if 'continue' not in data:
            break

        # continue 파라미터 업데이트
        for key, value in data['continue'].items():
            if key != 'continue':
                params[key] = value

        print(f"진행 중... (현재 {len(pages)}개)")

    return pages


def classify_by_category(pages):
    """카테고리별로 페이지 분류"""
    category_map = defaultdict(list)
    no_category = []

    for page in pages:
        if page['categories']:
            for category in page['categories']:
                category_map[category].append(page['title'])
        else:
            no_category.append(page['title'])

    return dict(sorted(category_map.items())), no_category


def classify_by_namespace(pages):
    """네임스페이스별로 페이지 분류"""
    namespace_map = defaultdict(list)

    for page in pages:
        ns = page['namespace']
        namespace_map[ns].append(page['title'])

    return dict(sorted(namespace_map.items()))


def classify_by_subpage(pages):
    """하위 페이지(경로) 기반으로 계층 구조 생성"""
    root_pages = []
    subpage_map = defaultdict(list)

    for page in pages:
        title = page['title']
        if '/' in title:
            # 상위 페이지 추출
            parent = title.rsplit('/', 1)[0]
            subpage_map[parent].append(title)
        else:
            root_pages.append(title)

    return sorted(root_pages), dict(sorted(subpage_map.items()))


def write_hierarchy(file, items, indent=0, prefix=""):
    """계층 구조를 파일에 작성"""
    for item in items:
        file.write("  " * indent + prefix + item + "\n")

# 메인 실행
if __name__ == "__main__":
    if not login():
        print("로그인에 실패했습니다. username과 password를 확인하세요.")
        exit(1)

    # 먼저 사이드바/내비게이션 구조 확인
    found_pages = check_sidebar_and_navigation()

    if found_pages:
        print("\n발견된 내비게이션 페이지:")
        print("="*60)
        for page_title, content in found_pages.items():
            print(f"\n페이지: {page_title}")
            print(f"내용 길이: {len(content)} 문자")
            print("-"*60)
            # 처음 500자 미리보기
            preview = content[:500] if len(content) > 500 else content
            print(preview)
            if len(content) > 500:
                print(f"\n... (총 {len(content)}자 중 500자만 표시)")
            print()

        # 전체 내용을 파일로 저장
        with open('wiki_navigation_raw.txt', 'w', encoding='utf-8') as f:
            for page_title, content in found_pages.items():
                f.write(f"{'='*60}\n")
                f.write(f"페이지: {page_title}\n")
                f.write(f"{'='*60}\n\n")
                f.write(content)
                f.write("\n\n\n")

        print("✓ 'wiki_navigation_raw.txt' 파일에 원본 내용 저장 완료")
        print("\n이 내용을 확인하시고, 어떤 형태의 구조인지 알려주시면")
        print("그에 맞는 파싱 방법을 구현하겠습니다.")
        exit(0)

    print("\n내비게이션 페이지를 찾을 수 없습니다.")
    print("위키 왼쪽 사이드바의 구조가 어떤 페이지에서 정의되는지 확인이 필요합니다.")
    print("\n대안으로 기존 분류 방법을 실행하시겠습니까? (계속하려면 주석 처리)")
    exit(0)

    # 모든 페이지 정보 가져오기
    pages = get_all_pages_with_info()

    if not pages:
        print("가져온 문서가 없습니다.")
        exit(1)

    print(f"\n총 {len(pages)}개의 문서를 가져왔습니다.")
    print("="*60)

    # 1. 카테고리 기반 분류
    print("\n[1/3] 카테고리 기반 분류 생성 중...")
    category_map, no_category = classify_by_category(pages)

    with open('wiki_by_category.txt', 'w', encoding='utf-8') as f:
        f.write(f"카테고리별 위키 문서 분류\n")
        f.write(f"총 {len(pages)}개의 문서\n")
        f.write(f"카테고리 수: {len(category_map)}개\n")
        f.write("="*60 + "\n\n")

        for category, page_list in category_map.items():
            f.write(f"\n[{category}] ({len(page_list)}개)\n")
            f.write("-"*60 + "\n")
            for page_title in sorted(page_list):
                f.write(f"  - {page_title}\n")

        if no_category:
            f.write(f"\n\n[카테고리 없음] ({len(no_category)}개)\n")
            f.write("-"*60 + "\n")
            for page_title in sorted(no_category):
                f.write(f"  - {page_title}\n")

    print(f"   ✓ 'wiki_by_category.txt' 저장 완료 (카테고리 {len(category_map)}개)")

    # 2. 네임스페이스 기반 분류
    print("\n[2/3] 네임스페이스 기반 분류 생성 중...")
    namespace_map = classify_by_namespace(pages)

    with open('wiki_by_namespace.txt', 'w', encoding='utf-8') as f:
        f.write(f"네임스페이스별 위키 문서 분류\n")
        f.write(f"총 {len(pages)}개의 문서\n")
        f.write("="*60 + "\n\n")

        for ns, page_list in namespace_map.items():
            ns_name = NAMESPACE_NAMES.get(ns, f"Namespace {ns}")
            f.write(f"\n[{ns_name}] ({len(page_list)}개)\n")
            f.write("-"*60 + "\n")
            for page_title in sorted(page_list):
                f.write(f"  - {page_title}\n")

    print(f"   ✓ 'wiki_by_namespace.txt' 저장 완료 (네임스페이스 {len(namespace_map)}개)")

    # 3. 하위 페이지(경로) 기반 분류
    print("\n[3/3] 하위 페이지(경로) 기반 분류 생성 중...")
    root_pages, subpage_map = classify_by_subpage(pages)

    with open('wiki_by_subpage.txt', 'w', encoding='utf-8') as f:
        f.write(f"경로 기반 위키 문서 계층 구조\n")
        f.write(f"총 {len(pages)}개의 문서\n")
        f.write(f"최상위 페이지: {len(root_pages)}개\n")
        f.write(f"하위 페이지가 있는 페이지: {len(subpage_map)}개\n")
        f.write("="*60 + "\n\n")

        # 최상위 페이지 출력
        f.write("=== 최상위 페이지 ===\n\n")
        for root_page in root_pages:
            f.write(f"{root_page}\n")

            # 이 페이지의 하위 페이지 출력
            if root_page in subpage_map:
                for subpage in sorted(subpage_map[root_page]):
                    depth = subpage.count('/')
                    f.write("  " * depth + f"└─ {subpage.split('/')[-1]}\n")

        # 부모가 없는 하위 페이지들 (부모 페이지가 존재하지 않는 경우)
        orphan_subpages = []
        for parent, children in subpage_map.items():
            # 부모가 실제 페이지 목록에 없는 경우
            parent_exists = any(p['title'] == parent for p in pages)
            if not parent_exists and parent not in root_pages:
                orphan_subpages.append((parent, children))

        if orphan_subpages:
            f.write("\n\n=== 상위 페이지가 없는 하위 페이지 ===\n\n")
            for parent, children in sorted(orphan_subpages):
                f.write(f"\n[{parent}] (상위 페이지 없음)\n")
                for subpage in sorted(children):
                    f.write(f"  - {subpage}\n")

    print(f"   ✓ 'wiki_by_subpage.txt' 저장 완료")

    # 요약 통계
    print("\n" + "="*60)
    print("모든 분류 완료!")
    print(f"\n생성된 파일:")
    print(f"  1. wiki_by_category.txt  - 카테고리별 분류 ({len(category_map)}개 카테고리)")
    print(f"  2. wiki_by_namespace.txt - 네임스페이스별 분류 ({len(namespace_map)}개 네임스페이스)")
    print(f"  3. wiki_by_subpage.txt   - 경로 기반 계층 구조 ({len(root_pages)}개 최상위 페이지)")
    print("="*60)