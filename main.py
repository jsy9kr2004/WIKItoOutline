import os
import requests
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

def get_all_pages():
    """모든 페이지 제목 가져오기"""
    titles = []
    
    params = {
        "action": "query",
        "list": "allpages",
        "aplimit": "500",
        "format": "json"
    }
    
    print("문서 목록을 가져오는 중...")
    
    while True:
        response = session.get(api_url, params=params)
        data = response.json()
        
        # 에러 체크
        if 'error' in data:
            print(f"API 에러: {data['error']}")
            break
        
        if 'query' not in data:
            print("응답 구조 확인:")
            print(data)
            break
        
        for page in data['query']['allpages']:
            titles.append(page['title'])
        
        if 'continue' not in data:
            break
        
        params['apcontinue'] = data['continue']['apcontinue']
        print(f"진행 중... (현재 {len(titles)}개)")
    
    return titles

# 메인 실행
if login():
    titles = get_all_pages()
    
    # txt 파일로 저장
    if titles:
        with open('wiki_titles.txt', 'w', encoding='utf-8') as f:
            f.write(f"총 {len(titles)}개의 문서\n")
            f.write("="*50 + "\n\n")
            for title in titles:
                f.write(title + '\n')
        
        print(f"완료! 총 {len(titles)}개의 문서를 'wiki_titles.txt'에 저장했습니다.")
    else:
        print("가져온 문서가 없습니다.")
else:
    print("로그인에 실패했습니다. username과 password를 확인하세요.")