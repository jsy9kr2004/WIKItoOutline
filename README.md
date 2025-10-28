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

### 1. 위키 문서 구조 분석 (main.py)

```bash
python main.py
```

실행하면 3가지 방법으로 분류된 결과 파일이 생성됩니다:

### 생성되는 파일

1. **`wiki_by_category.txt`** - 카테고리 기반 분류
   - 각 문서가 속한 카테고리별로 그룹화
   - 가장 일반적이고 체계적인 분류 방법
   - 카테고리가 없는 문서도 별도로 표시

2. **`wiki_by_namespace.txt`** - 네임스페이스 기반 분류
   - 페이지 유형별로 분류 (Main, User, File, Template 등)
   - MediaWiki의 기본 페이지 구조 파악에 유용

3. **`wiki_by_subpage.txt`** - 하위 페이지(경로) 기반 분류
   - URL 경로 기반 계층 구조 (`/`로 구분)
   - 상위-하위 관계를 트리 구조로 표현
   - 예: `프로젝트/하위프로젝트/페이지`

### 2. 위키 페이지 → Outline 변환 (convert_to_outline.py)

특정 위키 페이지들을 Outline 포맷으로 변환합니다.

#### 설정

1. `urls.txt.example` 파일을 복사하여 `urls.txt` 파일 생성:
```bash
cp urls.txt.example urls.txt
```

2. `urls.txt` 파일에 변환할 위키 페이지 URL을 한 줄에 하나씩 입력:
```
http://192.168.1.153:8080/index.php/Main_Page
http://192.168.1.153:8080/index.php/프로젝트/개요
http://192.168.1.153:8080/index.php/문서/가이드
```

#### 실행

```bash
python convert_to_outline.py
```

#### 결과

- `result/` 폴더에 각 페이지별로 outline 포맷 파일이 생성됩니다
- 파일명은 페이지 제목 기반으로 자동 생성됩니다
- 섹션 구조와 전체 내용이 포함됩니다
- 바로 복사해서 사용할 수 있는 포맷으로 저장됩니다

#### URL 형식 지원

다음 형식의 URL을 지원합니다:
- `http://wiki.example.com/index.php/PageTitle`
- `http://wiki.example.com/wiki/PageTitle`
- `http://wiki.example.com/index.php?title=PageTitle`

## 주의사항

- `.env` 파일은 보안 정보를 포함하므로 git에 커밋하지 마세요
- `.env` 파일은 이미 `.gitignore`에 포함되어 있습니다