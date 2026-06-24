import json
import random
import re
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods


def login_required_json(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def _unavailable():
    return JsonResponse({'error': '현재 사용할 수 없는 기능입니다.'}, status=503)


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


def _parse_json_body(request):
    try:
        return json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _strip_json_fence(text):
    if '```' in text:
        text = re.sub(r'```(?:json)?', '', text).strip()
    return text


GUARDRAIL_SYSTEM_PROMPT = (
    '당신은 한국 문화유산·여행 안내 챗봇의 질문 검수기입니다. '
    '사용자 질문이 한국의 문화유산, 역사, 여행지, 동선 등과 관련된 적절한 질문인지 판단하세요. '
    '인사, 안부, 챗봇 자신(이름·정체성 등)에 대한 가벼운 질문도 적절한 질문으로 취급하세요. '
    '욕설·혐오·개인정보 요청·서비스와 전혀 무관한 질문만 부적절합니다.\n\n'
    'JSON만 응답 (다른 텍스트 없이): {"is_valid": <true|false>, "reason": "<한 줄 이유>"}'
)

SCOLDING_MESSAGES = [
    '예끼 이놈! 그런 질문은 나리에게 어울리지 않느니라.',
    '무엄하도다! 문화유산과 무관한 질문은 삼가거라.',
    '허허, 그것은 답할 수 없는 질문이로구나. 다른 것을 물어보거라.',
    '고얀지고! 그런 질문은 나리도 답하기 어렵느니라.',
    '에잉, 쓸데없는 소리는 그만두고 문화 명소나 물어보거라.',
]


def _record_scold(user, idx):
    """유저가 받아본 SCOLDING_MESSAGES 인덱스를 누적 기록 (칭호 집계용)."""
    try:
        profile = user.profile
    except Exception:
        return
    seen = set(profile.scolded_message_ids or [])
    if idx not in seen:
        seen.add(idx)
        profile.scolded_message_ids = sorted(seen)
        profile.save(update_fields=['scolded_message_ids'])


def _record_chat(user):
    """나리와의 대화 횟수·심야(00~06시) 대화 횟수 누적 (칭호 집계용)."""
    try:
        profile = user.profile
    except Exception:
        return
    profile.chat_count += 1
    fields = ['chat_count']
    if timezone.localtime().hour < 6:
        profile.night_chat_count += 1
        fields.append('night_chat_count')
    profile.save(update_fields=fields)

CHAT_SYSTEM_PROMPT = """당신은 CultureRoute의 AI 도우미입니다.

CultureRoute는 서울·경기 지역의 문화유산 장소를 추천하고 경로를 안내하는 서비스입니다.

[주요 기능]
- 시대별 문화 장소 추천 (삼국시대, 고려, 조선 등)
- 날씨 기반 실내/실외 장소 추천
- 설문을 통한 개인 맞춤 추천
- 카카오맵 연동 경로 안내
- AI 챗봇을 통한 장소 질문 응답

[답변 지침]
- CultureRoute 서비스 기능과 문화유산 관련 질문에만 답변하세요.
- 무관한 질문은 정중히 거절하세요.
- 말투는 사극에서 사용할 법한 말투(반말)를 사용하세요. 어미는 "~느니라", "~이니라", "~거라", "~하시게", "~할 것이다" 등을 활용하세요.
- 모르는 정보는 추측하지 마세요."""


def _check_guardrail(client, question):
    """질문의 적절성을 OpenAI로 판단. 실패 시 통과(True) 처리."""
    try:
        completion = client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            max_tokens=200,
            extra_body={'reasoning_effort': 'none'},
            messages=[
                {'role': 'system', 'content': GUARDRAIL_SYSTEM_PROMPT},
                {'role': 'user', 'content': question},
            ],
        )
        result = json.loads(_strip_json_fence(completion.choices[0].message.content.strip()))
        return bool(result.get('is_valid', True)), result.get('reason', '')
    except Exception:
        return True, ''


@require_http_methods(['POST'])
@login_required_json
def guardrail(request):
    """POST /api/ai/guardrail/ — body: { question } → { is_valid, reason }"""
    client = _get_ai_client()
    if client is None:
        return _unavailable()

    question = _parse_json_body(request).get('question', '').strip()
    if not question:
        return JsonResponse({'error': '질문을 입력해 주세요.'}, status=400)

    is_valid, reason = _check_guardrail(client, question)
    return JsonResponse({'is_valid': is_valid, 'reason': reason})


@require_http_methods(['POST'])
@login_required_json
def chat(request):
    """
    POST /api/ai/chat/ — body: { question 또는 message, history? }
    → { is_valid, answer, reply, message } (reply/message는 answer와 동일값,
    플로팅 챗봇·저니모드 위젯이 reply/message 필드를 기대하기 때문)
    """
    client = _get_ai_client()
    if client is None:
        return _unavailable()

    data = _parse_json_body(request)
    question = (data.get('question') or data.get('message') or '').strip()
    if not question:
        return JsonResponse({'error': '질문을 입력해 주세요.'}, status=400)

    _record_chat(request.user)

    is_valid, reason = _check_guardrail(client, question)
    if not is_valid:
        idx = random.randrange(len(SCOLDING_MESSAGES))
        blocked_msg = SCOLDING_MESSAGES[idx]
        _record_scold(request.user, idx)
        return JsonResponse({'is_valid': False, 'reason': reason, 'reply': blocked_msg, 'message': blocked_msg})

    history = data.get('history', [])
    messages = [{'role': 'system', 'content': CHAT_SYSTEM_PROMPT}]
    for turn in history[-10:]:
        role = turn.get('role')
        if role in ('user', 'assistant') and turn.get('content'):
            messages.append({'role': role, 'content': turn['content']})
    messages.append({'role': 'user', 'content': question})

    try:
        completion = client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            max_tokens=500,
            extra_body={'reasoning_effort': 'none'},
            messages=messages,
        )
        answer = completion.choices[0].message.content.strip()
    except Exception:
        return JsonResponse({'error': '답변 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.'}, status=503)

    return JsonResponse({'is_valid': True, 'answer': answer, 'reply': answer, 'message': answer})


