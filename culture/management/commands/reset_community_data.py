import random

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Profile, UserFollow
from culture.models import Bookmark, Place, Review, Route, RouteComment, RouteLike, RoutePlace, Theme
from culture.views import _DEFAULT_VISIT_MIN, _VISIT_MIN, _haversine_km, _shortest_route

# 도보/자전거 속력은 culture/views.py의 추천 로직과 동일 기준(_REC_TRANSPORT_SPEED_KMH)을 따른다.
# transit/train은 그 모듈에 없는 보조 수단이라 여기서만 보수적으로 추정한다.
SPEED_KMH = {'walk': 4.8, 'bike': 15, 'transit': 20, 'car': 25, 'train': 50}
# 실제 도로/노선은 직선이 아니므로 직선거리(haversine)에 곱하는 굴곡 보정 — 값이 클수록 더 구불구불.
CURVE_FACTOR = {'walk': 1.15, 'bike': 1.2, 'transit': 1.35, 'car': 1.3, 'train': 1.15}

ADJ = ['고요', '부지런', '명랑', '다정', '용감', '느긋', '상냥', '씩씩', '발랄', '은은',
       '소소', '포근', '엉뚱', '단정', '활기', '여유', '엉큼', '담담', '쾌활', '차분']
NOUN = ['산책러', '여행자', '탐험가', '기록가', '덕후', '마니아', '나들이꾼', '수집가',
        '방랑자', '관찰자', '워커', '러버', '집사', '학도', '동무', '길잡이']

TITLE_TEMPLATES = [
    '{p0}에서 시작하는 {region} {era}코스',
    '{region} {transport} 여행 — {p0}부터 {p1}까지',
    '{era}따라가는 {region} 나들이',
    '{p0}와 {p1}, {region} 반나절 코스',
    '{transport}로 둘러보는 {region} {era}투어',
]

REVIEW_TEMPLATES = {
    5: ['{name}, 정말 인상 깊었어요! 다시 가고 싶습니다.', '{name} 강추합니다. 동선도 효율적이었어요.', '{name}에서 좋은 시간 보냈어요. 최고!'],
    4: ['{name} 괜찮았어요, 한 번쯌 가볼 만해요.', '{name} 생각보다 좋았습니다.'],
    3: ['{name} 평범했어요. 그냥 그랬습니다.'],
    2: ['{name} 기대보다는 아쉬웠어요.'],
    1: ['{name} 별로였습니다. 추천하지 않아요.'],
}

COMMENT_TEMPLATES = [
    '여기 진짜 좋았어요!', '동선이 효율적이네요.', '다음에 가보려고요, 감사합니다.',
    '사진 찍기 좋은 곳이 많은 것 같아요.', '저도 비슷한 코스로 다녀왔어요!', '거리도 적당하고 알찬 코스네요.',
]


def _gen_nicknames(n):
    combos = [a + b for a in ADJ for b in NOUN]
    random.shuffle(combos)
    result, used = [], set()
    i = 0
    while len(result) < n:
        base = combos[i % len(combos)]
        nick = base if i < len(combos) else f'{base}{i // len(combos)}'
        i += 1
        if nick in used or len(nick) > 10:
            continue
        used.add(nick)
        result.append(nick)
    return result


class Command(BaseCommand):
    help = (
        '장소(Place)·테마(Theme) 데이터는 그대로 두고, 유저 관련 데이터(계정/리뷰/북마크/팔로우/코스 등)를 '
        '전부 삭제한 뒤 master 관리자 1명 + 일반 유저 100명 + 공유 코스 90개를 새로 생성한다.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=100)
        parser.add_argument('--routes', type=int, default=90)

    @transaction.atomic
    def handle(self, *args, **kwargs):
        n_users = kwargs['users']
        n_routes = kwargs['routes']

        # ── 유저 전부 삭제: CASCADE로 Profile/Review/Route/RoutePlace/Bookmark/RouteLike/RouteComment/UserFollow 전부 함께 삭제됨.
        # Place/Theme은 User를 참조하지 않으므로 영향 없음.
        deleted_count = User.objects.all().count()
        User.objects.all().delete()
        self.stdout.write(f'기존 유저 {deleted_count}명 및 연관 데이터 삭제 완료.')

        call_command('create_legend_account', username='master', password='master123')

        nicknames = _gen_nicknames(n_users)
        users = []
        for i in range(1, n_users + 1):
            user = User.objects.create_user(username=f'user{i:03d}', password='user1234')
            Profile.objects.create(user=user, nickname=nicknames[i - 1])
            users.append(user)
        self.stdout.write(f'일반 유저 {len(users)}명 생성 완료.')

        # ── 팔로우 ──
        for user in users:
            others = [u for u in users if u != user]
            for target in random.sample(others, k=random.randint(0, 8)):
                UserFollow.objects.get_or_create(follower=user, following=target)

        # ── 북마크: 장소 0~8개, 코스는 라우트 생성 이후에 추가 ──
        all_places = list(Place.objects.select_related('theme').all())
        for user in users:
            for place in random.sample(all_places, k=random.randint(0, 8)):
                Bookmark.objects.get_or_create(user=user, place=place)

        # ── 리뷰: 유저당 0~5개, 평점은 긍정적으로 치우친 분포 ──
        rating_pool = [5] * 8 + [4] * 7 + [3] * 3 + [2] * 1 + [1] * 1
        for user in users:
            for place in random.sample(all_places, k=random.randint(0, 5)):
                rating = random.choice(rating_pool)
                content = random.choice(REVIEW_TEMPLATES[rating]).format(name=place.name)
                Review.objects.create(place=place, user=user, rating=rating, content=content)

        self.stdout.write('팔로우/북마크/리뷰 생성 완료.')

        # ── 공유 코스 90개 ──
        seoul_places = [p for p in all_places if p.region == 'seoul']
        gyeonggi_places = [p for p in all_places if p.region == 'gyeonggi']
        era_ko = dict(Theme.ERA_CHOICES)
        transport_ko = {'walk': '도보', 'bike': '자전거', 'transit': '대중교통', 'car': '자동차', 'train': '기차'}

        for _ in range(n_routes):
            mixed = random.random() < 0.15
            if mixed or not seoul_places or not gyeonggi_places:
                pool = all_places
                region_label = '서울·경기'
            elif random.random() < 0.6:
                pool = seoul_places
                region_label = '서울'
            else:
                pool = gyeonggi_places
                region_label = '경기'

            cluster_size = random.choice([3, 3, 4, 4, 5, 6])
            cluster_size = min(cluster_size, len(pool))
            seed = random.choice(pool)
            nearest = sorted(pool, key=lambda p: _haversine_km(seed, p))[:cluster_size]

            span_km = max(
                (_haversine_km(a, b) for i, a in enumerate(nearest) for b in nearest[i + 1:]),
                default=0,
            )
            if span_km <= 3:
                transport = random.choice(['walk', 'walk', 'bike'])
            elif span_km <= 8:
                transport = random.choice(['walk', 'bike', 'transit'])
            elif span_km <= 15:
                transport = random.choice(['bike', 'transit', 'car'])
            else:
                transport = 'car' if not mixed else random.choice(['car', 'train'])

            ordered = _shortest_route(nearest)
            curve = CURVE_FACTOR[transport]
            speed = SPEED_KMH[transport]

            leg_km = [_haversine_km(ordered[i], ordered[i + 1]) * curve for i in range(len(ordered) - 1)]
            travel_min = sum(km / speed * 60 for km in leg_km)
            visit_min = sum(_VISIT_MIN.get(p.category, _DEFAULT_VISIT_MIN) for p in ordered)
            total_distance_m = round(sum(leg_km) * 1000)
            total_time_min = round(travel_min + visit_min)

            eras = {p.theme.era for p in ordered if p.theme_id}
            if len(eras) == 1:
                mode = 'theme'
            else:
                mode = random.choice(['distance', 'time'])

            era_label = f'{era_ko[next(iter(eras))]} ' if len(eras) == 1 else ''
            title = random.choice(TITLE_TEMPLATES).format(
                p0=ordered[0].name, p1=ordered[-1].name if len(ordered) > 1 else ordered[0].name,
                region=region_label, era=era_label, transport=transport_ko[transport],
            )[:100]

            author = random.choice(users)
            route = Route.objects.create(
                user=author, title=title, mode=mode, transport_mode=transport,
                total_distance=total_distance_m, total_time=total_time_min,
                is_shared=True, is_footprint=False,
            )
            RoutePlace.objects.bulk_create([
                RoutePlace(route=route, place=p, order=i) for i, p in enumerate(ordered, start=1)
            ])

            likers = random.sample([u for u in users if u != author], k=random.randint(0, min(40, len(users) - 1)))
            RouteLike.objects.bulk_create([RouteLike(user=u, route=route) for u in likers])
            route.like_count = len(likers)
            route.save(update_fields=['like_count'])

            commenters = random.sample([u for u in users if u != author], k=random.randint(0, 4))
            RouteComment.objects.bulk_create([
                RouteComment(route=route, user=u, content=random.choice(COMMENT_TEMPLATES)) for u in commenters
            ])

        self.stdout.write(f'공유 코스 {n_routes}개 생성 완료.')

        # ── 코스 북마크: 코스 생성 후 일부 유저가 다른 공유 코스를 북마크 ──
        shared_routes = list(Route.objects.filter(is_shared=True))
        for user in users:
            candidates = [r for r in shared_routes if r.user != user]
            for route in random.sample(candidates, k=min(random.randint(0, 3), len(candidates))):
                Bookmark.objects.get_or_create(user=user, route=route)

        call_command('seed_demo_footprints')
        call_command('backfill_route_paths')

        self.stdout.write(self.style.SUCCESS(
            f'완료: master(관리자, pw=master123) + 일반 유저 {n_users}명(pw=user1234) + 공유 코스 {n_routes}개 생성.'
        ))
