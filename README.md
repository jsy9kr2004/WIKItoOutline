# WIKItoOutline

MediaWiki에서 모든 문서 제목을 가져와 텍스트 파일로 저장하는 도구입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 설정

1. `.env.example` 파일을 복사하여 `.env` 파일 생성:
```bash
cp .env.example .env
```

2. `.env` 파일을 열어 실제 값으로 수정:
```
WIKI_API_URL=http://your-wiki-server:port/api.php
WIKI_USERNAME=your_username
WIKI_PASSWORD=your_password
```

## 사용법

```bash
python main.py
```

실행하면 `wiki_titles.txt` 파일에 모든 문서 제목이 저장됩니다.

## 주의사항

- `.env` 파일은 보안 정보를 포함하므로 git에 커밋하지 마세요
- `.env` 파일은 이미 `.gitignore`에 포함되어 있습니다