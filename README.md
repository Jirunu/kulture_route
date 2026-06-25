# 🗺️ KultureRoute

<img width="737" height="487" alt="Image" src="docs/screenshots/hero.png" />

&nbsp;

**역사의 결을 따라 걷는, 나만의 문화 여정**

KultureRoute는 서울·경기 지역의 문화유산 명소를 추천하고 동선을 짜주는 AI 문화여행 플랫폼입니다.
</br>
설문 기반 AI 추천과 실시간 날씨, 카카오맵 동선 안내를 통해 삼국시대부터 현대까지 흩어진 문화 명소를 누구나 쉽게 하루 코스로 묶어 떠날 수 있습니다.

<br/>

## 📌 프로젝트 개요

-   **프로젝트명**: KultureRoute
-   **개발 기간**: 2026.06 ~ 진행 중 _(정확한 스프린트 기간으로 교체해 주세요)_
-   **팀 구성**: 서울 6반 1조 _(정확한 인원수로 교체해 주세요)_
-   **목표**: 흩어진 문화유산 정보를 한 곳에 모아, 취향과 날씨에 맞는 동선을 자동으로 짜주는 서비스

<br/>

## 🐿 서비스 특징

-   설문 기반 AI 추천 + 날씨 연동 실내/실외 장소 추천
-   카카오모빌리티(자동차)·OSRM(도보/자전거) 실제 도로 경로 기반 동선 생성
-   "오늘의 여행" 저니 모드 — 장소를 한 화면에 하나씩, 실시간 AI 해설사 "나리"와 함께 이동
-   방문 기록(발자취) 기반 칭호(Badge) 20종 수집 시스템
-   커뮤니티 공유 코스 + 좋아요·댓글, 칭호·닉네임 기반 소셜 기능

<br/>

## 👥 팀 소개

|                       박진우                       |                       장선형                     |                       공통                       |
| :----------------------------------------------------: | :----------------------------------------------------: | :----------------------------------------------------: |
|                          팀장                           |                          팀원                           |                          공통                           |
|                  Backend, AI 프롬프팅                  |                 Frontend, 지도/동선                  |               데이터 수집, 배포(PythonAnywhere)         |
|    |

### 🤝 역할 분담

<br/>

**박진우 (팀장)**

-   설문·AI 추천, 동선 최적화, 칭호(Badge) 시스템
-   `culture/`, `accounts/` 앱 모델링 및 API 설계
-   Gemini 프롬프트 엔지니어링(AI 해설사 "나리", 여행 스토리텔링)

**장선형 (팀원)**

-   메인 SPA(설문·지도·동선·저니 모드) 프론트엔드
-   카카오맵/카카오모빌리티 연동, 커뮤니티 코스 페이지

**공동 (팀원)**

-   장소 데이터 수집·정제(공공데이터/TourAPI), 칭호 데이터 시드
-   PythonAnywhere 배포 및 운영

<br/>

## 🛠 기술 스택

### Backend

![Django](https://img.shields.io/badge/DJANGO-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO_REST_FRAMEWORK-A30000?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLITE-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

### Frontend

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JAVASCRIPT-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

> 별도 프레임워크 없이 순수 HTML/CSS/JS로 구현 (Django 템플릿 기반 SPA)

### AI & API

![Gemini](https://img.shields.io/badge/GOOGLE_GEMINI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![Kakao](https://img.shields.io/badge/KAKAO_MAP-FFCD00?style=for-the-badge&logo=kakao&logoColor=black)
![KakaoMobility](https://img.shields.io/badge/KAKAO_MOBILITY-FFCD00?style=for-the-badge&logo=kakao&logoColor=black)
![OSRM](https://img.shields.io/badge/OSRM-7EBC6F?style=for-the-badge)
![OpenWeather](https://img.shields.io/badge/OPENWEATHER_API-EB6E4B?style=for-the-badge)
![TourAPI](https://img.shields.io/badge/한국관광공사_TourAPI-0072CE?style=for-the-badge)

### Auth

![Kakao](https://img.shields.io/badge/KAKAO_LOGIN-FFCD00?style=for-the-badge&logo=kakao&logoColor=black)
![Naver](https://img.shields.io/badge/NAVER_LOGIN-03C75A?style=for-the-badge&logo=naver&logoColor=white)
![Google](https://img.shields.io/badge/GOOGLE_LOGIN-4285F4?style=for-the-badge&logo=google&logoColor=white)

### Tools & Deploy

![Git](https://img.shields.io/badge/GIT-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GITHUB-181717?style=for-the-badge&logo=github&logoColor=white)
![PythonAnywhere](https://img.shields.io/badge/PYTHONANYWHERE-1D9FD7?style=for-the-badge)

<br/>

## 💻 개발 환경

-   **Python**: 3.12+
-   **Django**: 5.2.14
-   **Django REST Framework**: 3.17.1
-   **django-environ**: 0.13.0
-   **openai** (Gemini OpenAI 호환 엔드포인트): 1.109.1
-   **Pillow**: 12.2.0
-   **requests**: 2.34.2

<br/>

## 📂 프로젝트 구조

```
culture_route/
├── manage.py
├── requirements.txt
├── .env                          # API 키 등 환경변수 (git 미포함)
│
├── config/                       # 프로젝트 설정
│   ├── settings.py
│   ├── urls.py
│   └── context_processors.py     # KAKAO_JS_KEY 템플릿 컨텍스트
│
├── culture/                       # 장소·동선·커뮤니티
│   ├── models.py                 # Place, Theme, Route(path_data), RoutePlace, Review, Bookmark 등
│   ├── views.py                  # AI 추천, 동선 최적화, 실제 경로 계산, 날씨 연동
│   ├── serializers.py
│   ├── urls.py
│   └── management/commands/
│       ├── reset_community_data.py   # 데모 유저·공유 코스 일괄 재생성
│       ├── backfill_route_paths.py   # 공유 코스 실제 이동 경로 계산
│       ├── set_websites.py           # 장소별 공식 홈페이지 URL 일괄 등록
│       └── assign_themes.py          # 시대 테마 자동 분류
│
├── accounts/                      # 회원·칭호·소셜 로그인
│   ├── models.py                 # Profile(닉네임·대표칭호), UserFollow
│   ├── badges.py                  # 칭호 20종 정의 및 집계 로직
│   ├── views.py                  # 회원가입/로그인/프로필/간편 로그인(카카오·네이버·구글)
│   └── management/commands/
│       ├── create_legend_account.py  # 칭호 20개 전부 달성한 데모 superuser 생성
│       └── seed_demo_footprints.py   # 데모 유저 발자취 시드
│
├── ai/                            # AI 챗봇·스토리텔링
│   └── views.py                  # Gemini 연동 chat/guardrail/route-story
│
├── templates/                     # Django 템플릿(=프론트엔드 페이지)
│   ├── landing.html               # 랜딩
│   ├── survey.html                # 설문
│   ├── app.html                   # 메인 SPA (지도·동선·저니 모드)
│   ├── places.html / place_detail.html
│   ├── routes.html                # 커뮤니티 공유 코스
│   ├── profile.html               # 프로필·칭호·발자취
│   └── chat_widget.html           # 플로팅 AI 챗봇 "나리"
│
└── frontend/css/                  # 페이지별 스타일시트
```

<br/>

## 🖨 ERD

<img width="1344" height="913" alt="ERD" src="ERD.png" />

<br/>

## 🎨 화면 설계

### 플로우차트

<img width="3757" height="1779" alt="플로우차트" src="docs/screenshots/flowchart.png" />

### 와이어프레임

<img width="790" height="832" alt="와이어프레임" src="docs/screenshots/wireframe.png" />

<br />

## 💡 핵심 기능 상세 설명

### 1. 🤖 AI 기반 맞춤 동선 추천

#### 규칙 기반 스코어링 (`culture/views.py`)

```python
def _rank_candidates(candidates, eras, categories, duration_type, companions, purpose, interests):
    # 시대·카테고리·동행·목적·실내외·입장료 조건을 점수화해 상위 10곳을 추려
    # Gemini가 그중 적합한 순서로 다듬도록 후보를 좁히는 1차 필터
    score = 0
    if eras and era in eras:
        score += 4
    if categories and p.category in categories:
        score += 3
    if duration_type == 'short' and p.is_indoor:
        score += 2
    if companions == 'family' and p.entrance_fee == 0:
        score += 1
    ...
```

#### 동선 범위(반경) 자동 산정

설문에는 더 이상 "동선 범위" km 입력이 없습니다. 소요시간과 이동수단으로부터 서버가 직접 계산합니다.

```python
def _auto_radius_km(duration_hours, transport='walk'):
    """소요시간 중 약 40%를 이동에 쓴다고 가정해 탐색 반경(지름)을 추정한다.
    최종 동선의 적합성은 _trim_by_time_budget()의 시간 예산 검사가 별도로 보장한다."""
    speed_kmh = _REC_TRANSPORT_SPEED_KMH.get(transport, _REC_TRANSPORT_SPEED_KMH['walk'])
    estimated = speed_kmh * duration_hours * 0.4
    return max(_AUTO_RADIUS_MIN_KM, min(_AUTO_RADIUS_MAX_KM, estimated))
```

### 2. 🧭 실제 도로 기준 동선 최적화

#### 최단 동선 (방문 순서) 계산

```python
def _shortest_route(places):
    """총 이동거리가 최소인 방문 순서 반환. N≤8 완전탐색, N>8 최근접 이웃 휴리스틱."""
    if len(places) <= 8:
        return min(permutations(places), key=total_dist)
    # 모든 시작점에서 최근접 이웃 탐색 후 가장 짧은 경로 선택
    ...
```

#### 공유 코스 생성 시점에 실제 경로를 1회 계산해 저장

커뮤니티에서 코스를 조회할 때마다 외부 API를 다시 호출하지 않도록, 코스 생성/수정 시점에 **자동차는 카카오모빌리티, 도보·자전거는 OSRM**으로 실제 도로를 따라가는 좌표를 계산해 `Route.path_data`에 저장합니다.

```python
def compute_route_path(ordered_places, transport_mode):
    for a, b in zip(ordered_places, ordered_places[1:]):
        if transport_mode == 'car':
            result = _kakao_directions_leg(origin, destination)
        elif transport_mode in _OSRM_PROFILE:
            result = _osrm_route_leg(origin, destination, _OSRM_PROFILE[transport_mode])
        # 실패하거나 대중교통/기차처럼 지원하지 않는 수단은 직선 좌표로 대체
```

### 3. 🏅 칭호(Badge) 수집 시스템

#### 발자취 기반 집계 (`accounts/badges.py`)

```python
def _compute_badge_stats(target):
    # is_footprint=True인 Route에 포함된 장소들을 카테고리·지역·시대·키워드로 집계
    palace_cat = [p for p in places if p.category == 'palace']
    temple = sum(1 for p in palace_cat if _is_temple(p.name))   # 이름 패턴으로 궁궐/사찰 구분
    return {
        'total': len(places), 'seoul': seoul, 'gyeonggi': gyeonggi,
        'era_joseon': era_counts.get('joseon', 0), ...
    }
```

대표 칭호는 `selected_badge`에 저장되지만, 조회할 때마다 **실제 달성 여부를 재검증**해 달성하지 못한 칭호는 절대 노출되지 않습니다.

### 4. 🗣 AI 해설사 "나리"

저니 모드에서는 현재 보고 있는 장소 정보를 함께 전달해, "여기 뭐야?" 같은 질문에도 그 장소를 기준으로 답합니다.

```python
def _build_place_context(place):
    lines = [f'[현재 위치] 사용자는 지금 여행 중 "{place["name"]}"을 보고 있다.']
    if place.get('description'):
        lines.append(f'장소 설명: {place["description"][:300]}')
    lines.append('사용자가 이 장소나 "여기"·"이곳"에 대해 물으면 위 정보를 바탕으로 자세히 설명하라.')
    return '\n\n' + '\n'.join(lines)
```

<br/>

## 📝 코드 컨벤션

<details>
<summary><b>Backend (Python/Django)</b></summary>

### 네이밍 규칙

-   **변수/함수**: snake_case
    ```python
    visit_min = VISIT_MIN.get(place.category, _DEFAULT_VISIT_MIN)
    def _auto_radius_km(duration_hours, transport='walk'):
        pass
    ```
-   **클래스**: PascalCase
    ```python
    class RoutePlace(models.Model):
        pass
    ```
-   **내부 전용 함수/상수**: 언더스코어 프리픽스
    ```python
    def _haversine_km(p1, p2):
        pass
    _AUTO_RADIUS_MIN_KM = 4
    ```

</details>

<details>
<summary><b>Frontend (Vanilla JS)</b></summary>

### 네이밍 규칙

-   **변수/함수**: camelCase
    ```javascript
    const currentRoutePlaces = [];
    function reloadAIRecommend(isRetry = false) {}
    ```
-   **localStorage 키**: `cr_` 프리픽스 + snake_case
    ```javascript
    localStorage.setItem('cr_active_route_places', JSON.stringify(places));
    ```

</details>

<details>
<summary><b>Git Commit Convention</b></summary>

### Commit Message 형식

```
<type>: <subject>

<body>
```

### Type 종류

-   `feat`: 새로운 기능 추가
-   `fix`: 버그 수정
-   `docs`: 문서 수정
-   `style`: 코드 포맷팅, 마크업/스타일 조정
-   `refactor`: 코드 리팩토링
-   `chore`: 빌드/설정, 데이터 시드 등

### 예시

```
feat: 공유 코스 생성 시 실제 이동 경로를 계산해 저장

- 카카오모빌리티(자동차)·OSRM(도보/자전거) 연동
- 조회 시점 재호출 없이 저장된 path_data로 곡선 경로 표시
```

</details>

<br/>

## 🚀 설치 및 실행 방법

<details>
<summary><b>1. 저장소 클론</b></summary>

```bash
git clone https://github.com/Jirunu/kulture_route.git
cd kulture_route
```

</details>

<details>
<summary><b>2. 가상환경 및 패키지 설치</b></summary>

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

</details>

<details>
<summary><b>3. 환경변수 설정 (.env 파일 생성)</b></summary>

아래 "환경변수 설정" 섹션 참고

</details>

<details>
<summary><b>4. 데이터베이스 마이그레이션</b></summary>

```bash
python manage.py migrate

# 데모 데이터(유저·공유 코스)가 필요하면
python manage.py reset_community_data
```

</details>

<details>
<summary><b>5. 서버 실행</b></summary>

```bash
python manage.py runserver
```

-   **접속**: http://localhost:8000

</details>

<br/>

## 🔑 환경변수 설정 (.env)

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 한국관광공사 TourAPI
PUBLIC_DATA_API_KEY=your_public_data_api_key
# OpenWeatherMap
OPENWEATHER_API_KEY=your_openweather_api_key
# Kakao Map / Mobility
KAKAO_JS_KEY=your_kakao_js_key
KAKAO_REST_KEY=your_kakao_rest_key
# Google Gemini (OpenAI 호환 엔드포인트)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_IMAGE_MODEL=imagen-3.0-generate-002



<br/>

## 🎬 주요 기능 시연

### 1. 설문 & AI 추천

<details>
<summary><b>취향 설문 & 맞춤 동선 추천</b></summary>

![설문](docs/screenshots/survey.png)

-   거주 지역·관심 분야·선호 시대·동행·목적 6단계 설문
-   날씨·소요시간·이동수단을 반영한 AI 추천

![AI 추천 동선](docs/screenshots/recommend.png)

-   추천 동선 드래그로 순서 변경
-   "↺ 재추천"으로 최대 3회까지 다른 동선 받기

</details>

### 2. 지도 & 동선

<details>
<summary><b>카카오맵 실제 경로 동선</b></summary>

![동선 지도](docs/screenshots/route_map.png)

-   자동차: 카카오모빌리티 실제 도로 경로
-   도보/자전거: OSRM 실제 경로
-   이동수단별 예상 소요시간·거리 표시

</details>

### 3. 오늘의 여행 (저니 모드)

<details>
<summary><b>한 화면에 한 장소씩, AI 해설사와 함께</b></summary>

![저니 모드](docs/screenshots/journey.png)

-   장소별 사진·소개·운영시간, 다음 장소 미리보기
-   실시간 AI 해설사 "나리"에게 현재 장소 질문 가능
-   발자국 남기기(방문 체크) + 메모

![여행 마무리](docs/screenshots/journey_wrapup.png)

-   방문한 장소 별점 등록
-   코스 저장·공유 또는 발자취만 기록하고 종료

</details>

### 4. 칭호(Badge) & 프로필

<details>
<summary><b>발자취 기반 칭호 수집</b></summary>

![칭호](docs/screenshots/badges.png)

-   방문 기록으로 자동 집계되는 칭호 20종
-   대표 칭호 설정 시 닉네임 옆에 노출

</details>

### 5. 커뮤니티

<details>
<summary><b>공유 코스 탐색 & 좋아요·댓글</b></summary>

![커뮤니티](docs/screenshots/community.png)

-   소요시간·이동수단·지역 필터링
-   좋아요·댓글, 지도로 코스 미리보기

</details>

### 6. 간편 로그인

<details>
<summary><b>카카오 · 네이버 · 구글 로그인</b></summary>

![간편 로그인](docs/screenshots/social_login.png)

-   Authorization Code 방식, SDK 없이 직접 토큰 교환
-   미설정 시에도 에러 없이 안전하게 폴백

</details>

<br/>

## 🐛 트러블슈팅

### 1. PythonAnywhere 무료 플랜의 아웃바운드 인터넷 제한

**문제**: 로컬에서는 카카오모빌리티·OSRM 실제 경로가 잘 나오는데, PythonAnywhere에 배포하니 전부 직선 거리로만 표시됨

**원인**: PythonAnywhere 무료(Beginner) 플랜은 화이트리스트에 없는 도메인으로는 아웃바운드 요청이 막힘. `apis-navi.kakaomobility.com`, `router.project-osrm.org`가 화이트리스트에 없어 요청이 실패하고, 코드가 실패를 조용히 직선 거리로 폴백하던 것이었음

**해결**: 유료 플랜으로 업그레이드해 화이트리스트 제한을 해제. (무료 플랜을 유지해야 한다면 해당 기능은 사실상 동작 불가)

### 2. Gemini 무료 티어 일일 쿼터 초과

**문제**: AI 해설사 챗봇이 응답하지 않음

**원인**: 챗봇 1회 질문마다 적절성 검사(guardrail) + 답변 생성, 총 2번씩 Gemini를 호출하는 구조라, 여러 AI 기능이 같은 키의 하루 20회 무료 쿼터를 빠르게 소진함

**해결**: 쿼터 초과 시 503을 반환하도록 이미 처리돼 있어 에러 없이 폴백되지만, 테스트 시 하루 호출량을 염두에 두고 모델/쿼터 한도를 문서화

```python
def _get_ai_client():
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return None
    return _oai.OpenAI(api_key=api_key, base_url=settings.GEMINI_BASE_URL)
```

### 3. `DEBUG=False`에서 프로필 사진이 안 보임

**문제**: 로컬에서는 잘 보이던 프로필 사진이 배포 후 전부 깨짐

**원인**: `config/urls.py`가 `DEBUG=True`일 때만 `MEDIA_URL`을 서빙하도록 되어 있어, 배포 환경(`DEBUG=False`)에서는 Django가 미디어 파일을 직접 서빙하지 않음

**해결**: PythonAnywhere의 Static files 설정에 `/media/` → `media/` 디렉터리 매핑을 추가로 등록

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 4. 저니 모드 챗봇 아바타가 깨진 듯 크게 표시됨

**문제**: 인라인 AI 해설사 대화창에서 메시지마다 붙는 캐릭터 이미지가 비정상적으로 크게 나옴

**원인**: 헤더용 아바타(`.jchat-avatar-header`)에만 크기 CSS가 정의돼 있고, 말풍선용 아바타 클래스(`.jchat-avatar`)에는 스타일이 누락되어 1536×1024 원본 이미지가 그대로 렌더링됨

**해결**: 누락된 CSS 규칙 추가

```css
.jchat-avatar {
  width: 24px; height: 24px; border-radius: 50%;
  object-fit: cover; object-position: center 15%;
  border: 1px solid rgba(240,199,94,.5);
}
```

### 5. 설문을 새로 해도 예전 동선이 그대로 복원됨

**문제**: 설문을 처음/다시 완료했는데 추천 동선에 깨진 거리 값(수만 km)이 그대로 표시됨

**원인**: `app.html`이 페이지 진입 시 `localStorage`에 저장된 이전 동선(`cr_active_route_places`)을 항상 복원하는데, 새 설문 제출 시 이 값을 지우지 않아서 오래된/잘못된 데이터가 그대로 살아남음

**해결**: 설문 저장 성공 시 관련 `localStorage` 키를 전부 정리하도록 수정

```javascript
localStorage.removeItem('cr_active_route_places');
localStorage.removeItem('cr_journey_ids');
```

<br/>

## 📚 배운 점 & 느낀 점

### 기술적 성장

-   **외부 API 연동 경험**: 카카오맵/모빌리티, OSRM, Gemini, TourAPI 등 다양한 외부 API를 한 서비스에 통합
-   **AI 프롬프트 엔지니어링**: 캐릭터 페르소나("나리")를 유지하면서 컨텍스트(현재 장소 정보)를 주입해 답변 품질을 높이는 경험
-   **배포 환경 차이 대응**: 로컬과 PythonAnywhere의 네트워크·정적 파일 서빙 차이를 직접 겪고 원인을 추적
-   **데이터 모델링**: 발자취 기반 칭호 집계처럼 여러 모델을 가로지르는 통계 로직 설계

### 협업 & 프로젝트 관리

-   **점진적 개선**: 기능을 만들고 끝이 아니라, 실제 사용해보며 UX 디테일(아코디언 박스, 색상, 문구)을 계속 다듬는 과정의 중요성 체감
-   **문서화**: CLAUDE.md로 기능·API·DB 현황을 계속 최신화하며 협업 효율 확보

<br/>

## 🔮 향후 개선 사항

-   [ ] 대중교통/기차 구간의 실제 경로(곡선) 지원
-   [ ] 리뷰 이미지 직접 업로드 (현재는 URL 입력만 지원)
-   [ ] 개별 장소 단위 발자취 기록 (현재는 완료한 동선 전체 단위로만 기록)
-   [ ] 닉네임 변경 이력 관리

<br/>

---

<div align="center">

**역사의 결을 따라 걷는, 나만의 문화 여정**

Made by 서울 6반 1조

</div>
