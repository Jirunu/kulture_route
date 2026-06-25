import json
import math
import re
import requests
from itertools import permutations
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Place, Theme, Review, Route, RoutePlace, Bookmark, RouteLike, RouteComment
from .serializers import (
    PlaceListSerializer, PlaceDetailSerializer,
    ThemeSerializer,
    ReviewSerializer,
    RouteListSerializer, RouteDetailSerializer, RouteCreateSerializer,
    RouteCommentSerializer,
    BookmarkSerializer,
)


# -----------------------------------------------
# F808 - place_list
# 전체 문화 장소 목록 조회
# -----------------------------------------------
@api_view(['GET'])
def place_list(request):
    """
    GET /api/places/
    전체 문화 장소 목록 반환
    - q: 이름 검색 (name__icontains)
    """
    places = Place.objects.select_related('theme').all()
    q = request.query_params.get('q')
    if q:
        places = places.filter(name__icontains=q)
    serializer = PlaceListSerializer(places, many=True)
    return Response(serializer.data)


# -----------------------------------------------
# F809 - place_detail
# 단일 문화 장소 상세 조회
# -----------------------------------------------
@api_view(['GET'])
def place_detail(request, place_pk):
    """
    GET /api/places/<place_pk>/
    단일 장소 상세 정보 반환 (리뷰 최신 5개 포함)
    """
    place = get_object_or_404(Place, pk=place_pk)
    serializer = PlaceDetailSerializer(place)
    return Response(serializer.data)


# -----------------------------------------------
# F810 - place_by_theme
# 시대·카테고리·지역 필터 장소 조회
# -----------------------------------------------
@api_view(['GET'])
def place_by_theme(request):
    """
    GET /api/places/filter/
    쿼리 파라미터로 필터링
    - era      : 시대 (three_kingdoms / goryeo / joseon / japanese / modern)
    - category : 카테고리 (historic / museum / park / palace / culture / etc)
    - region   : 지역 (seoul / gyeonggi)
    - is_indoor: 실내 여부 (true / false)
    - visited  : 방문 여부 (true / false) — 로그인 사용자의 발자취(Route is_footprint=True) 기준, 비로그인 시 무시
    """
    places = Place.objects.select_related('theme').all()

    era_list      = request.query_params.getlist('era')
    category_list = request.query_params.getlist('category')
    region        = request.query_params.get('region')
    is_indoor     = request.query_params.get('is_indoor')
    is_active     = request.query_params.get('is_active')
    visited       = request.query_params.get('visited')
    q             = request.query_params.get('q')

    if era_list:
        places = places.filter(theme__era__in=era_list)
    if category_list:
        places = places.filter(category__in=category_list)
    if region:
        places = places.filter(region=region)
    if is_indoor is not None:
        places = places.filter(is_indoor=is_indoor.lower() == 'true')
    if is_active is not None:
        places = places.filter(is_active=is_active.lower() == 'true')
    if visited is not None and request.user.is_authenticated:
        visited_ids = RoutePlace.objects.filter(
            route__is_footprint=True, route__user=request.user
        ).values_list('place_id', flat=True)
        if visited.lower() == 'true':
            places = places.filter(pk__in=visited_ids)
        else:
            places = places.exclude(pk__in=visited_ids)
    if q:
        places = places.filter(name__icontains=q)

    serializer = PlaceListSerializer(places, many=True)
    return Response(serializer.data)


# -----------------------------------------------
# 로그인 유저가 방문(발자취 기록)한 장소 id 목록
# -----------------------------------------------
@api_view(['GET'])
def visited_place_ids(request):
    """
    GET /api/places/visited-ids/
    로그인 사용자의 발자취(Route is_footprint=True)에 포함된 장소 id 목록.
    비로그인 시 빈 목록 반환.
    """
    if not request.user.is_authenticated:
        return Response({'ids': []})
    ids = RoutePlace.objects.filter(
        route__is_footprint=True, route__user=request.user
    ).values_list('place_id', flat=True).distinct()
    return Response({'ids': list(ids)})


# -----------------------------------------------
# 비슷한 장소 추천
# -----------------------------------------------
@api_view(['GET'])
def place_similar(request, place_pk):
    """GET /api/places/<pk>/similar/ — 같은 카테고리·테마 장소 4개"""
    place = get_object_or_404(Place, pk=place_pk)
    qs = Place.objects.filter(
        Q(category=place.category) | Q(theme=place.theme)
    ).exclude(pk=place_pk).select_related('theme').order_by('?')[:4]
    return Response(PlaceListSerializer(qs, many=True).data)


# -----------------------------------------------
# F811 - review_list
# 특정 장소의 전체 리뷰 조회 + 리뷰 작성
# -----------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def review_list(request, place_pk):
    """
    GET  /api/places/<place_pk>/reviews/  : 해당 장소 리뷰 목록 조회
    POST /api/places/<place_pk>/reviews/  : 리뷰 작성 (로그인 필요)
    """
    place = get_object_or_404(Place, pk=place_pk)

    if request.method == 'GET':
        reviews = place.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    # POST
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, place=place)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------
# F812 - review_detail
# 단일 리뷰 조회·수정·삭제
# -----------------------------------------------
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def review_detail(request, place_pk, review_pk):
    """
    GET    /api/places/<place_pk>/reviews/<review_pk>/  : 단일 리뷰 조회
    PUT    /api/places/<place_pk>/reviews/<review_pk>/  : 리뷰 수정 (작성자만)
    DELETE /api/places/<place_pk>/reviews/<review_pk>/  : 리뷰 삭제 (작성자만)
    """
    place  = get_object_or_404(Place, pk=place_pk)
    review = get_object_or_404(Review, pk=review_pk, place=place)

    if request.method == 'GET':
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    # 작성자 본인만 수정·삭제 가능
    if review.user != request.user:
        return Response(
            {'detail': '본인이 작성한 리뷰만 수정·삭제할 수 있습니다.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'PUT':
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    review.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------
# F813 - create_review
# 리뷰 작성 (단독 엔드포인트 - review_list POST와 동일 역할)
# -----------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, place_pk):
    """
    POST /api/places/<place_pk>/reviews/create/
    리뷰 데이터를 전달받아 DB에 저장
    """
    place = get_object_or_404(Place, pk=place_pk)
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, place=place)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _save_route_path(route):
    """코스 생성/수정 시점에 실제 경로(곡선)를 1회 계산해 path_data에 저장한다."""
    ordered = [rp.place for rp in route.routeplace_set.select_related('place').order_by('order')]
    route.path_data = compute_route_path(ordered, route.transport_mode) if len(ordered) >= 2 else []
    route.save(update_fields=['path_data'])


# -----------------------------------------------
# F814 - route_recommend
# 동선 코스 자동 생성 및 목록 조회
# -----------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def route_recommend(request):
    """
    GET  /api/routes/          : 공유된 커뮤니티 코스 목록 조회
    POST /api/routes/          : 새 코스 생성
         body: { title, mode, total_distance, total_time, is_shared, place_ids }
    """
    if request.method == 'GET':
        routes = Route.objects.filter(is_shared=True).select_related('user').prefetch_related(
            'routeplace_set__place', 'likes', 'comments'
        ).order_by('-created_at')
        serializer = RouteListSerializer(routes, many=True, context={'request': request})
        return Response(serializer.data)

    # POST
    serializer = RouteCreateSerializer(data=request.data)
    if serializer.is_valid():
        route = serializer.save(user=request.user)
        _save_route_path(route)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def route_detail(request, route_pk):
    """
    GET    /api/routes/<route_pk>/  : 코스 상세 조회
    PUT    /api/routes/<route_pk>/  : 코스 수정 (생성자만)
    DELETE /api/routes/<route_pk>/  : 코스 삭제 (생성자만)
    """
    route = get_object_or_404(Route, pk=route_pk)

    if request.method == 'GET':
        serializer = RouteDetailSerializer(route)
        return Response(serializer.data)

    if route.user != request.user:
        return Response(
            {'detail': '본인이 생성한 코스만 수정·삭제할 수 있습니다.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'PUT':
        serializer = RouteCreateSerializer(route, data=request.data, partial=True)
        if serializer.is_valid():
            route = serializer.save()
            if 'place_ids' in request.data or 'transport_mode' in request.data:
                _save_route_path(route)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    route.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------
# F815 - bookmark_list / detail
# 북마크 목록 조회·추가·삭제
# -----------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def bookmark_list(request):
    """
    GET  /api/bookmarks/  : 내 북마크 목록 조회
    POST /api/bookmarks/  : 북마크 추가
         body: { place: <id> } 또는 { route: <id> }
    """
    if request.method == 'GET':
        bookmarks = Bookmark.objects.filter(user=request.user).select_related('place', 'route')
        place_id = request.query_params.get('place')
        if place_id:
            bookmarks = bookmarks.filter(place_id=place_id)
        serializer = BookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data)

    # POST
    serializer = BookmarkSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def bookmark_detail(request, bookmark_pk):
    """
    DELETE /api/bookmarks/<bookmark_pk>/  : 북마크 삭제 (본인만)
    """
    bookmark = get_object_or_404(Bookmark, pk=bookmark_pk, user=request.user)
    bookmark.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------
# F816 - 날씨 기반 장소 추천
# -----------------------------------------------
@api_view(['GET'])
def weather_recommend(request):
    """
    GET /api/places/weather/
    쿼리 파라미터:
    - is_indoor : true / false  (날씨 API 연동 후 자동 판단 예정)
    - is_active : true / false  (동적/정적 장소 여부)

    현재는 파라미터 기반 필터링,
    추후 OpenWeatherMap API 연동으로 자동화 예정 (F818)
    """
    places = Place.objects.select_related('theme').all()

    is_indoor = request.query_params.get('is_indoor')
    is_active = request.query_params.get('is_active')

    if is_indoor is not None:
        places = places.filter(is_indoor=is_indoor.lower() == 'true')
    if is_active is not None:
        places = places.filter(is_active=is_active.lower() == 'true')

    serializer = PlaceListSerializer(places, many=True)
    return Response(serializer.data)


def _pm25_grade(pm2_5):
    """미세먼지(PM2.5) 등급 기준 (㎍/㎥)."""
    if pm2_5 <= 15:
        return '좋음'
    if pm2_5 <= 35:
        return '보통'
    if pm2_5 <= 75:
        return '나쁨'
    return '매우나쁨'


# -----------------------------------------------
# F818 - OpenWeatherMap 실시간 날씨 조회
# -----------------------------------------------
@api_view(['GET'])
def weather_current(request):
    """
    GET /api/places/weather-current/
    OpenWeatherMap API로 서울 현재 날씨를 조회하고
    실내/실외 추천 여부와 함께 반환한다.
    """
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
    if not api_key:
        return Response({'error': 'OPENWEATHER_API_KEY가 설정되지 않았습니다.'}, status=503)

    try:
        resp = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'q': 'Seoul,KR', 'appid': api_key, 'units': 'metric', 'lang': 'kr'},
            timeout=5,
        )
        resp.raise_for_status()
        w = resp.json()
    except requests.RequestException:
        return Response({'error': '날씨 정보를 가져올 수 없습니다. 잠시 후 다시 시도해 주세요.'}, status=503)

    pm10 = pm2_5 = air_quality_grade = None
    try:
        lat, lon = w['coord']['lat'], w['coord']['lon']
        air_resp = requests.get(
            'https://api.openweathermap.org/data/2.5/air_pollution',
            params={'lat': lat, 'lon': lon, 'appid': api_key},
            timeout=5,
        )
        air_resp.raise_for_status()
        components = air_resp.json()['list'][0]['components']
        pm10 = round(components['pm10'])
        pm2_5 = round(components['pm2_5'])
        air_quality_grade = _pm25_grade(pm2_5)
    except (requests.RequestException, KeyError, IndexError):
        pass

    weather_id   = w['weather'][0]['id']
    description  = w['weather'][0]['description']
    temp         = round(w['main']['temp'])
    humidity     = w['main']['humidity']
    icon_code    = w['weather'][0]['icon']
    city         = w['name']

    # 800: 맑음, 801-802: 구름 조금 → 실외 OK / 나머지 → 실내 권장
    is_indoor = not (weather_id == 800 or 801 <= weather_id <= 802)

    if weather_id == 800:
        emoji, msg = '☀️', '야외 활동하기 최적의 날씨입니다.\n실외 역사 유적지와 궁궐을 추천드립니다.'
        conds = ['실외 · 동적 장소 우선', '공원 · 궁궐 · 유적지 추천']
    elif 801 <= weather_id <= 802:
        emoji, msg = '⛅', '구름이 조금 있지만 야외 활동 가능합니다.\n궁궐이나 공원 방문을 추천드립니다.'
        conds = ['실외 장소 무난', '공원 · 산책로 추천']
    elif 803 <= weather_id <= 804:
        emoji, msg = '☁️', '흐린 날씨입니다.\n실내 박물관이나 미술관 방문을 추천드립니다.'
        conds = ['실내 시설 우선 추천', '박물관 · 미술관 · 문화 시설']
    elif 300 <= weather_id <= 321:
        emoji, msg = '🌦️', '이슬비가 내리고 있습니다.\n실내 문화 시설을 추천드립니다.'
        conds = ['실내 시설 추천', '박물관 · 미술관']
    elif 500 <= weather_id <= 531:
        emoji, msg = '🌧️', '비가 내리고 있습니다.\n따뜻한 실내 문화 시설을 추천드립니다.'
        conds = ['실내 관람 시설 우선', '박물관 · 역사관 추천']
    elif 600 <= weather_id <= 622:
        emoji, msg = '❄️', '눈이 내리고 있습니다.\n실내 박물관이나 미술관을 추천드립니다.'
        conds = ['실내 시설 강력 추천', '박물관 · 미술관 · 실내 문화']
    elif 200 <= weather_id <= 232:
        emoji, msg = '⛈️', '천둥번개가 치고 있습니다.\n안전을 위해 실내 시설을 이용하세요.'
        conds = ['실내 시설 이용 권장', '안전 우선 실내 관람']
    else:
        emoji, msg = '🌤️', '다양한 문화 명소를 즐겨보세요.'
        conds = ['날씨에 맞는 장소 추천', '문화 명소 탐방']

    return Response({
        'temp':           temp,
        'description':    description,
        'humidity':       humidity,
        'emoji':          emoji,
        'city':           city,
        'is_indoor':      is_indoor,
        'recommendation': msg,
        'conditions':     conds,
        'icon':           f'https://openweathermap.org/img/wn/{icon_code}@2x.png',
        'pm10':                pm10,
        'pm2_5':               pm2_5,
        'air_quality_grade':   air_quality_grade,
    })


# -----------------------------------------------
# F819 - 커뮤니티 코스 좋아요 토글
# -----------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def route_like(request, route_pk):
    """
    POST /api/routes/<route_pk>/like/
    좋아요 토글 — 처음 누르면 추가, 다시 누르면 취소
    """
    route = get_object_or_404(Route, pk=route_pk, is_shared=True)
    like, created = RouteLike.objects.get_or_create(user=request.user, route=route)
    if not created:
        like.delete()
        route.like_count = max(0, route.like_count - 1)
        liked = False
    else:
        route.like_count += 1
        liked = True
    route.save(update_fields=['like_count'])
    return Response({'liked': liked, 'like_count': route.like_count}, status=status.HTTP_200_OK)


# -----------------------------------------------
# 코스 댓글
# -----------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def route_comments(request, route_pk):
    """
    GET  /api/routes/<route_pk>/comments/  : 댓글 목록 조회
    POST /api/routes/<route_pk>/comments/  : 댓글 작성 (로그인 필요)
    """
    route = get_object_or_404(Route, pk=route_pk)
    if request.method == 'GET':
        serializer = RouteCommentSerializer(route.comments.select_related('user').all(), many=True)
        return Response(serializer.data)
    serializer = RouteCommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, route=route)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def route_comment_detail(request, route_pk, comment_pk):
    """
    DELETE /api/routes/<route_pk>/comments/<comment_pk>/  : 댓글 삭제 (작성자만)
    """
    comment = get_object_or_404(RouteComment, pk=comment_pk, route_id=route_pk)
    if comment.user != request.user:
        return Response({'detail': '본인이 작성한 댓글만 삭제할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# -----------------------------------------------
# 온보딩 설문 뷰
# -----------------------------------------------
@login_required
def survey_view(request):
    """GET /survey/ — survey_done 세션 없으면 설문, 있으면 /app/ 리다이렉트"""
    if request.session.get('survey_done'):
        return redirect('/app/')
    return render(request, 'survey.html')


@login_required
def app_view(request):
    """GET /app/ — 설문 완료 후 메인 앱 (미완료 시 /survey/ 리다이렉트)"""
    if not request.session.get('survey_done'):
        return redirect('/survey/')
    survey_data = request.session.get('survey_data', {})
    return render(request, 'app.html', {'survey_data_json': json.dumps(survey_data, ensure_ascii=False)})


def index_view(request):
    """GET / — 랜딩 페이지 (survey_done 여부 + 통계 수치를 context로 전달)"""
    return render(request, 'landing.html', {
        'survey_done': request.session.get('survey_done', False),
        'community_route_count': Route.objects.filter(is_shared=True).count(),
        'place_count_floor': (Place.objects.count() // 10) * 10,
    })


@require_http_methods(['POST'])
def survey_save(request):
    """POST /api/survey/save/ — 설문 응답을 세션에 저장"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': '잘못된 데이터입니다.'}, status=400)
    request.session['survey_done'] = True
    request.session['survey_data'] = data
    request.session.pop('ai_recommend_history', None)
    return JsonResponse({'status': 'ok', 'redirect': '/loading/'})


# -----------------------------------------------
# Haversine 거리 계산 (km)
# -----------------------------------------------
def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# 지역 중심 좌표 (새 설문 region 값 기준)
_REGION_CENTER = {
    'seoul_center':   (37.5704, 126.9868),
    'seoul_outer':    (37.5665, 126.9780),
    'gyeonggi_north': (37.7500, 127.0000),
    'gyeonggi_south': (37.2500, 127.0000),
    'any':            (37.5665, 126.9780),
}

# 새 설문 interest 값 → DB 필터 매핑
_ERA_MAP = {
    'joseon':        ['joseon'],
    'goryeo_samguk': ['goryeo', 'three_kingdoms'],
    'modern_history':['japanese', 'modern'],
}
_CAT_MAP = {
    'buddhism': 'palace',
    'royal':    'palace',
    'folk':     'historic',
    # 설문 2단계 직접 선택값
    'historic': 'historic',
    'museum':   'museum',
    'palace':   'palace',
}
_DURATION_MAP = {'short': 2, 'half': 4, 'full': 8}
_REGION_DB_MAP = {
    'seoul_center': 'seoul', 'seoul_outer': 'seoul',
    'gyeonggi_north': 'gyeonggi', 'gyeonggi_south': 'gyeonggi',
    'any': '',
    # 구 설문 형식 호환
    'seoul_north': 'seoul', 'seoul_south': 'seoul',
    'seoul_east':  'seoul', 'seoul_west':  'seoul',
    'gyeonggi_east': 'gyeonggi', 'gyeonggi_west': 'gyeonggi',
}


def _get_ai_client():
    """GEMINI_API_KEY가 설정돼 있으면 Gemini(OpenAI 호환 엔드포인트) 클라이언트, 아니면 None."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return None
    try:
        import openai as _oai
    except ImportError:
        return None
    return _oai.OpenAI(api_key=api_key, base_url=settings.GEMINI_BASE_URL)


def _call_ai_recommend(survey, candidates, exclude_ids=None):
    """Gemini API로 후보 장소 중 최적 5개 추천. 실패 시 None 반환."""
    client = _get_ai_client()
    if client is None:
        return None

    ERA_KO = {
        'three_kingdoms': '삼국시대', 'goryeo': '고려시대', 'joseon': '조선시대',
        'japanese': '일제강점기', 'modern': '현대',
    }
    CAT_KO = {'historic': '역사 유적', 'museum': '박물관·미술관', 'palace': '궁궐·사찰'}
    COMPANIONS_KO = {'solo': '혼자', 'couple': '커플', 'group': '소그룹', 'family': '가족'}
    PURPOSE_KO = {'study': '역사 학습', 'culture': '문화 체험', 'healing': '힐링', 'photo': '사진 촬영'}
    DURATION_KO = {'short': '2~3시간', 'half': '반나절(4시간)', 'full': '하루(8시간)'}
    TRANSPORT_KO = {'walk': '도보', 'bike': '자전거', 'car': '자동차'}

    interests = [i for i in survey.get('interests', []) if i != 'any']
    interests_str = ', '.join(CAT_KO.get(i, i) for i in interests) or '무관'
    companions = COMPANIONS_KO.get(survey.get('companions', ''), '')
    purpose = PURPOSE_KO.get(survey.get('purpose', ''), '')
    duration = DURATION_KO.get(survey.get('duration_type', ''), '')
    transport_ko = TRANSPORT_KO.get(survey.get('transport', 'walk'), '도보')

    places_data = [
        {
            'id': p.id,
            'name': p.name,
            'category': CAT_KO.get(p.category, p.category),
            'era': ERA_KO.get(p.theme.era if p.theme else '', ''),
            'indoor': '실내' if p.is_indoor else '실외',
            'fee': '무료' if p.entrance_fee == 0 else f'{p.entrance_fee:,}원',
            'lat': float(p.latitude),
            'lng': float(p.longitude),
        }
        for p in candidates
    ]

    exclude_note = ''
    if exclude_ids:
        exclude_note = (
            f'\n이전에 추천한 장소 id 목록: {list(exclude_ids)}\n'
            f'위 장소들은 제외하고 완전히 다른 장소로 새 동선을 구성해줘.\n'
        )

    prompt = (
        f'서울·경기 문화명소 여행 큐레이터입니다.\n\n'
        f'사용자 취향: 관심분야={interests_str}, 동행={companions}, 목적={purpose}, 소요시간={duration}, 이동수단={transport_ko}\n'
        f'{exclude_note}\n'
        f'후보 장소 {len(places_data)}곳을 이 사용자에게 적합한 순서대로 최대 10곳까지 순위를 매기고, '
        f'취향에 맞춘 추천 이유를 한 문장씩 작성하세요. (실제로는 이후 소요시간에 맞춰 앞에서부터 일부만 사용됩니다)\n\n'
        f'중요: 각 장소의 lat/lng 좌표를 참고해, {transport_ko} 이동을 기준으로 서로 가까워 '
        f'효율적으로 묶일 수 있는 장소를 우선 배치하세요. 관람시간(장소당 약 45~70분)에 비해 '
        f'이동시간이 지나치게 긴 멀리 떨어진 장소들을 연속으로 배치하지 마세요.\n\n'
        f'후보:\n{json.dumps(places_data, ensure_ascii=False)}\n\n'
        f'JSON만 응답 (다른 텍스트 없이):\n'
        f'{{"ranked": [{{"id": <숫자>, "reason": "<이유>"}}, ...]}}'
    )

    try:
        completion = client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            max_tokens=900,
            extra_body={'reasoning_effort': 'none'},
            messages=[{'role': 'user', 'content': prompt}],
        )
        text = completion.choices[0].message.content.strip()
        if '```' in text:
            text = re.sub(r'```(?:json)?', '', text).strip()
        ranked = json.loads(text).get('ranked', [])[:10]
        id_to_place = {p.id: p for p in candidates}
        result = [
            (id_to_place[item['id']], item.get('reason', ''))
            for item in ranked
            if item.get('id') in id_to_place
        ]
        return result or None
    except Exception:
        return None


# 장소 카테고리별 평균 관람 소요시간(분) — templates/app.html의 VISIT_MIN과 동일 기준
_VISIT_MIN = {'museum': 70, 'palace': 70, 'historic': 45}
_DEFAULT_VISIT_MIN = 55
# 이동수단별 평균 속력(km/h) 추정 — route-transit-info의 walk/bike 속력과 동일 기준,
# car는 시내 주행(신호 대기 포함) 평균으로 추정. ponytail: 추정치, 실측 API 연동 시 교체.
_REC_TRANSPORT_SPEED_KMH = {'walk': 4.8, 'bike': 15, 'car': 25}
# 관람시간 대비 이동시간이 이 비율(+최소 20분 여유)을 넘으면 비효율적인 동선으로 보고 제외한다.
_MAX_TRAVEL_TO_VISIT_RATIO = 1.5
_AUTO_RADIUS_MIN_KM = 4
_AUTO_RADIUS_MAX_KM = 40


def _auto_radius_km(duration_hours, transport='walk'):
    """
    동선 범위(후보 탐색용 지름)를 유저가 직접 정하지 않고, 소요시간·이동수단으로부터 추정한다.
    소요시간 중 일부(약 40%)를 이동에 쓴다고 가정해 그 시간 동안 갈 수 있는 거리를 지름으로 삼는다.
    실제 최종 동선의 적합성은 _trim_by_time_budget()의 시간 예산 검사가 따로 보장한다.
    """
    speed_kmh = _REC_TRANSPORT_SPEED_KMH.get(transport, _REC_TRANSPORT_SPEED_KMH['walk'])
    estimated = speed_kmh * duration_hours * 0.4
    return max(_AUTO_RADIUS_MIN_KM, min(_AUTO_RADIUS_MAX_KM, estimated))


def _trim_by_time_budget(selected_places, duration_hours, transport='walk', pinned_count=0):
    """
    추천 순위 순서대로 앞에서부터 채워가며, '관람시간 + 이동시간(이동수단 기준 추정)'의 누적합이
    설문에서 받은 소요시간(시간 단위) 이내가 되는 만큼만 남긴다.
    관람시간에 비해 이동시간이 지나치게 긴(비효율적인) 장소는 건너뛰고 다음 순위를 시도한다.
    맨 앞 pinned_count개(사용자가 직접 체크한 필수 방문지)는 예산·효율성 검사 없이 항상 포함한다.
    최소 1곳은 항상 포함한다(첫 장소 혼자 예산을 넘어도 유지).
    """
    if not selected_places:
        return selected_places

    speed_kmh = _REC_TRANSPORT_SPEED_KMH.get(transport, _REC_TRANSPORT_SPEED_KMH['walk'])
    budget_min = duration_hours * 60

    n_seed = max(1, pinned_count)
    trimmed = list(selected_places[:n_seed])
    total_min = sum(_VISIT_MIN.get(p.category, _DEFAULT_VISIT_MIN) for p, _ in trimmed)
    for i in range(1, len(trimmed)):
        total_min += _haversine_km(trimmed[i - 1][0], trimmed[i][0]) / speed_kmh * 60

    for place, reason in selected_places[n_seed:]:
        prev_place = trimmed[-1][0]
        travel_min = _haversine_km(prev_place, place) / speed_kmh * 60
        visit_min = _VISIT_MIN.get(place.category, _DEFAULT_VISIT_MIN)

        if travel_min > max(visit_min, 20) * _MAX_TRAVEL_TO_VISIT_RATIO:
            continue  # 관람시간 대비 이동시간이 너무 길어 비효율적인 동선 — 건너뛰고 다음 후보 시도

        added = travel_min + visit_min
        if total_min + added > budget_min:
            break
        trimmed.append((place, reason))
        total_min += added

    return trimmed


def _rank_candidates(candidates, eras, categories, duration_type, companions, purpose, interests):
    """설문 데이터 기반 규칙 점수 산정 → 상위 10개 반환 (시간 예산 트림은 별도 단계에서 처리)."""
    ERA_LABEL = {
        'three_kingdoms': '삼국시대', 'goryeo': '고려시대', 'joseon': '조선시대',
        'japanese': '일제강점기', 'modern': '현대',
    }
    CAT_LABEL = {'historic': '역사 유적', 'museum': '박물관·미술관', 'palace': '궁궐·사찰'}

    scored = []
    for p in candidates:
        score = 0
        tags = []
        era = p.theme.era if p.theme else ''

        if eras and era in eras:
            score += 4
            tags.append(f'{ERA_LABEL.get(era, era)} 관련 장소')

        if categories and p.category in categories:
            score += 3
            tags.append(f'{CAT_LABEL.get(p.category, p.category)} 취향에 맞음')

        if duration_type == 'short' and p.is_indoor:
            score += 2
        elif duration_type == 'full' and not p.is_indoor:
            score += 1

        if purpose == 'study' and p.category in ('museum', 'historic'):
            score += 2
            tags.append('역사 학습에 적합')
        elif purpose == 'culture' and p.category == 'palace':
            score += 2
            tags.append('전통 문화 체험에 좋음')
        elif purpose in ('healing', 'photo') and not p.is_indoor:
            score += 1

        if companions == 'family' and p.entrance_fee == 0:
            score += 1
            tags.append('가족 방문에 알맞은 무료 장소')
        elif p.entrance_fee == 0:
            score += 1

        if not tags:
            if era:
                tags.append(f'{ERA_LABEL.get(era, era)} 테마의 장소')
            else:
                tags.append(f'{CAT_LABEL.get(p.category, "")} 취향 추천 장소')

        scored.append((score, p, ', '.join(tags)))

    scored.sort(key=lambda x: -x[0])
    return [(p, reason) for _, p, reason in scored[:10]]


# -----------------------------------------------
# AI 장소 추천 (OpenAI API + 규칙 기반 폴백)
# -----------------------------------------------
@api_view(['POST'])
def ai_recommend(request):
    """
    POST /api/places/ai-recommend/
    세션 설문 데이터 기반으로 Gemini가 장소를 추천(최대 10곳 순위)한 뒤,
    관람시간 + 이동시간(설문에서 선택한 이동수단 기준 추정)의 합이 설문 소요시간 이내가 되는 만큼만
    앞에서부터 남긴다(최소 1곳은 항상 포함). 동선 범위(반경)는 유저 입력값이 아니라 소요시간·이동수단으로부터
    AI 추천 로직이 자동으로 산정한다(_auto_radius_km).
    body: {
      retry: <bool, 재추천 여부 기본 false>,
      pinned_ids: <장소 탭에서 체크해 둔 "꼭 가고 싶은" 장소 id 목록, 결과에 항상 포함되고
                   그 주변 장소들이 우선적으로 채워진다>
    }
    재추천(retry:true) 시 이전에 추천했던 장소들을 제외하고 새로 추천하며,
    세션에 누적된 재추천 기록을 기준으로 최대 3회까지만 허용한다(단, pinned_ids는 재추천에도 항상 유지).
    비로그인도 허용 (설문 데이터는 세션에 저장).
    """
    survey = request.session.get('survey_data', {})
    is_retry = bool(request.data.get('retry', False))
    pinned_ids = [int(i) for i in request.data.get('pinned_ids', []) if str(i).lstrip('-').isdigit()]

    history = request.session.get('ai_recommend_history', [])
    if not is_retry:
        history = []
    elif len(history) >= 3:
        return Response({
            'places': [],
            'message': '더 이상 새로운 추천이 없습니다.',
            'max_retries_reached': True,
        })

    # pinned(꼭 포함) 장소는 재추천 시에도 절대 제외하지 않는다.
    exclude_ids = {pid for batch in history for pid in batch} - set(pinned_ids)

    # ── 새 설문(v2) / 구 설문(v1) 공용 파싱 ─────
    is_new_survey = 'duration_type' in survey or 'companions' in survey

    if is_new_survey:
        interests     = survey.get('interests', [])
        duration_type = survey.get('duration_type', 'half')
        survey_region = survey.get('region', 'any')
        companions    = survey.get('companions', '')
        purpose       = survey.get('purpose', '')
        duration      = _DURATION_MAP.get(duration_type, 4)

        has_all = 'all' in interests or 'any' in interests
        eras, categories = [], []
        if not has_all:
            for interest in interests:
                if interest in _ERA_MAP:
                    for e in _ERA_MAP[interest]:
                        if e not in eras:
                            eras.append(e)
                elif interest in _CAT_MAP:
                    cat = _CAT_MAP[interest]
                    if cat not in categories:
                        categories.append(cat)
    else:
        # 구 설문 형식 호환
        interests     = survey.get('interests', [])
        duration      = survey.get('duration', 3)
        survey_region = survey.get('region', 'any')
        companions    = survey.get('visitors', '')
        purpose       = survey.get('activity', '')
        duration_type = 'half'
        eras          = [e for e in survey.get('eras', []) if e != 'any']
        categories    = [i for i in interests if i in ('historic', 'museum', 'palace')]

    region = _REGION_DB_MAP.get(survey_region, '')
    radius = _auto_radius_km(duration, survey.get('transport', 'walk'))

    # pinned 장소가 있으면 그 좌표 중심(centroid)을 기준으로 주변 장소를 채운다.
    pinned_places = list(Place.objects.select_related('theme').filter(pk__in=pinned_ids)) if pinned_ids else []
    pinned_ids_set = {p.id for p in pinned_places}
    if pinned_places:
        center = (
            sum(float(p.latitude) for p in pinned_places) / len(pinned_places),
            sum(float(p.longitude) for p in pinned_places) / len(pinned_places),
        )
    else:
        center = _REGION_CENTER.get(survey_region, (37.5665, 126.9780))

    # ── 후보 장소 조회 ────────────────────────────
    places_qs = Place.objects.select_related('theme').all()
    if region and not pinned_places:
        places_qs = places_qs.filter(region=region)
    if eras:
        places_qs = places_qs.filter(theme__era__in=eras)
    if categories:
        places_qs = places_qs.filter(category__in=categories)
    if exclude_ids:
        places_qs = places_qs.exclude(pk__in=exclude_ids)
    if pinned_ids_set:
        places_qs = places_qs.exclude(pk__in=pinned_ids_set)

    candidates = list(places_qs[:50])

    # ── 범위 필터링 (Haversine) ───────────────────
    # radius는 동선 지름(km). 지역 중심에서 radius/2 이내 장소만 포함해
    # 어떤 두 장소도 최대 radius km 이내에 위치하도록 한다.
    filter_r = radius / 2
    if radius < 50:
        candidates = [
            p for p in candidates
            if _haversine(center[0], center[1], float(p.latitude), float(p.longitude)) <= filter_r
        ]

    # 범위 내 장소가 3개 미만이면 지름 2배로 재시도
    if len(candidates) < 3:
        fallback = list(places_qs[:50])
        wider = [
            p for p in fallback
            if _haversine(center[0], center[1], float(p.latitude), float(p.longitude)) <= filter_r * 2
        ]
        if len(wider) > len(candidates):
            candidates = wider

    if not pinned_places:
        if not candidates:
            return Response({'places': [], 'message': f'동선 범위 {radius:.0f}km 내 장소가 없습니다. 범위를 늘려 다시 시도해 주세요.'})
        if len(candidates) < 3:
            return Response({'places': [], 'message': '반경 내 장소가 부족합니다. 반경을 넓혀주세요.'})

    if candidates:
        selected_places = _call_ai_recommend(survey, candidates, exclude_ids)
        if selected_places is None:
            selected_places = _rank_candidates(candidates, eras, categories, duration_type, companions, purpose, interests)
    else:
        selected_places = []

    # pinned(꼭 가고 싶은) 장소는 맨 앞에 고정 — 트림 단계에서 절대 빠지지 않는다.
    pinned_with_reason = [(p, '직접 선택한 필수 방문지') for p in pinned_places]
    selected_places = pinned_with_reason + selected_places

    # 관람시간 + 이동시간(설문에서 선택한 이동수단 기준 추정) 합이 설문 소요시간 이내가 되도록
    # 추천 순서대로 트림하고, 관람시간 대비 이동시간이 너무 긴 비효율적인 장소는 제외한다.
    transport = survey.get('transport', 'walk')
    selected_places = _trim_by_time_budget(selected_places, duration, transport, pinned_count=len(pinned_with_reason))

    history.append([p.id for p, _ in selected_places])
    request.session['ai_recommend_history'] = history

    result = [
        {
            'id':             p.id,
            'name':           p.name,
            'address':        p.address,
            'latitude':       float(p.latitude),
            'longitude':      float(p.longitude),
            'category':       p.category,
            'category_display': p.get_category_display(),
            'region':         p.region,
            'region_display': p.get_region_display(),
            'is_indoor':      p.is_indoor,
            'image_url':      p.image_url,
            'reason':         reason,
        }
        for p, reason in selected_places
    ]
    return Response({'places': result})


# -----------------------------------------------
# 동선 스토리텔링 (Gemini API)
# -----------------------------------------------
@api_view(['POST'])
def route_story(request):
    """
    POST /api/places/route-story/
    동선 장소들을 잇는 여행 스토리텔링 내러티브 생성
    body: { place_ids: [1, 2, 3, ...] }
    """
    place_ids = request.data.get('place_ids', [])
    if not place_ids:
        return Response({'error': '장소를 선택해 주세요.'}, status=400)

    places_qs = {p.id: p for p in Place.objects.filter(pk__in=place_ids).select_related('theme')}
    ordered = [places_qs[pid] for pid in place_ids if pid in places_qs]

    if not ordered:
        return Response({'error': '장소를 찾을 수 없습니다.'}, status=404)

    client = _get_ai_client()
    if client is None:
        return Response({'error': 'AI 기능이 설정되지 않았습니다.'}, status=503)

    ERA_KO = {
        'three_kingdoms': '삼국시대', 'goryeo': '고려시대', 'joseon': '조선시대',
        'japanese': '일제강점기', 'modern': '현대',
    }
    CAT_KO = {'historic': '역사 유적', 'museum': '박물관·미술관', 'palace': '궁궐·사찰'}

    places_desc = '\n'.join(
        f'{i+1}. {p.name}'
        f' ({CAT_KO.get(p.category, p.category)}'
        f' | {ERA_KO.get(p.theme.era if p.theme else "", "시대 미상")})'
        f'{(" — " + p.description[:60]) if p.description else ""}'
        for i, p in enumerate(ordered)
    )

    prompt = (
        '당신은 한국 문화유산을 정말 잘 알고 있는 80대 할머니입니다.\n\n'
        f'오늘의 동선:\n{places_desc}\n\n'
        '이 장소들을 방문 순서대로 자연스럽게 잇는 여행 스토리텔링 내러티브를 작성하세요.\n\n'
        '요구사항:\n'
        '- 8~10 문장의 하나의 단락으로 작성\n'
        '- 역사적 사실과 감성적 묘사를 균형 있게 담을 것\n'
        '- 방문자가 시간 여행을 하는 듯한 몰입감을 줄 것\n'
        '- 장소명은 「」로 강조 (예: 「경복궁」)\n'
        '- 순수 텍스트만 출력 (JSON·마크다운 없이)\n'
        '- 손자에게 전래동화를 풀어주듯 사용자에게 이야기를 풀어주세요 \n'
        '- 기승전결을 잘 지켜서 하나의 이야기처럼 엮어줘 \n'
        '- 절대 역사적 사실을 왜곡해서는 안돼'
    )

    try:
        completion = client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            max_tokens=600,
            extra_body={'reasoning_effort': 'none'},
            messages=[{'role': 'user', 'content': prompt}],
        )
        return Response({'story': completion.choices[0].message.content.strip()})
    except Exception:
        return Response({'error': '스토리 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.'}, status=503)


@require_http_methods(['POST'])
def survey_reset(request):
    """POST /api/survey/reset/ — 설문 세션 초기화"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
    request.session.pop('survey_done', None)
    request.session.pop('survey_data', None)
    request.session.pop('ai_recommend_history', None)
    return JsonResponse({'status': 'ok'})


# -----------------------------------------------
# 동선 최적화
# -----------------------------------------------
def _haversine_km(p1, p2):
    R = 6371
    lat1, lon1 = math.radians(float(p1.latitude)), math.radians(float(p1.longitude))
    lat2, lon2 = math.radians(float(p2.latitude)), math.radians(float(p2.longitude))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _shortest_route(places):
    """총 이동거리가 최소인 방문 순서 반환 (N≤8 브루트포스, N>8 최근접 휴리스틱)."""
    n = len(places)
    if n <= 1:
        return list(places)

    def total_dist(order):
        return sum(_haversine_km(order[i], order[i + 1]) for i in range(len(order) - 1))

    if n <= 8:
        best = min(permutations(places), key=total_dist)
        return list(best)

    # 최근접 이웃 — 모든 시작점 시도
    best_order, best_dist = None, float('inf')
    for start in range(n):
        unvisited = list(places)
        cur = unvisited.pop(start)
        order = [cur]
        while unvisited:
            nxt = min(unvisited, key=lambda p: _haversine_km(cur, p))
            unvisited.remove(nxt)
            order.append(nxt)
            cur = nxt
        d = total_dist(order)
        if d < best_dist:
            best_dist, best_order = d, order
    return best_order


@api_view(['POST'])
def route_optimize(request):
    """
    POST /api/places/route-optimize/
    좌표 기반 최단 동선 계산 + Gemini로 팁·요약 생성
    body: { place_ids: [1, 2, 3, ...] }
    """
    place_ids = request.data.get('place_ids', [])
    if not place_ids:
        return Response({'error': '장소를 선택해 주세요.'}, status=400)

    places_qs = {p.id: p for p in Place.objects.filter(pk__in=place_ids).select_related('theme')}
    raw = [places_qs[pid] for pid in place_ids if pid in places_qs]

    # 좌표로 최단 동선 계산
    geo_ordered = _shortest_route(raw)
    optimal_ids = [p.id for p in geo_ordered]

    client = _get_ai_client()
    if client is None or len(geo_ordered) <= 1:
        return Response({'order': optimal_ids, 'tips': {}, 'summary': ''})

    CAT_KO = {'historic': '역사 유적', 'museum': '박물관·미술관', 'palace': '궁궐·사찰'}
    places_data = [
        {
            'id': p.id,
            'name': p.name,
            'category': CAT_KO.get(p.category, p.category),
            'address': p.address,
            'indoor': '실내' if p.is_indoor else '실외',
        }
        for p in geo_ordered
    ]

    prompt = (
        '서울·경기 문화 여행 안내사입니다.\n\n'
        '아래는 이미 이동거리 최소화 순서로 정렬된 장소 목록입니다. '
        '각 장소의 핵심 방문 포인트를 한 문장씩 설명하고, 전체 동선을 한 줄로 요약하세요.\n\n'
        f'장소(순서 고정):\n{json.dumps(places_data, ensure_ascii=False)}\n\n'
        'JSON만 응답 (다른 텍스트 없이):\n'
        '{"tips": {"<id문자열>": "<팁>", ...}, "summary": "<동선 한 줄 요약>"}'
    )

    try:
        completion = client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            max_tokens=600,
            extra_body={'reasoning_effort': 'none'},
            messages=[{'role': 'user', 'content': prompt}],
        )
        text = completion.choices[0].message.content.strip()
        if '```' in text:
            text = re.sub(r'```(?:json)?', '', text).strip()
        result = json.loads(text)
        tips = {str(k): v for k, v in result.get('tips', {}).items()}
        return Response({'order': optimal_ids, 'tips': tips, 'summary': result.get('summary', '')})
    except Exception:
        return Response({'order': optimal_ids, 'tips': {}, 'summary': ''})


# -----------------------------------------------
# 카카오모빌리티 실제 도로 경로
# -----------------------------------------------
KAKAO_DIRECTIONS_URL = 'https://apis-navi.kakaomobility.com/v1/directions'
_WALK_MPS = 80 / 60  # 도보 분당 80m 가정 (직선 대체 시 사용)


def _kakao_directions_leg(origin, destination):
    """
    카카오모빌리티 자동차 길찾기 단일 구간 호출.
    origin/destination: (lat, lng) 튜플.
    성공 시 {'distance_m', 'duration_sec', 'path': [[lat, lng], ...]} 반환, 실패 시 None.
    """
    headers = {'Authorization': f'KakaoAK {settings.KAKAO_REST_KEY}'}
    params = {
        'origin': f'{origin[1]},{origin[0]}',
        'destination': f'{destination[1]},{destination[0]}',
        'priority': 'RECOMMEND',
        'road_details': 'true',
    }
    try:
        resp = requests.get(KAKAO_DIRECTIONS_URL, headers=headers, params=params, timeout=8)
        if not resp.ok:
            return None
        data = resp.json()
        routes = data.get('routes', [])
        if not routes or routes[0].get('result_code') != 0:
            return None
        route = routes[0]
        summary = route.get('summary', {})

        path = []
        for section in route.get('sections', []):
            for road in section.get('roads', []):
                vertexes = road.get('vertexes', [])
                for i in range(0, len(vertexes) - 1, 2):
                    lng, lat = vertexes[i], vertexes[i + 1]
                    path.append([lat, lng])
        if not path:
            path = [[origin[0], origin[1]], [destination[0], destination[1]]]

        return {
            'distance_m': summary.get('distance', 0),
            'duration_sec': summary.get('duration', 0),
            'path': path,
        }
    except Exception:
        return None


_TAXI_BASE_FARE = 4800        # 서울 중형택시 기본요금(원, 1.6km까지)
_TAXI_BASE_DISTANCE_M = 1600
_TAXI_DIST_UNIT_M = 132       # 132m마다
_TAXI_DIST_UNIT_WON = 100     # 100원 추가


def _estimate_taxi_fare(distance_m):
    """
    서울 중형택시 기준요금표 기반 대략적인 예상 거리요금(원).
    시간요금(저속/정차)·심야·지역별 차이는 반영하지 않은 단순 추정치.
    """
    if distance_m <= _TAXI_BASE_DISTANCE_M:
        return _TAXI_BASE_FARE
    extra_units = math.ceil((distance_m - _TAXI_BASE_DISTANCE_M) / _TAXI_DIST_UNIT_M)
    return _TAXI_BASE_FARE + extra_units * _TAXI_DIST_UNIT_WON


@api_view(['POST'])
def route_directions(request):
    """
    POST /api/places/route-directions/
    body: { place_ids: [순서가 고정된 장소 id 목록] }
    카카오모빌리티 자동차 길찾기로 구간별 실제 도로 경로(polyline)·거리·소요시간을 계산.
    구간별·총 예상 택시요금(거리 기준 추정치)도 함께 반환.
    구간 호출이 실패하면 해당 구간만 직선 거리로 대체(ok: false로 표시).
    """
    place_ids = request.data.get('place_ids', [])
    if len(place_ids) < 2:
        return Response({'error': '장소가 2곳 이상 필요합니다.'}, status=400)

    places_qs = {p.id: p for p in Place.objects.filter(pk__in=place_ids)}
    ordered = [places_qs[pid] for pid in place_ids if pid in places_qs]
    if len(ordered) < 2:
        return Response({'error': '장소를 찾을 수 없습니다.'}, status=404)

    legs = []
    total_distance = 0
    total_duration = 0
    total_fare = 0
    any_ok = False

    for a, b in zip(ordered, ordered[1:]):
        origin = (float(a.latitude), float(a.longitude))
        destination = (float(b.latitude), float(b.longitude))
        result = _kakao_directions_leg(origin, destination)

        if result is None:
            dist_m = round(_haversine_km(a, b) * 1000)
            leg = {
                'from_id': a.id, 'to_id': b.id, 'ok': False,
                'distance_m': dist_m,
                'duration_sec': round(dist_m / _WALK_MPS),
                'path': [[origin[0], origin[1]], [destination[0], destination[1]]],
            }
        else:
            leg = {'from_id': a.id, 'to_id': b.id, 'ok': True, **result}
            any_ok = True

        leg['fare_won'] = _estimate_taxi_fare(leg['distance_m'])
        legs.append(leg)
        total_distance += leg['distance_m']
        total_duration += leg['duration_sec']
        total_fare += leg['fare_won']

    return Response({
        'legs': legs,
        'total_distance_m': total_distance,
        'total_duration_sec': total_duration,
        'total_fare_won': total_fare,
        'ok': any_ok,
    })


# -----------------------------------------------
# 이동수단별 구간 정보 (도보/자전거 — OSRM 실제 경로)
# -----------------------------------------------
_TRANSPORT_KO = {'walk': '도보', 'bike': '자전거'}
_TRANSPORT_SPEED_KMH = {'walk': 4.8, 'bike': 15}

OSRM_BASE_URL = 'https://router.project-osrm.org/route/v1'
_OSRM_PROFILE = {'walk': 'foot', 'bike': 'bike'}


def _osrm_route_leg(origin, destination, profile):
    """
    OSRM 공개 서버로 단일 구간의 실제 경로(도로/보행로를 따라가는 polyline)를 조회.
    origin/destination: (lat, lng) 튜플.
    성공 시 {'distance_m', 'path': [[lat, lng], ...]} 반환, 실패 시 None.
    (OSRM 공개 데모 서버의 foot/bike duration 값은 비현실적으로 빨라 신뢰할 수 없으므로 거리만 사용한다)
    """
    coords = f'{origin[1]},{origin[0]};{destination[1]},{destination[0]}'
    url = f'{OSRM_BASE_URL}/{profile}/{coords}'
    try:
        resp = requests.get(
            url,
            params={'overview': 'full', 'geometries': 'geojson'},
            timeout=8,
        )
        if not resp.ok:
            return None
        data = resp.json()
        if data.get('code') != 'Ok' or not data.get('routes'):
            return None
        route = data['routes'][0]
        path = [[lat, lng] for lng, lat in route['geometry']['coordinates']]
        if not path:
            return None
        return {
            'distance_m': route.get('distance', 0),
            'path': path,
        }
    except Exception:
        return None


def compute_route_path(ordered_places, transport_mode):
    """
    코스를 생성/수정하는 시점에 실제 이동수단 기준 경로(자동차=카카오모빌리티, 도보/자전거=OSRM)를
    한 번만 계산해 Route.path_data에 저장해둔다. 조회할 때마다 외부 API를 다시 호출하지 않고
    저장된 좌표로 곧장 곡선 경로를 그릴 수 있게 하기 위함.
    대중교통/기차는 실제 경로 API가 없어 직선 좌표를 그대로 둔다(기존 route_directions/
    route_transit_info의 구간 실패 시 대체 로직과 동일한 기준).
    """
    legs = []
    for a, b in zip(ordered_places, ordered_places[1:]):
        origin = (float(a.latitude), float(a.longitude))
        destination = (float(b.latitude), float(b.longitude))
        path = None

        if transport_mode == 'car':
            result = _kakao_directions_leg(origin, destination)
            if result:
                path = result['path']
        elif transport_mode in _OSRM_PROFILE:
            result = _osrm_route_leg(origin, destination, _OSRM_PROFILE[transport_mode])
            straight_m = _haversine_km(a, b) * 1000
            if result and (straight_m <= 0 or result['distance_m'] <= straight_m * 3):
                path = result['path']

        if not path:
            path = [[origin[0], origin[1]], [destination[0], destination[1]]]
        legs.append({'from_id': a.id, 'to_id': b.id, 'path': path})

    return legs


@api_view(['POST'])
def route_transit_info(request):
    """
    POST /api/places/route-transit-info/
    body: { place_ids: [순서 고정된 장소 id 목록], transport: walk|bike }
    OSRM 공개 서버로 구간별 실제 경로(polyline)·거리를 조회하고, 소요시간은 실거리 ÷ 평균 속력으로 계산.
    OSRM 조회 실패 시 해당 구간만 직선 거리로 대체(path_ok: false).
    """
    place_ids = request.data.get('place_ids', [])
    transport = request.data.get('transport', 'walk')
    if transport not in _TRANSPORT_KO:
        transport = 'walk'
    if len(place_ids) < 2:
        return Response({'error': '장소가 2곳 이상 필요합니다.'}, status=400)

    places_qs = {p.id: p for p in Place.objects.filter(pk__in=place_ids)}
    ordered = [places_qs[pid] for pid in place_ids if pid in places_qs]
    if len(ordered) < 2:
        return Response({'error': '장소를 찾을 수 없습니다.'}, status=404)

    transport_ko = _TRANSPORT_KO[transport]
    speed_kmh = _TRANSPORT_SPEED_KMH[transport]
    osrm_profile = _OSRM_PROFILE[transport]

    legs = []
    osrm_ok = True
    for a, b in zip(ordered, ordered[1:]):
        origin = (float(a.latitude), float(a.longitude))
        destination = (float(b.latitude), float(b.longitude))

        straight_m = _haversine_km(a, b) * 1000
        osrm_result = _osrm_route_leg(origin, destination, osrm_profile)
        # OSRM 공개 데모 서버는 보행자 횡단 데이터가 부실한 구간에서
        # 실제로 유턴을 포함한 비정상 우회 경로를 반환하는 경우가 있다.
        # 직선 거리 대비 너무 먼 경로는 신뢰하지 않고 직선으로 대체한다.
        if osrm_result is not None and straight_m > 0 and osrm_result['distance_m'] > straight_m * 3:
            osrm_result = None
        if osrm_result is None:
            osrm_ok = False
            distance_m = round(straight_m)
            path = [[origin[0], origin[1]], [destination[0], destination[1]]]
            path_ok = False
        else:
            distance_m = round(osrm_result['distance_m'])
            path = osrm_result['path']
            path_ok = True

        eta_min = max(1, round(distance_m / 1000 / speed_kmh * 60))
        legs.append({
            'from_id': a.id, 'to_id': b.id,
            'eta_min': eta_min,
            'method': f'{transport_ko} 이동',
            'path': path,
            'path_ok': path_ok,
            'distance_m': distance_m,
        })

    return Response({'legs': legs, 'ok': osrm_ok, 'path_ok': osrm_ok})
