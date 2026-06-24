from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from accounts.models import Profile, UserFollow
from ai.views import SCOLDING_MESSAGES
from culture.models import Bookmark, Place, Review, Route, RouteComment, RouteLike, RoutePlace


class Command(BaseCommand):
    help = '모든 칭호(여행 기반 + 재미 요소)를 달성하고 모든 기능에 접근 가능한 슈퍼유저 데모 계정을 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='legend')
        parser.add_argument('--password', default='Legend1234!')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']

        user, _ = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        places = list(Place.objects.all())

        # ── 여행 기반 칭호 (장소 531곳 전부 발자취) ──
        title = '모든 칭호 달성 발자취'
        Route.objects.filter(user=user, is_footprint=True, title=title).delete()
        route = Route.objects.create(
            user=user, title=title, mode='distance', is_shared=False, is_footprint=True,
        )
        RoutePlace.objects.bulk_create([
            RoutePlace(route=route, place=p, order=i) for i, p in enumerate(places, start=1)
        ])

        # ── 도보·자전거 거리 칭호 ──
        Route.objects.filter(user=user, is_footprint=True, title__startswith='칭호용 이동거리').delete()
        for mode, label, distance_m in [('walk', '도보', 43000), ('bike', '자전거', 101000)]:
            dist_route = Route.objects.create(
                user=user, title=f'칭호용 이동거리({label})', mode='distance',
                transport_mode=mode, total_distance=distance_m,
                is_shared=False, is_footprint=True,
            )
            RoutePlace.objects.bulk_create([
                RoutePlace(route=dist_route, place=places[i], order=i + 1) for i in range(2)
            ])

        # ── 공유 코스 5개 (코스 디자이너) ──
        Route.objects.filter(user=user, title__startswith='전설의 코스').delete()
        for i in range(5):
            shared_route = Route.objects.create(
                user=user, title=f'전설의 코스 {i + 1}', mode='theme',
                is_shared=True, is_footprint=False,
            )
            RoutePlace.objects.bulk_create([
                RoutePlace(route=shared_route, place=places[i * 2 + j], order=j + 1) for j in range(2)
            ])

        # ── 댓글 20개 (댓글 수다쟁이) ──
        comment_target_route = Route.objects.exclude(user=user).first() or route
        RouteComment.objects.filter(user=user, content__startswith='[칭호용]').delete()
        RouteComment.objects.bulk_create([
            RouteComment(route=comment_target_route, user=user, content=f'[칭호용] 정말 멋진 코스네요 {i + 1}')
            for i in range(20)
        ])

        # ── 좋아요 20개 (좋아요 난사범) ──
        RouteLike.objects.filter(user=user).delete()
        like_targets = list(Route.objects.exclude(user=user)[:20])
        for r in like_targets:
            RouteLike.objects.get_or_create(user=user, route=r)

        # ── 북마크 30개 (북마크 폭주족) ──
        Bookmark.objects.filter(user=user, place__isnull=False).delete()
        for p in places[:30]:
            Bookmark.objects.get_or_create(user=user, place=p)

        # ── 리뷰: 5점 10개(+장문 리뷰어 겸용) / 1점 5개 (호평 제조기/독설가) ──
        Review.objects.filter(user=user, content__startswith='[칭호용]').delete()
        long_text = '[칭호용] ' + '정말 인상 깊은 곳이었습니다. ' * 20
        Review.objects.bulk_create([
            Review(place=places[i], user=user, rating=5, content=long_text) for i in range(10)
        ])
        Review.objects.bulk_create([
            Review(place=places[10 + i], user=user, rating=1, content='[칭호용] 별로였습니다.') for i in range(5)
        ])

        # ── 팔로우/팔로워 10명씩 (마당발/문화 인플루언서) ──
        others = list(User.objects.exclude(id=user.id)[:10])
        UserFollow.objects.filter(follower=user).delete()
        UserFollow.objects.filter(following=user).delete()
        for other in others:
            UserFollow.objects.get_or_create(follower=user, following=other)
            UserFollow.objects.get_or_create(follower=other, following=user)

        # ── 프로필: 닉네임·사진(자기관리 만렙), 나리와의 대화 기록 ──
        profile, _ = Profile.objects.get_or_create(user=user)
        if not profile.nickname:
            profile.nickname = f'{username}_전설'
        if not profile.profile_image:
            with open('culture/static/culture/images/default_profile.png', 'rb') as f:
                profile.profile_image.save('legend_profile.png', ContentFile(f.read()), save=False)
        profile.scolded_message_ids = list(range(len(SCOLDING_MESSAGES)))
        profile.chat_count = 100
        profile.night_chat_count = 5
        profile.selected_badge = 'heritage_conqueror'
        profile.save()

        self.stdout.write(self.style.SUCCESS(
            f'super account ready - username: {username} / password: {password} / places: {len(places)} / all badges earned'
        ))
