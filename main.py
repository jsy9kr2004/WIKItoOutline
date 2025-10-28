import requests

# MediaWiki 설정
api_url = "http://192.168.1.153:8080/api.php"
username = "your_username"  # 여기에 위키 사용자명 입력
password = "your_password"  # 여기에 위키 비밀번호 입력

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