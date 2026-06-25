# KultureRoute — CLAUDE.md

서울·경기 문화명소 추천 Django 웹앱. 설문 기반 AI 추천 + 카카오맵 동선 + 장소 목록/상세/커뮤니티 + 여행 떠나기(저니 모드) + 칭호 시스템.

---

## 기술 스택

- **Backend**: Django 5.2 + Django REST Framework, SQLite
- **Frontend**: 순수 HTML/CSS/JS (프레임워크 없음)
- **지도**: Kakao Maps JS API (`autoload=false` → `kakao.maps.load(callback)` 패턴)
- **배포**: PythonAnywhere (`/home/cultureroute/culture_route/`)
- **GitHub**: https://github.com/Jirunu/kulture_route.git (private) — 2026-06-24 신규 저장소로 이전, `night.gif`(145MB) 등 대용량 파일을 `git filter-repo`로 히스토리에서 제거 후 push함

---

## 환경 변수 (.env — 절대 커밋 금지)

```
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=cultureroute.pythonanywhere.com

PUBLIC_DATA_API_KEY=...   # 한국관광공사 TourAPI (일일 쿼터 있음)
OPENWEATHER_API_KEY=...
KAKAO_JS_KEY=...
KAKAO_REST_KEY=...
GEMINI_API_KEY=...                          # Google Gemini API, 무료 티어 (미입력 시 ai/ 503 반환)
GEMINI_MODEL=gemini-2.5-flash-lite           # 미설정 시 기본값 (gemini-2.5-flash는 무료 일일 쿼터 20회로 매우 적음)
GEMINI_IMAGE_MODEL=imagen-3.0-generate-002   # 미설정 시 기본값 (무료 티어 미지원 가능, 실패 시 503)

# 간편 로그인 — 카카오는 KAKAO_REST_KEY를 client_id로 재사용(Kakao Developers에서 "카카오 로그인" 활성화 필요)
KAKAO_CLIENT_SECRET=...   # Kakao Developers에서 Client Secret 활성화한 경우만 필요, 기본은 비워둠
NAVER_CLIENT_ID=...       # Naver Developers
NAVER_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...      # Google Cloud Console OAuth 2.0 클라이언트
GOOGLE_CLIENT_SECRET=...
```

**소셜 로그인 Redirect URI 등록값** (각 콘솔에 정확히 등록해야 함):
- 카카오: `http://localhost:8000/api/accounts/social/kakao/callback/` (배포 시 도메인 교체)
- 네이버: `http://localhost:8000/api/accounts/social/naver/callback/`
- 구글: `http://localhost:8000/api/accounts/social/google/callback/`

클라이언트 ID/Secret을 비워두면 해당 버튼 클릭 시 `/login/?social_error=<provider>`로 안전하게 폴백된다(에러 없이 동작).

---

## DB 현황 (로컬 기준)

| 항목 | 수 |
|------|-----|
| Place 전체 | 530 |
| 관련 URL 등록 | 315 / 530 |
| 역사유적 | 279 |
| 박물관·미술관 | 102 |
| 궁궐·사찰 (category=`palace`, 이름 패턴으로 궁궐/사찰 구분) | 149 |
| 서울 | 212 |
| 경기 | 318 |
| Theme | 5 (삼국·고려·조선·일제·현대, `assign_themes` 영향으로 조선 비중 압도적) |
| User | `master`(관리자) + `user001`~`user100`(데모 유저, 아래 참고) + 수동 테스트 계정 일부 |
| Route | 공유 코스(`is_shared`) 약 96개 + 발자취(`is_footprint`) 약 117개 — `reset_community_data`로 재생성 가능 |
| Review / Bookmark / RouteComment / RouteLike | `reset_community_data` 실행 시마다 갱신되는 데모 데이터(고정값 아님) |

장소(Place·Theme) 데이터는 위 시드 스크립트들이 절대 건드리지 않는 원본 데이터다. 유저/코스/리뷰 등 "사람이 만든" 데이터만 초기화·재생성 대상.

---

## 구현된 전체 기능

### 설문 & 추천 (`templates/app.html`)
- **설문 수정 모달**: 프로필 카드 "✎ 수정" 버튼 → 6단계 설문 한 화면에 표시 → 저장 후 즉시 반영
- **AI 추천 (규칙 기반)**: `_rank_candidates()` (`culture/views.py`) — 시대·카테고리·동행·목적·실내외·입장료 점수 → 상위 5개
- **동선 재추천**: "↺ 재추천" 버튼 클릭 시 `reloadAIRecommend(true)`로 `retry:true` 전송 → 서버가 세션에 누적된 이전 추천 장소를 전부 제외하고 새로 추천. 최대 3회까지 가능, 4회차부터는 "더 이상 새로운 추천이 없습니다" 표시. 설문 저장/초기화 시 재추천 기록도 함께 리셋
- **설문 페이지 돌아가기**: `templates/survey.html` 좌측 상단 "← 돌아가기" 버튼 → `/` 메인 페이지로 이동

### 지도·동선 (`templates/app.html`)
- **동선 범위(반경)는 유저 입력이 아니라 AI가 자동 산정**: 설문에서 km 슬라이더는 제거됨. `culture/views.py`의 `_auto_radius_km(duration_hours, transport)`가 소요시간×이동수단 평균속력의 약 40%를 후보 탐색 반경(지름, 4~40km로 clamp)으로 계산해 `ai_recommend()` 내부에서만 사용. 최종 동선의 적합성은 별도로 `_trim_by_time_budget()`(관람시간+이동시간 합이 소요시간을 넘으면 트림)이 보장
- **최단 동선 최적화**: `_shortest_route()` — N≤8 완전탐색(itertools.permutations), N>8 nearest-neighbor
- **카카오모빌리티 실제 경로**: `POST /api/places/route-directions/` — 구간별 자동차 길찾기(`apis-navi.kakaomobility.com`) 호출, 도로를 따라가는 polyline + 실거리/실시간 표시. 구간 호출 실패 시 해당 구간만 직선 거리로 대체(`ok:false`) 후 상태 알림(`#route-directions-status`)에 안내. 생성 직후엔 직선 임시선 → 실제 경로 도착 시 자동 교체
- **장소 순서 드래그 변경**: 동선 리스트 항목에 드래그 핸들(`⠿`), HTML5 `draggable`로 순서 변경 시 마커 번호·polyline·총 거리/시간을 즉시 재계산(`reorderRoutePlaces()`)
- **방문 여부 표시**: 동선 리스트의 각 장소명 옆에 "✓ 방문함" 배지 — `/api/places/visited-ids/`로 로그인 유저의 발자취 장소 id를 로드해 표시
- **이동수단 선택**: 도보/대중교통/자전거/자동차 버튼(`#transport-select`) — 자동차는 카카오모빌리티 실제 경로, 나머지는 `/api/places/route-transit-info/`(Gemini)로 구간별 예상 시간·구체적 이동방법(지하철 호선 등)을 받아 동선 리스트 구간 표시를 갱신(`setTransportMode()`/`loadTransitInfo()`)
- **장소 직접 추가**: 동선 결과 화면 하단 "+ 장소 추가" 버튼 → 검색 모달(`#add-place-modal`, `/api/places/?q=` 재사용) → 선택 시 `currentRoutePlaces` 맨 뒤에 추가, 마커·polyline·이동정보 즉시 재계산. 드래그로 순서도 바로 재배치 가능
- **동선 저장/공유**: 동선 생성 화면에는 별도 저장 버튼이 없고, "▶ 여행 떠나기"로 저니를 시작해 마무리 화면까지 가야 저장·공유할 수 있다(아래 "여행 떠나기 / 오늘의 여행" 절 참고). `.save-route-btn`/`이 동선 저장하기` 관련 코드는 과거 UI의 잔재로 현재 렌더링되는 버튼은 없음(죽은 코드)
- **동선 생성 상태 유지**: 동선 생성 시 `currentRoutePlaces`를 `localStorage('cr_active_route_places')`에 저장 → 다른 페이지 갔다와도 `restoreActiveRoute()`가 자동 복원 (장소 다시 선택/재추천 시 클리어, **설문을 새로 제출할 때도 `templates/survey.html`의 `submitSurvey()`가 이 키를 비워 이전 동선이 복원되지 않도록 함**)
- **공유 코스의 실제 경로는 생성 시점에 1회 계산해 저장**: `/api/routes/` POST(생성) 또는 PUT(place_ids·transport_mode 변경 시) 시 `culture/views.py`의 `_save_route_path()` → `compute_route_path()`가 자동차=카카오모빌리티, 도보/자전거=OSRM(대중교통/기차는 직선)으로 구간별 좌표를 계산해 `Route.path_data`(JSONField)에 저장. 커뮤니티에서 코스를 조회할 때는 이 저장된 좌표로 즉시 곡선 경로를 그리며, 조회 시점에 외부 API를 다시 호출하지 않음(`templates/routes.html`의 `routePolylinePath()`). 과거에 만든 코스는 `python manage.py backfill_route_paths`로 일괄 채움

### 여행 떠나기 / 오늘의 여행 (저니 모드) (`templates/app.html`)
- **진입**: 동선 생성 후 "▶ 여행 떠나기" 버튼, 또는 모든 페이지 Nav의 **"여행 떠나기"** 강조 버튼(금색 사각형, 커뮤니티보다 앞 배치) → `/app/?go=journey`
  - `go=journey` 쿼리 + 저장된 활성 동선 + 진행 중인 저니(`cr_journey_ids` 일치) 가 있으면 자동으로 저니 화면을 염
  - `/app/`는 설문 미완료 시 서버에서 `/survey/`로 자동 리다이렉트되므로 별도 분기 불필요
- **화면 구성**: 장소를 한 번에 다 보여주지 않고 **한 화면에 한 장소씩** 스텝 형식으로 진행
  - 큰 사진 + 장소명·태그(카테고리/지역/실내외/관람시간/입장료)·운영시간·소개·공식 홈페이지 링크
  - 옆(또는 모바일에서 아래)에 **다음 장소 미리보기** 카드 — 사진·이름·태그 + 이동수단/거리/예상 소요시간(haversine 기반)
  - 다음 장소 카드 아래 **"실시간 AI 해설사 · 나리"** 인라인 챗봇 (`/api/ai/chat/` 연동, 단계 이동해도 대화 로그 유지)
  - "👣 발자국 남기기" 토글로 방문 체크, 메모 입력
  - 하단 "‹ 이전 장소" / "다음 장소 →" 내비게이션, 마지막 장소에서는 "여행 마무리 →"로 전환
  - 진행 단계는 `localStorage('cr_journey_step')`로 저장되어 페이지 이탈 후에도 같은 자리에서 재개됨
- **마무리 화면**: "‹"(화살표만, 텍스트 없음) 버튼으로 마지막 장소 재방문, 방문 체크한 장소별 별점 즉시 등록(`/api/places/<id>/reviews/`)
  - 모달 없이 `.wrapup-actions` 바로 아래에 **인라인 아코디언 박스**가 펼쳐지는 방식(과거의 별도 저장 모달은 삭제됨)
  - **"↑ 코스 저장 및 공유하기"** 클릭 → `toggleWrapupSaveBox()`로 코스 이름 입력 + 공유 여부 체크박스 + "저장하기" 버튼이 담긴 `#wrapup-save-box`가 펼쳐짐(다시 클릭하면 닫힘). 제출 성공 시(`submitSaveRoute()`) 자동으로 발자취 기록 + 설문 초기화 + 메인 화면(`/`)으로 이동
  - **"여행 끝내기"** 클릭 → `toggleWrapupEndConfirm()`로 "정말 종료하시겠습니까?" 확인 문구 + "네, 종료할게요" 버튼이 담긴 `#wrapup-end-confirm-box`가 펼쳐짐(다시 클릭하면 닫힘). 확인 버튼을 눌러야 실제로 `endJourney()`가 실행되어 저장 없이 발자취 기록 + 설문 초기화 + **메인 화면(`/`)**으로 이동
  - 두 아코디언 박스는 상호 배타적(하나가 열리면 다른 하나는 자동으로 닫힘)
  - 저장/종료가 완료되면 `cr_active_route_places`/`cr_journey_*` localStorage 전부 삭제
- **발자취 자동 기록**: 여행 종료 시 `currentRoutePlaces`를 `Route(is_footprint=True, is_shared=False)`로 자동 생성 (`POST /api/routes/`, `is_footprint:true`) — "저장한 코스"와는 별도 데이터
- **플로팅 챗봇 숨김**: 저니 화면이 열려 있는 동안에는 우측 하단 플로팅 AI 챗봇(`chat_widget.html`)을 숨기고, 닫으면 다시 보이게 처리

### AI 캐릭터 "나리" (`character.png`)
- 갓·한복을 입은 로봇 캐릭터. 챗봇/대화 기능 전반의 페르소나로 사용 — 플로팅 위젯(`chat_widget.html`)과 저니 모드 인라인 챗봇(`templates/app.html`)에 아바타·이름 노출. 둘 다 같은 `/api/ai/chat/`을 호출하며, 별도의 전용 챗봇 페이지 템플릿은 없음
- 이미지: `culture/static/culture/images/character.png` → `{% static 'culture/images/character.png' %}`
- `ai/views.py`의 `CHAT_SYSTEM_PROMPT`에 "나리" 페르소나(이름·캐릭터 설정) 반영 — 실제 답변에도 자신을 나리라 칭함
- **플로팅 챗봇 위치**: `chat_widget.html`의 `positionWidgetPanel()` — 기본값은 캐릭터(`#chat-fab`) **우측 상단**(`fabRect.right + 12`)에 패널을 띄움. 화면 우측 공간이 부족하면 자동으로 좌측으로 보정(반응형). 캐릭터 자체는 드래그로 위치 이동 가능하고 `localStorage('cr_chat_fab_pos')`에 저장됨

### 칭호(Badge) 시스템 (`accounts/badges.py`, `accounts/models.py`)
- **집계 기준**: `RoutePlace(route__is_footprint=True, route__user=대상)`에 포함된 장소들을 카테고리/지역/시대(Theme.era)/이름·설명 키워드로 집계
- **칭호 20종** (쉬움→어려움, `accounts/badges.py`의 `BADGE_DEFS`에 정의):
  - 아주 쉬움: 첫 발걸음(1곳), 고려 충신(고려 유적 2곳)
  - 쉬움: 삼국시대 덕후(4), 동네 산책러(5곳), 전쟁광(전쟁 키워드 4곳), 모던 컬처 헌터(현대 6)
  - 보통: 실내파 문화인(12), 햇빛 마니아(실외 15), 박물관은 살아있을지도?(박물관 10), 근현대사 워커(일제 8), 발로 쓰는 역사책(역사유적 20)
  - 어려움: 서울 토박이(15), 경기 유랑자(15), 내 안의 작은 부처(사찰 15), 전생에 왕족이었나?(궁궐 6), 수도권 정복자(서울·경기 각 10), 문화 노마드(15곳)
  - 매우 어려움: 조선왕조 500년 산증인(조선 35), 역사 덕후(30곳), 문화유산 정복자(50곳)
  - 각 칭호에 달성 조건 한 줄(`condition`)이 포함되어 칭호 탭에 그대로 표시됨
  - 궁궐 vs 사찰은 `category='palace'` 안에서 이름 패턴(`_is_temple()`, `move_temples.py`와 동일 로직)으로 구분
- **선택/표시**: `Profile.selected_badge`에 칭호 id 저장. `POST /api/accounts/me/badge/`로 설정/해제 — **실제 earned 여부를 매번 재검증**(`get_badge_info()`)하므로 달성 못 한 칭호는 절대 노출되지 않음
- **난이도 4색**: 노랑(아주 쉬움/쉬움) → 주황(보통) → 빨강(어려움) → 검정(매우 어려움), `TIER_COLOR_KEY` 매핑. 닉네임 옆 칭호 상자(Nav/리뷰/코스 카드/댓글/프로필 헤더) 전부 이 4색만 사용. "대표 칭호로 설정" 버튼은 칭호 색과 무관하게 항상 검정으로 고정
- **공개 범위**: 칭호 탭과 칭호 정보는 **다른 유저 프로필에서도 조회 가능**(`profile_detail`에서 `is_self` 무관하게 항상 계산). "대표 칭호로 설정/해제" 버튼만 본인에게만 노출
- **프로필 탭**: "저장한 코스" 옆에 **"나의 발자취"**(자동 기록된 완료 여행, `is_footprint=True`인 Route) 탭과 **"칭호"** 탭 추가

### 닉네임 (`accounts/models.py` Profile.nickname, `accounts/utils.py`)
- 로그인 아이디(username)는 그대로 유지, 별도 `Profile.nickname` 필드(고유, 2~10자, 한글/영문/숫자만, 공백 불가 — `_validate_nickname()`)로 표시 이름 설정 가능
- `POST /api/accounts/me/nickname/` — `{nickname: str}` (규칙 위반/중복 시 400, 빈 문자열/null이면 닉네임 해제)
- `GET /api/accounts/check-nickname/?nickname=` — 실시간 중복확인, `{available, detail}` 반환 (회원가입 폼에서 0.5초 디바운스로 호출)
- 회원가입(`POST /api/accounts/signup/`) 시 `nickname`을 함께 받아 같은 규칙으로 검증 후 `Profile`까지 한 번에 생성 (선택 입력, 비워두면 username만 사용)
- `get_display_name(user)` 헬퍼: 닉네임 있으면 닉네임, 없으면 username — `/api/accounts/me/`, `profile_detail`, 리뷰/코스/댓글 시리얼라이저(`display_name` 필드)에 전부 반영
- 프론트엔드는 닉네임 표시 위치(Nav, 리뷰, 코스 카드, 댓글, 프로필 헤더) 전부 `display_name || username`으로 렌더링, 단 프로필 URL(`/accounts/profile/<username>/`)은 항상 실제 username 사용
- `templates/profile.html`에 본인용 "닉네임 설정/변경" 인라인 입력 UI 있음

### 프로필 사진 (`accounts/models.py` Profile.profile_image)
- `Profile.profile_image` (ImageField, `upload_to='profiles/'`) — 미설정 시 `get_avatar_url()`이 기본 이미지(`culture/static/culture/images/default_profile.png`) 경로 반환
- `POST /api/accounts/me/profile-image/` — multipart/form-data `{image: file}`, 업로드 후 `{avatar_url}` 반환
- `avatar_url`은 `/api/accounts/me/`·`profile_detail` 응답에 포함되어 Nav 32×32 원형 썸네일(`.nav-avatar`, `common.css`)과 프로필 헤더 큰 사진(`templates/profile.html` `.avatar`)에 공통으로 사용됨
- 프로필 페이지에서 사진 클릭/"사진 변경" 버튼 → 파일 선택 즉시 로컬 미리보기(`URL.createObjectURL`) → "저장" 버튼으로 업로드, "취소" 시 원래 사진으로 복원
- `MEDIA_URL`/`MEDIA_ROOT` 추가(`config/settings.py`), `DEBUG=True`일 때만 Django가 직접 서빙(`config/urls.py`) — 배포 환경에서는 별도 정적 파일 서버 설정 필요
- Pillow 패키지 필요(`requirements.txt`에 추가됨, ImageField 의존성)

### 간편 로그인 (`accounts/views.py`)
- 로그인(`templates/login.html`)·회원가입(`templates/signup.html`) 페이지에 카카오/네이버/구글 버튼
- Authorization Code 방식 OAuth, SDK 없이 `requests`로 직접 토큰 교환 — `SOCIAL_PROVIDERS` 딕셔너리에 제공자별 endpoint/scope/설정키 정의
- 카카오는 Maps용 `KAKAO_REST_KEY`를 client_id로 재사용(Kakao Developers에서 "카카오 로그인" 활성화 + Redirect URI 등록 필요), 네이버·구글은 `NAVER_CLIENT_ID`/`GOOGLE_CLIENT_ID` 등 별도 `.env` 키 필요
- 최초 로그인 시 `username=<provider>_<고유id>`로 User를 get_or_create, 제공자가 내려준 닉네임이 있고 중복이 아니면 `Profile.nickname`에 자동 반영
- CSRF 방지를 위해 `state` 값을 세션에 저장 후 콜백에서 검증, `?next=`로 로그인 후 이동 경로 보존
- 클라이언트 ID 미설정 시 버튼 클릭하면 에러 없이 `/login/?social_error=<provider>`로 이동(로그인 페이지에 안내 문구 표시)

### 장소 목록 (`templates/places.html`)
- 이름 검색 (Enter·버튼·✕), 페이지네이션 (5개 번호 + «‹›»)
- 카드 북마크 버튼 (☆/★) — 로그인 시 내 북마크 상태 자동 로드
- 카드 클릭 시 지도 마커 하이라이트, 마커 클릭 시 카드 스크롤 + 테두리 강조
- **방문 여부 필터**: 전체/방문함/안 가본 곳 — 로그인 시에만 노출(`#visited-filter-wrap`), `RoutePlace(route__is_footprint=True, route__user=요청자)` 기준으로 `/api/places/filter/?visited=true|false` 필터링
- **방문 완료 배지**: 로그인 시 `/api/places/visited-ids/`로 받은 id 목록을 기준으로 카드 우측 상단에 "✓ 방문 완료" 배지 표시(`.visited-badge`), 비로그인이면 표시 안 함

### 장소 상세 (`templates/place_detail.html`)
- **관련 URL**: URL 있으면 `장소명 ↗` 링크, 없으면 `—`
- **북마크 버튼**: 상세 페이지 헤더에서 토글 (로그인 필요)
- **리뷰**: 별점 선택·내용·이미지URL 입력 → 등록, 본인 리뷰 삭제 버튼 표시, 작성자 닉네임/칭호 표시
- **리뷰 더 보기**: 초기 preview 개수 초과 시 "리뷰 더 보기 (N개 더)" 버튼
- **비슷한 장소**: 같은 카테고리 OR 시대 기반 4개 카드 (페이지 하단)
- **설명 더보기/접기**: 120자 이상 소개 축약·펼치기
- **소형 카카오맵**: 장소 위치 마커 + 말풍선

### 커뮤니티 코스 (`templates/routes.html`)
- 코스 목록 (2열 그리드), 좋아요·댓글 — 작성자 옆에 닉네임/칭호 표시
- **코스 만들기 모달**: 제목·모드·장소 선택(체크박스 + 검색필터)·거리·시간·공유여부
- **수정·삭제**: 본인 코스에만 버튼 표시
- **지도 보기 모달**: 코스 장소들을 번호 마커 + Polyline으로 Kakao맵에 시각화

### 프로필 (`templates/profile.html`)
- 탭: 내가 쓴 리뷰 / 북마크한 장소 / 저장한 코스 / **나의 발자취** / **칭호**
- 닉네임 설정 UI, 대표 칭호 설정/해제, 팔로우/팔로잉

### 로딩 (`templates/loading.html`)
- 3.2초 후 `/app/` 자동 이동
- **바로 시작 →** 스킵 버튼으로 즉시 이동 가능

### 데이터 관리 (`python manage.py set_websites`)
URL 등록 우선순위 (이미 URL 있으면 스킵):
1. 공식 홈페이지 (63개 직접 조사)
2. 한국민족문화대백과 encykorea (25개)
3. 대한민국 구석구석 visitkorea (73개)
4. 나머지 → 나무위키 자동 (`urllib.parse.quote(name)`)

---

## 테스트/관리 계정 (로컬)

| 계정 | 비밀번호 | 특징 |
|------|----------|------|
| `master` | `master123` | superuser, 칭호 20개 전부 달성(전체 Place 발자취), 대표 칭호 "문화유산 정복자", 닉네임 `master` |
| `user001` ~ `user100` | `user1234` | 일반 데모 유저 100명 — 닉네임·팔로우·북마크·리뷰·발자취·칭호가 무작위로 채워진 상태 |

위 계정들은 **장소(Place·Theme) 데이터는 그대로 두고 유저 관련 데이터만 전부 삭제 후 재생성**하는 아래 명령으로 만들어진다(반복 실행 가능, 매번 새로 시드됨):
```bash
python manage.py reset_community_data            # --users 100 --routes 90 옵션으로 개수 조절 가능
```
내부적으로 다음을 순서대로 수행:
1. `User.objects.all().delete()` — CASCADE로 Profile/Review/Route/Bookmark/RouteLike/RouteComment/UserFollow까지 함께 삭제 (Place는 User를 참조하지 않으므로 영향 없음)
2. `create_legend_account --username master --password master123` 호출 — 칭호 20개 전부 달성한 관리자 계정 생성
3. 일반 유저 100명 생성 + 팔로우/북마크/리뷰를 무작위로 채움
4. **공유 코스 90개** 생성 — 지리적으로 가까운 장소 3~6곳을 `_shortest_route()`로 순서를 정하고, 이동수단별 굴곡 보정(직선거리×1.15~1.35)으로 거리를 추정해 도보/자전거/대중교통/자동차 중 동선 폭에 맞는 이동수단을 자동 배정. 댓글·좋아요도 무작위로 채움
5. `seed_demo_footprints` + `backfill_route_paths` 호출 — 발자취/칭호와 공유 코스의 실제 곡선 경로(`path_data`)까지 한 번에 채움

칭호 20개 전부 달성한 단일 superuser만 따로 다시 만들고 싶을 때:
```bash
python manage.py create_legend_account --username 원하는ID --password 원하는비번
```

기존 유저들에게 칭호가 보이도록 데모 발자취만 뿌리는 명령(발자취 없는 유저만 대상, idempotent):
```bash
python manage.py seed_demo_footprints
```

공유 코스의 실제 이동 경로(`path_data`)가 비어 있는 코스에만 카카오모빌리티/OSRM 경로를 계산해 채우는 명령:
```bash
python manage.py backfill_route_paths            # --all 옵션으로 이미 있는 것도 재계산
```

---

## 핵심 파일 위치

| 파일 | 역할 |
|------|------|
| `templates/app.html` | 메인 SPA (설문·지도·동선·추천·동선저장·여행 떠나기/저니 모드) |
| `templates/places.html` | 장소 목록·검색·북마크·지도 연동 |
| `templates/place_detail.html` | 장소 상세·리뷰·북마크·비슷한장소 |
| `templates/routes.html` | 커뮤니티 코스·지도모달·댓글 |
| `templates/loading.html` | 로딩 화면 + 스킵 버튼 |
| `templates/survey.html` | 초기 설문 페이지 + 돌아가기 버튼 |
| `templates/profile.html` | 유저 프로필 (코스·북마크·리뷰·발자취·칭호·닉네임 설정) |
| `templates/landing.html` | 랜딩 페이지(`/`) — 설문 완료 여부에 따라 CTA 분기 |
| `templates/chat_widget.html` | 우측 하단 플로팅 AI 챗봇 (저니 모드에서는 숨김) |
| `culture/views.py` | 모든 장소/동선 API 뷰, `_rank_candidates()`, `_shortest_route()`, `_haversine_km()` |
| `culture/models.py` | Place·Theme·Review·Route(`is_footprint`, `path_data` 포함)·RoutePlace·RouteComment·RouteLike·Bookmark |
| `culture/serializers.py` | DRF 시리얼라이저 — Review/RouteList/RouteDetail/RouteComment에 `display_name`·`badge` 필드 포함 |
| `culture/urls.py` | 장소/동선 API URL 라우팅 |
| `culture/management/commands/set_websites.py` | URL 일괄 등록 |
| `culture/management/commands/reset_community_data.py` | 장소 데이터는 유지하고 유저 관련 데이터 전부 삭제 후 `master` 관리자 + 데모 유저 100명 + 공유 코스 90개 재생성 |
| `culture/management/commands/backfill_route_paths.py` | 공유 코스의 실제 이동 경로(`Route.path_data`)를 계산해 저장 (자동차=카카오모빌리티, 도보/자전거=OSRM) |
| `accounts/models.py` | `Profile`(`selected_badge`, `nickname`, `display_name` property), `UserFollow` |
| `accounts/badges.py` | 칭호 20종 정의(`BADGE_DEFS`), 집계(`compute_badges`/`_compute_badge_stats`), `get_badge_info()` |
| `accounts/utils.py` | `get_display_name(user)` — 닉네임 우선 표시 이름 헬퍼 |
| `accounts/views.py` | 계정 API — signup/login/logout/me/profile_detail/follow_toggle/select_badge/set_nickname + 간편 로그인(`social_login_start`/`social_login_callback`, `SOCIAL_PROVIDERS`) |
| `accounts/urls.py` | 계정 API URL 라우팅 |
| `accounts/management/commands/create_legend_account.py` | 칭호 20개 전부 달성한 superuser 데모 계정 생성 |
| `accounts/management/commands/seed_demo_footprints.py` | 발자취 없는 기존 유저에게 무작위 발자취 부여 |
| `ai/views.py` | chat·guardrail·image_generate·score — Gemini API(OpenAI 호환 엔드포인트, `GEMINI_API_KEY`) 기반 구현, 키 미설정 시 503 |
| `config/settings.py` | Django 설정, .env 로드 |
| `config/urls.py` | 전체 URL conf |
| `config/context_processors.py` | KAKAO_JS_KEY 템플릿 컨텍스트 |

---

## 주요 API 엔드포인트

### 장소·동선 (`culture/urls.py`)
| URL | 메서드 | 설명 |
|-----|--------|------|
| `/api/places/` | GET | 목록 (`?q=&era=&category=&region=`) |
| `/api/places/<pk>/` | GET | 상세 |
| `/api/places/filter/` | GET | 필터링 (`?era=&category=&region=&is_indoor=&visited=`) |
| `/api/places/visited-ids/` | GET | 로그인 유저의 발자취 장소 id 목록 (`{ids: [...]}`, 비로그인 시 빈 배열) |
| `/api/places/<pk>/similar/` | GET | 비슷한 장소 4개 |
| `/api/places/ai-recommend/` | POST | AI 추천 (`{retry?: bool, pinned_ids?: [id,...]}`) — 동선 범위(반경)는 더 이상 body로 받지 않고 서버가 소요시간·이동수단 기반으로 자동 산정(`_auto_radius_km`). `retry:true`면 세션에 누적된 이전 추천 장소를 제외하고 새로 추천(최대 3회, 초과 시 빈 결과+안내 메시지) |
| `/api/places/route-optimize/` | POST | 최단 동선 정렬 |
| `/api/places/route-directions/` | POST | 카카오모빌리티 구간별 실제 경로(자동차, `{place_ids}` → `{legs, total_distance_m, total_duration_sec, ok}`) |
| `/api/places/route-transit-info/` | POST | 이동수단별(도보/대중교통/자전거) 구간 정보 — Gemini로 예상 시간·구체적 이동방법 생성 (`{place_ids, transport}` → `{legs:[{eta_min, method}], ok}`) |
| `/api/places/route-story/` | POST | AI 여행 스토리 생성 |
| `/api/places/weather/`, `/api/places/weather-current/` | GET | 날씨 기반 추천·현재 날씨(기온·미세먼지 PM10/PM2.5 등급 포함) |
| `/api/places/<pk>/reviews/` | GET·POST | 리뷰 목록·작성 |
| `/api/places/<pk>/reviews/<pk>/` | DELETE | 리뷰 삭제 |
| `/api/routes/` | GET·POST | 코스 목록(공개 코스만)·생성 (`is_footprint:true`로 발자취 생성 가능). 생성 시 서버가 실제 이동 경로를 계산해 `path_data`에 저장 |
| `/api/routes/<pk>/` | GET·PUT·DELETE | 코스 상세(`path_data` 포함)·수정(place_ids/transport_mode 변경 시 `path_data` 재계산)·삭제 |
| `/api/routes/<pk>/like/` | POST | 좋아요 토글 |
| `/api/routes/<pk>/comments/` | GET·POST | 댓글 목록·작성 |
| `/api/routes/<pk>/comments/<pk>/` | DELETE | 댓글 삭제 |
| `/api/bookmarks/` | GET·POST | 북마크 목록(`?place=id`)·추가 |
| `/api/bookmarks/<pk>/` | DELETE | 북마크 삭제 |
| `/api/survey/save/` | POST | 설문 저장 |
| `/api/survey/reset/` | POST | 설문 초기화 |

### 계정 (`accounts/urls.py`)
| URL | 메서드 | 설명 |
|-----|--------|------|
| `/api/accounts/me/` | GET | 로그인 유저 정보 (`username`, `nickname`, `display_name`, `avatar_url`, `badge`) |
| `/api/accounts/login/` | POST | 로그인 |
| `/api/accounts/logout/` | POST | 로그아웃 |
| `/api/accounts/signup/` | POST | 회원가입 (`{username, password, password2, nickname?}`) |
| `/api/accounts/check-nickname/` | GET | 닉네임 중복확인 (`?nickname=`, `{available, detail}`) |
| `/api/accounts/me/profile-image/` | POST | 프로필 사진 업로드 (multipart `{image}`, `{avatar_url}` 반환) |
| `/api/accounts/social/<provider>/` | GET | 간편 로그인 시작 (`kakao`/`naver`/`google`) → 각 제공자 인가 페이지로 리다이렉트, `?next=`로 로그인 후 이동 경로 지정 가능 |
| `/api/accounts/social/<provider>/callback/` | GET | 인가 코드 콜백 — 토큰 교환 + 사용자 조회 후 `username=<provider>_<uid>`로 get_or_create, 로그인 처리. 실패 시 `/login/?social_error=<provider>` |
| `/api/accounts/profile/<username>/` | GET | 프로필 조회 (리뷰·북마크·코스·발자취·칭호 전체 포함, 칭호는 누구나 조회 가능) |
| `/api/accounts/profile/<username>/follow/` | POST | 팔로우 토글 |
| `/api/accounts/me/badge/` | POST | 대표 칭호 선택/해제 (`{badge_id}`, earned 검증) |
| `/api/accounts/me/nickname/` | POST | 닉네임 설정/변경/해제 (`{nickname}`, 2~10자·한글/영문/숫자만·중복 불가) |

---

## 세션 상태

```python
request.session['survey_data']  # 설문 dict
request.session['survey_done']  # bool
```

설문 데이터 형식:
```json
{
  "region": "seoul_center",
  "interests": ["joseon", "royal"],
  "duration_type": "half",
  "companions": "couple",
  "purpose": "culture"
}
```

## 클라이언트 localStorage 키 (`templates/app.html`)

| 키 | 용도 |
|-----|------|
| `cr_active_route_places` | 생성된 동선의 전체 장소 데이터 — 페이지 이동 후 `restoreActiveRoute()`로 복원 |
| `cr_journey_ids` | 현재 진행 중인 저니의 장소 id 순서 — 동선이 바뀌면 저니 상태 초기화 기준 |
| `cr_journey_visited` | 저니 내 장소별 "발자국 남기기" 체크 상태 |
| `cr_journey_memos` | 저니 내 장소별 메모 |
| `cr_journey_step` | 저니 진행 단계(현재 보고 있는 장소 인덱스) — 페이지 재방문 시 이어보기 |

여행을 끝내면(저장 또는 "여행 끝내기") 위 키 전부 삭제 + 서버 세션 `survey_done`/`survey_data`도 초기화됨.

---

## PythonAnywhere 최초 배포 (처음 등록할 때)

### 1. 계정 및 Web App 생성

1. [pythonanywhere.com](https://www.pythonanywhere.com) 접속 → 계정 생성 (무료 플랜 가능)
2. **Web** 탭 → **Add a new web app** → **Manual configuration** → **Python 3.12** 선택
   - Domain: `cultureroute.pythonanywhere.com` (무료 플랜 기본)

### 2. Bash 콘솔에서 코드 클론

**Consoles** 탭 → **New console: Bash**

```bash
# 홈 디렉토리에서 작업
cd ~

# private repo이면 GitHub 토큰 사용 (Settings → Developer settings → Personal access tokens → Classic)
git clone https://<토큰>@github.com/Jirunu/kulture_route.git culture_route

cd culture_route
```

### 3. 가상환경 생성 및 패키지 설치

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. .env 파일 생성

```bash
nano .env
```

아래 내용 붙여넣기 (값 채우기):

```
SECRET_KEY=랜덤한_긴_문자열_여기에_입력
DEBUG=False
ALLOWED_HOSTS=cultureroute.pythonanywhere.com

PUBLIC_DATA_API_KEY=한국관광공사_키
OPENWEATHER_API_KEY=오픈웨더_키
KAKAO_JS_KEY=카카오_JS_키
KAKAO_REST_KEY=카카오_REST_키
GEMINI_API_KEY=
```

> `SECRET_KEY` 생성: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### 5. DB 업로드 및 정적 파일 수집

**DB는 로컬 `db.sqlite3`를 그대로 업로드한다** (장소·URL·시드 데이터·관리자 계정 포함).

1. PythonAnywhere **Files** 탭 → `/home/cultureroute/culture_route/` 경로 이동
2. `db.sqlite3` 파일 업로드 (덮어쓰기)
3. Bash 콘솔에서:

```bash
source venv/bin/activate
python manage.py migrate          # 혹시 미적용 마이그레이션 있으면 반영
python manage.py collectstatic --noinput
```

> 로컬 DB 기준(`reset_community_data` 직후): Place 530개, User `master` + `user001`~`user100`(101명) + 수동 테스트 계정 일부, 공유 코스 약 96개 + 발자취 약 117개
> `master` 계정만 is_superuser=True — 로컬에서 쓰는 비밀번호(`master123`)로 그대로 로그인 가능

> **DB 재업로드 시점**: 로컬에서 장소 추가·URL 세팅·시드 데이터 변경 등 데이터 작업 후
> 코드만 바뀐 경우엔 git pull + Reload만으로 충분

### 6. WSGI 파일 설정

**Web** 탭 → **WSGI configuration file** 링크 클릭 (보통 `/var/www/cultureroute_pythonanywhere_com_wsgi.py`)

기존 내용을 전부 지우고 아래로 교체:

```python
import sys
import os

path = '/home/cultureroute/culture_route'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. 가상환경 경로 설정

**Web** 탭 → **Virtualenv** 섹션:

```
/home/cultureroute/culture_route/venv
```

### 8. 정적 파일 설정

**Web** 탭 → **Static files** 섹션에 아래 두 줄 추가:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/cultureroute/culture_route/staticfiles` |

### 9. Reload

**Web** 탭 상단 **Reload** 버튼 클릭 → `cultureroute.pythonanywhere.com` 접속 확인

---

## PythonAnywhere 이후 업데이트 배포

코드 변경 후 PythonAnywhere에 반영하는 절차:

```bash
# Bash 콘솔 열기
cd ~/culture_route
source venv/bin/activate

git pull

# 모델 변경이 있으면
python manage.py migrate

# requirements.txt 변경이 있으면
pip install -r requirements.txt

# 정적 파일 변경이 있으면
python manage.py collectstatic --noinput
```

그 후 **Web** 탭 → **Reload** 클릭.

**현재까지 누적된 마이그레이션** (배포 시 `migrate` 한 번이면 전부 반영됨):
- `culture.0006_route_is_footprint` — Route에 `is_footprint` 필드 추가 (발자취 자동 기록용)
- `culture.0008_route_path_data` — Route에 `path_data` 필드 추가 (실제 이동 경로 좌표 저장용)
- `accounts.0002_profile` — `Profile` 모델 추가 (`selected_badge`)
- `accounts.0003_profile_nickname` — `Profile.nickname` 추가

처음 배포하거나 칭호/발자취 기능을 새로 반영하는 경우, migrate 후 한 번씩 실행:
```bash
python manage.py seed_demo_footprints      # 기존 유저들 칭호 노출
python manage.py create_legend_account --username master --password master123  # 슈퍼 데모 계정(선택)
python manage.py backfill_route_paths      # 공유 코스 실제 경로(path_data) 채우기
```

배포본 전체를 로컬과 동일한 데모 상태로 맞추려면(유저 데이터 전부 초기화 + 재생성) `reset_community_data`를 그대로 실행해도 된다 — Place/Theme은 건드리지 않는다.

---

## 별도 실험 파일 (프로젝트 외부, Django와 무관)

- **`C:\Users\SSAFY\Desktop\osrm_kakao_test.html`** — OSRM(도보/자전거/대중교통 경로) + 카카오맵 Polyline 표시를 검증하기 위한 단일 HTML 테스트 파일. Django 서버 없이 브라우저에서 바로 열어서 확인하는 용도로, **이 프로젝트의 git 저장소·코드와는 분리되어 있고 본 리포의 기능에는 영향 없음**.
  - 구성: Kakao Map(경복궁·창덕궁·인사동 마커) + 도보/자전거/대중교통 버튼 + OSRM `/route/v1/{foot|bike|driving}/` 호출 → Polyline 표시 + 구간별·총 거리/시간 카드. 대중교통은 자동차 프로필을 시간 ×1.3 보정해 대체.
  - Kakao JS 키는 `.env`의 `KAKAO_JS_KEY` 값을 그대로 하드코딩해서 삽입(해당 `.env`에 `KAKAO_MAP_API_KEY`라는 키는 존재하지 않음).
  - **현재 상태: 미작동 확인됨 (2026-06-22 기준 디버깅 필요)** — 코드 자체는 작성 완료됐지만 실제 브라우저 테스트에서 의도대로 동작하지 않음. 의심 원인(미확인, 다음 점검 시 우선 검토):
    1. Kakao Developers 콘솔에 등록된 플랫폼 도메인이 `file://` 로컬 실행을 허용하지 않아 지도 자체가 안 뜨는 경우
    2. OSRM 공개 데모 서버(`router.project-osrm.org`)가 `foot`/`bike` 프로필을 지원하지 않아(공식 데모는 `driving` 위주) 404/오류로 떨어지는 경우
    3. 그 외 CORS, 마커/인포윈도우 렌더 순서 등 콘솔 에러 미확인 상태
  - 다음 작업 시 브라우저 콘솔 에러 로그를 먼저 확보하고 위 원인부터 순서대로 배제할 것.

## 알려진 이슈 / 미완성

- `ai/views.py` chat·guardrail·score: Gemini API(OpenAI 호환 엔드포인트, `GEMINI_API_KEY`, 모델은 `GEMINI_MODEL`)로 구현 완료. 키 미설정 시에만 503 반환.
- `ai/views.py`의 image_generate: Gemini 무료 티어가 OpenAI 호환 `images.generate`를 지원하지 않을 수 있음 — 호출 실패 시 503 반환(`GEMINI_IMAGE_MODEL`).
- `culture/views.py`의 `_call_ai_recommend`(AI 추천)·`route_story`(여행 스토리)·`route_optimize`(동선 팁)도 동일하게 Gemini 사용. 키 없으면 규칙 기반 폴백(추천) 또는 빈 결과(스토리·팁)로 동작.
- `fetch_websites` (TourAPI 자동 수집): 일일 쿼터 소진으로 미활용. `set_websites`로 대체.
- 나무위키 링크: 장소명 ≠ 나무위키 문서명일 경우 404 가능 (자동 설정이므로 검증 안 됨).
- 리뷰 이미지: URL 입력 방식만 지원. S3 파일 업로드는 미구현.
- `ai/` 챗봇 페이지: 로그인 필요 (`login_required`).
- 발자취/칭호는 여행 전체 단위로만 기록됨 — 저니 중 개별 "발자국 남기기" 체크 여부는 서버에 전송되지 않고 클라이언트 localStorage에만 남음(서버는 완료한 동선 전체를 발자취로 기록).
- 닉네임 변경 시 과거에 작성된 리뷰/댓글 등의 표시 이름은 실시간으로 갱신됨(저장 시점 스냅샷이 아니라 매 조회 시 `get_display_name()` 호출) — 별도 이력 관리 없음.
- 공유 코스의 `path_data` 계산은 카카오모빌리티/OSRM 외부 API를 실시간 호출하므로, 코스 생성·수정(`POST`/`PUT /api/routes/`) 응답이 구간 수에 비례해 느려질 수 있다(네트워크 실패 시 해당 구간만 직선으로 폴백, 에러는 아님).
- `대중교통`/`기차` 이동수단은 OSRM/카카오모빌리티 어느 쪽도 지원하지 않아 `path_data`가 항상 직선 좌표로 저장된다(곡선 경로 미지원).
