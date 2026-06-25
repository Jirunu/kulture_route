from django.core.management.base import BaseCommand

from culture.models import Route
from culture.views import compute_route_path


class Command(BaseCommand):
    help = (
        '공유 코스(Route.is_shared=True)의 실제 이동 경로(path_data)를 계산해 저장한다. '
        '자동차=카카오모빌리티, 도보/자전거=OSRM 실제 도로 경로를 1회 계산해두면, '
        '커뮤니티에서 코스를 조회할 때마다 다시 호출하지 않고 곧장 곡선 경로를 그릴 수 있다.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true',
                             help='path_data가 이미 있는 코스도 다시 계산한다 (기본은 비어있는 코스만).')

    def handle(self, *args, **kwargs):
        routes = Route.objects.filter(is_shared=True).prefetch_related('routeplace_set__place')
        if not kwargs['all']:
            routes = [r for r in routes if not r.path_data]
        else:
            routes = list(routes)

        updated = 0
        for route in routes:
            places = [rp.place for rp in route.routeplace_set.all() if rp.place]
            if len(places) < 2:
                continue
            route.path_data = compute_route_path(places, route.transport_mode)
            route.save(update_fields=['path_data'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'{updated}개 공유 코스의 path_data를 계산했습니다.'))
