# -*- coding: utf-8 -*-
"""
스피드 배관공사 — 정적 사이트 생성기
실행: python3 build.py

생성물
- index.html
- services/<slug>.html            (4개)
- regions/<slug>.html             (17개 광역시·도)
- regions/<slug>/<구·군·시>/index.html          (전국 시·군·구 = 행정구)
- regions/<slug>/<구·군·시>/<행정동>.html        (전국 읍·면·동 = 행정동)
- sitemap.xml(색인) + sitemap-core.xml + sitemap-<slug>.xml
- robots.txt
- assets/img/*.svg                (플레이스홀더 20장)

행정구역 데이터: data/districts.json (17개 시·도 / 252개 시·군·구 / 3,556개 행정동)
※ 행정구역 명칭은 공공데이터(행정안전부 행정동 기준, 2025)에 근거한 사실 정보입니다.
"""
import os, html, json, re
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────
# 사이트 설정  ★ 실제 정보로 교체하세요 ★
# ─────────────────────────────────────────────
SITE = {
    "brand": "스피드 배관공사",
    "tagline": "전국 24시간 출동 배관·누수·하수구 전문",
    "domain": "https://www.speedbaegwan.co.kr",   # ★ 실제 도메인으로 교체
    "phone_display": "1668-0000",                 # ★ 실제 대표번호로 교체
    "phone_tel": "16680000",
    "email": "help@speedbaegwan.co.kr",           # ★ 교체
    "ceo": "홍길동",                               # ★ 대표자명
    "biz_no": "000-00-00000",                      # ★ 사업자등록번호
    "addr": "서울특별시 ○○구 ○○로 000",           # ★ 본사 주소
    "hours": "연중무휴 24시간",
    "emergency": "24시 긴급출동",           # 상단바·히어로 어필 문구
    "reserve": "24시 전화예약",             # 플로팅 전화예약 버튼 문구
    "founded": "2015",
}

# ─────────────────────────────────────────────
# 행정구역 데이터 로드
# DATA = [{slug, short, full, districts:[{name, disp, code, dongs:[{name, code}]}]}]
# ─────────────────────────────────────────────
with open(os.path.join(ROOT, "data", "districts.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)

# 네비/푸터/스키마용 광역시·도 튜플 (slug, short, full, districts)
REGIONS = [(d["slug"], d["short"], d["full"], d["districts"]) for d in DATA]

# 서비스 카테고리 (요청 키워드 전부 분배)
SERVICES = [
    {
        "slug": "nusu",
        "name": "누수탐지·누수공사",
        "short": "누수",
        "icon": "drop",
        "desc": "첨단 장비로 벽·바닥 속 숨은 누수 지점을 정확히 찾아 최소 파손으로 잡습니다.",
        "keywords": ["누수탐지", "누수공사", "수도누수", "욕실배관누수", "주방배관누수", "물샘", "수도수리"],
        "lead": "천장 얼룩, 원인 모를 수도요금 폭탄, 벽에서 새는 물. 스피드 배관공사는 청음식·가스식 누수탐지 장비로 정확한 지점을 찾아 불필요한 벽·바닥 철거 없이 시공합니다.",
        "points": [
            "비파괴 누수탐지로 벽·바닥 손상 최소화",
            "옥상·화장실·주방·보일러 배관 전 구간 대응",
            "탐지 후 즉시 공사까지 원스톱 처리",
            "누수 원인·비용 사전 고지 후 진행",
        ],
    },
    {
        "slug": "makhim",
        "name": "하수구·배관 막힘 뚫음",
        "short": "막힘",
        "icon": "clog",
        "desc": "역류하는 하수구, 내려가지 않는 변기·싱크대. 원인을 찾아 확실하게 뚫습니다.",
        "keywords": ["하수구막힘", "배관막힘", "싱크대하수구막힘", "세면대막힘", "배수구막힘",
                     "배수구뚫음", "주방배수구막힘", "변기막힘", "역류", "이물질제거"],
        "lead": "물이 내려가지 않거나 역류한다면 방치할수록 피해가 커집니다. 스프링·고압세척·관로내시경으로 막힘 원인을 확인하고 재발 없이 처리합니다.",
        "points": [
            "변기·싱크대·세면대·배수구 전 배관 막힘 해결",
            "관로 내시경으로 막힘·이물질 원인 정확 진단",
            "역류·악취 재발 방지 시공",
            "출동 전 예상 비용 안내",
        ],
    },
    {
        "slug": "gyoche",
        "name": "수전·변기·설비 교체",
        "short": "교체",
        "icon": "wrench",
        "desc": "노후 수전·변기·세면대 교체와 부속품 수리를 깔끔하게 마감합니다.",
        "keywords": ["수전교체", "싱크대수전교체", "화장실수전교체", "세면대교체",
                     "화장실변기교체", "변기부속품수리", "부품"],
        "lead": "물이 새는 낡은 수전, 흔들리는 변기, 깨진 세면대까지. 정품 부속으로 교체하고 마감까지 깔끔하게 처리합니다.",
        "points": [
            "주방·욕실 수전 및 변기·세면대 교체",
            "변기 부속(필밸브·플러시밸브 등) 부품 수리",
            "정품 자재 사용, 시공 후 마감 점검",
            "제품 추천부터 설치까지 한 번에",
        ],
    },
    {
        "slug": "seolbi",
        "name": "배관설비·고압세척·내시경",
        "short": "설비",
        "icon": "camera",
        "desc": "노후 배관 교체·설비 시공과 고압세척, 관로 내시경 진단을 제공합니다.",
        "keywords": ["배관설비", "고압세척", "내시경"],
        "lead": "오래된 건물 배관 교체, 정기 고압세척, 관로 내시경 진단까지. 상가·공장·주택 규모에 맞춰 설비 공사를 진행합니다.",
        "points": [
            "노후 급수·배수 배관 교체 및 신설",
            "고압세척으로 관 내부 슬러지·기름때 제거",
            "관로 내시경 촬영으로 배관 상태 리포트 제공",
            "주택·상가·공장 현장별 맞춤 견적",
        ],
    },
]

# 아이콘 (인라인 SVG path)
ICONS = {
    "drop": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2s6 6.5 6 11a6 6 0 1 1-12 0c0-4.5 6-11 6-11z"/></svg>',
    "clog": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v4H4z"/><path d="M8 8v6a4 4 0 0 0 8 0V8"/><path d="M12 18v3"/></svg>',
    "wrench": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a4 4 0 0 0 5 5l-1.6 1.6L21 16l-3 3-3.1-2.9L7 23l-2-2 7-8.9L9 9 6 6l2-2 4 4z"/></svg>',
    "camera": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7h4l2-2h8l2 2h4v12H2z"/><circle cx="12" cy="13" r="3.5"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.6A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.8 2z"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5z"/><path d="m9 12 2 2 4-4"/></svg>',
    "won": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6l3 9 5-9 5 9 3-9"/><path d="M3 11h18"/><path d="M3 14h18"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "badge": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="5"/><path d="M8.2 12 7 22l5-3 5 3-1.2-10"/></svg>',
    "user": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.5-6 8-6s8 2 8 6"/></svg>',
    "doc": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.5l2.9 5.9 6.5.95-4.7 4.58 1.11 6.47L12 17.9l-5.81 3.05 1.11-6.47-4.7-4.58 6.5-.95z"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
}

def esc(s): return html.escape(s, quote=True)

def logo_svg():
    return ICONS["drop"]

# ─────────────────────────────────────────────
# 행정동 그룹핑
#  숫자로 나뉜 동(세류1동·세류2동·세류3동, 면목3·8동 등)은
#  대표 1개(세류동, 면목동)로 묶어서 표기한다.
#  단, 가(街)형 행정동(종로1·2·3·4가동, 용산2가동)은 그 자체가
#  하나의 행정동이므로 묶지 않는다.
# ─────────────────────────────────────────────
_NUMDONG = re.compile(r'^(.+?)\d+(?:[·\-]\d+)*동$')

def dong_repr(name):
    """숫자 꼬리표를 뗀 대표 동 이름. 숫자형이 아니면 원래 이름."""
    m = _NUMDONG.match(name)
    if m and m.group(1):
        return m.group(1) + "동"
    return name

def dist_groups(dist):
    """
    한 시·군·구의 행정동을 대표 이름으로 묶어 순서를 유지한 리스트로 반환.
    반환: [{"repr": 대표이름, "members": [동 dict, ...]}]
    """
    groups, index = [], {}
    for d in dist["dongs"]:
        key = dong_repr(d["name"])
        g = index.get(key)
        if g is None:
            g = {"repr": key, "members": []}
            index[key] = g
            groups.append(g)
        g["members"].append(d)
    return groups

# ─────────────────────────────────────────────
# URL 헬퍼 (한글 경로는 퍼센트 인코딩)
# ─────────────────────────────────────────────
def q(s):
    return quote(s, safe="")

def region_url(slug):
    return f"regions/{slug}.html"

def city_url(slug, city):
    return f"regions/{slug}/{q(city)}/"

def gu_url(slug, city, gu):
    return f"regions/{slug}/{q(city)}/{q(gu)}/"

def unit_url(slug, city, gu):
    """동을 직접 담는 단위(구 또는 구 없는 시/군/구)의 목록 페이지 URL."""
    return gu_url(slug, city, gu) if gu else city_url(slug, city)

def dong_url(slug, city, gu, dong):
    return f"{unit_url(slug, city, gu)}{q(dong)}.html"

def path_prefix(depth):
    return "../" * depth

# ─────────────────────────────────────────────
# 행정 계층 구성
#  도 → 행정시 → 행정구 → 행정동  /  광역시 → 구·군 → 동
#  데이터의 sgg가 "○○시○○구"(예: 수원시장안구)면 시(city)와 구(gu)로 분리해
#  중간에 '행정시' 허브를 만든다. 그 외(김포시, 종로구, 강화군)는 시=단위 자체.
# ─────────────────────────────────────────────
_CITY_GU = re.compile(r'^(.+?시)(.+구)$')

def split_city_gu(sgg):
    m = _CITY_GU.match(sgg)
    if m:
        return m.group(1), m.group(2)
    return sgg, None

def build_hier():
    """
    [{"sido": sido dict,
      "cities": [{"name": 시/군/구, "gus": [{"name": 구, "dist": dist}], "unit": dist|None}]}]
    - gus 가 있으면 '행정시'(구를 가진 시). unit 은 None.
    - gus 가 비고 unit 이 있으면 구 없는 시/군/구(동을 직접 가짐).
    """
    hier = []
    for sido in DATA:
        cities, cmap = [], {}
        for dist in sido["districts"]:
            city, gu = split_city_gu(dist["name"])
            c = cmap.get(city)
            if c is None:
                c = {"name": city, "gus": [], "unit": None}
                cmap[city] = c
                cities.append(c)
            if gu:
                c["gus"].append({"name": gu, "dist": dist})
            else:
                c["unit"] = dist
        hier.append({"sido": sido, "cities": cities})
    return hier

HIER = build_hier()

def iter_units(sidoh):
    """한 시·도의 '동을 직접 담는 단위'들을 순회. yield (city, gu_or_None, dist)."""
    for c in sidoh["cities"]:
        if c["gus"]:
            for g in c["gus"]:
                yield c["name"], g["name"], g["dist"]
        else:
            yield c["name"], None, c["unit"]

# ─────────────────────────────────────────────
# 콘텐츠 변주 (중복·도어웨이 방지)
#  · 지역마다 결정적(deterministic)으로 다른 문장 조합을 선택해
#    같은 문구가 통째로 반복되지 않도록 한다.
#  · 지역 고유 사실(상위 행정구역·인접 동·포함 세부동·동 수·읍/면/동 특성)을
#    본문에 실어 페이지마다 실제로 다른 정보를 담는다.
# ─────────────────────────────────────────────
import zlib

def _hkey(*xs):
    return zlib.crc32("|".join(str(x) for x in xs).encode("utf-8"))

def pick(pool, *key):
    """키에 따라 결정적으로 pool 원소 하나 선택."""
    return pool[_hkey(*key) % len(pool)]

def picks(pool, n, *key):
    """키에 따라 결정적으로 서로 다른 n개 선택(순서도 지역마다 다름)."""
    n = min(n, len(pool))
    order = sorted(range(len(pool)), key=lambda i: _hkey(*key, i))
    return [pool[i] for i in order[:n]]

def area_kind(name):
    """행정동 이름의 접미로 지역 성격을 추정(사실 기반 문구용)."""
    if name.endswith("읍"):
        return "읍내 상권과 주변 주택·농가가 함께 있어 노후 배관·정화조 관련 시공이 잦은 지역"
    if name.endswith("면"):
        return "여러 마을(리)로 이루어져 단독주택·농가의 급배수와 지하수 설비 문의가 많은 지역"
    if name.endswith("가동"):
        return "오래된 상가·업무용 건물이 밀집해 배관 노후와 영업장 긴급 시공 수요가 많은 지역"
    if name.endswith("리"):
        return "농어촌 마을 특성상 정화조·단독배관 시공이 많은 지역"
    return "아파트 단지와 다세대·상가가 섞여 있어 누수·막힘 문의가 꾸준한 지역"

# 소제목 앞 도입 문장(히어로 아래) — {area} {dong}
DONG_INTRO = [
    "{area}에서 누수가 의심되거나 하수구·변기·싱크대가 막혔다면 스피드 배관공사로 연락하세요. {dong} 인근에 신속 출동해 원인을 정확히 진단하고 재발 없이 시공합니다.",
    "{dong} 일대에서 물이 새거나 잘 내려가지 않아 곤란하셨다면, {area} 어디든 빠르게 찾아가는 스피드 배관공사가 해결합니다. 진단 후 확정 견적을 먼저 알려드립니다.",
    "{dong}에서 천장 얼룩·수도요금 급증·배수 지연 같은 신호를 느끼셨다면 초기 대응이 중요합니다. {area} 전역에 24시간 출동해 원인부터 정확히 잡아드립니다.",
    "갑작스러운 누수·역류·막힘은 {dong}에서도 예고 없이 찾아옵니다. 스피드 배관공사는 {area}에 상시 대기하며 전화 한 통이면 가까운 기술자가 출동합니다.",
    "{area}의 주택·상가 어디든, {dong}의 배관 고민은 스피드 배관공사가 맡습니다. 불필요한 철거 없이 원인만 짚어 최소 시공으로 마무리합니다.",
    "{dong} 주민이라면 배관 문제로 더 미루지 마세요. 누수탐지·막힘 뚫음·설비 교체까지 {area} 현장에 맞춰 한 번에 처리하고 비용은 시공 전에 안내합니다.",
]

# 본문 첫 문단 — {area} {disp} {dong} {kind}
DONG_OPEN = [
    "{area}는 {kind}입니다. 오래된 주택부터 신축 건물까지 배관 상태가 제각각이라, 스피드 배관공사는 현장을 먼저 확인한 뒤 필요한 시공만 안내합니다.",
    "{dong} 일대는 {kind}으로, 계절이 바뀌거나 사용량이 늘면 누수·막힘이 잦아집니다. 증상에 맞춰 장비와 방법을 골라 재발을 줄입니다.",
    "{disp}에 속한 {dong}은(는) {kind}입니다. 같은 증상이라도 건물 구조에 따라 원인이 다르므로, 눈으로 확인한 뒤 정확히 처리합니다.",
    "{kind}인 {dong}에서는 배관 노후로 인한 문의가 특히 많습니다. 스피드 배관공사는 {area} 현장 특성을 감안해 손상을 최소화하는 방식으로 시공합니다.",
    "{area}에서 접수되는 문의는 주거·상가 환경이 섞여 있는 {kind} 특성을 반영합니다. 원인을 먼저 진단하고, 확정 견적에 동의하신 뒤에만 작업합니다.",
]

# 증상 안내 문장 풀(2개 선택)
SYMPTOMS = [
    "천장이나 벽의 얼룩, 원인 모를 수도요금 증가는 숨은 누수의 신호일 수 있습니다.",
    "물이 잘 내려가지 않거나 역류·악취가 있다면 배관 막힘을 의심해야 합니다.",
    "바닥이 자주 축축하거나 곰팡이가 반복된다면 배관 누수를 점검할 시점입니다.",
    "쓰지 않을 때도 수도 계량기가 돌아간다면 어딘가 물이 새고 있을 수 있습니다.",
    "변기·싱크대·세면대가 자주 막힌다면 관 내부 이물질이나 구조 문제일 수 있습니다.",
    "보일러 압력이 자꾸 떨어진다면 난방·급탕 배관의 누수를 확인해야 합니다.",
]

# 처리 방식 문장 풀(2개 선택)
METHODS = [
    "청음식·가스식 누수탐지 장비로 벽·바닥을 뜯지 않고 새는 지점을 찾습니다.",
    "관로 내시경으로 막힘 원인을 눈으로 확인한 뒤 고압세척으로 뿌리째 제거합니다.",
    "스프링·고압세척 등 상황에 맞는 방식으로 재발 없이 뚫어냅니다.",
    "정품 부속으로 교체하고 시공 후 마감과 재발 여부까지 점검합니다.",
    "급수·배수 배관은 구간별로 점검해 손상 부위만 최소로 교체합니다.",
]

# 비용 안내 문장 풀
COSTS = [
    "{area}의 출동 비용과 시공 가격은 증상·자재·난이도에 따라 달라집니다. 전화로 증상을 알려주시면 예상 비용을 먼저 안내하고, 방문 진단 후 확정 견적을 드립니다.",
    "{dong} 시공 비용은 현장 상황에 따라 다르므로 방문 진단 후 확정 견적으로 안내합니다. 동의 없이 추가 비용이 붙지 않습니다.",
    "가격은 언제나 시공 전에 먼저 확인해 드립니다. {area} 어디든 증상과 위치를 말씀해 주시면 예상 범위를 안내한 뒤 진행합니다.",
    "{area} 내 작업은 자재·난이도에 따라 비용이 달라집니다. 진단 결과와 확정 견적을 문서로 안내해 예상치 못한 비용을 방지합니다.",
]

# 제목 패턴 풀
DONG_TITLES = [
    "{disp} {dong} 배관공사·누수·하수구막힘 | {brand}",
    "{disp} {dong} 하수구막힘·누수탐지 24시간 출동 | {brand}",
    "{dong} 배관·누수·막힘 시공 - {disp} {brand}",
    "{disp} {dong} 변기·싱크대 막힘·누수공사 | {brand}",
    "{dong} 누수탐지·고압세척·설비교체 | {disp} {brand}",
]

# ─────────────────────────────────────────────
# 공통 head
# ─────────────────────────────────────────────
def head(title, desc, canonical, og_img="assets/img/og-main.svg", extra_ld=""):
    base = SITE["domain"]
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{base}/{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="{esc(SITE['brand'])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE['brand'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{base}/{canonical}">
<meta property="og:image" content="{base}/{og_img}">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A1A2F">
<link rel="stylesheet" href="{{CSS}}">
{extra_ld}
</head>
<body>
'''

# ─────────────────────────────────────────────
# 헤더/내비 (depth: 0 = 루트, n = 하위폴더 깊이)
# ─────────────────────────────────────────────
def header(depth=0):
    p = path_prefix(depth)
    svc_links = ""
    for s in SERVICES:
        svc_links += f'<a href="{p}services/{s["slug"]}.html"><b>{esc(s["name"])}</b><span>{esc(s["desc"])}</span></a>'
    reg_links = ""
    for slug, short, full, _ in REGIONS:
        reg_links += f'<a href="{p}regions/{slug}.html">{esc(full)}</a>'
    return f'''<div class="topbar"><div class="wrap">
  <span class="tb-note"><span class="blink"></span>{esc(SITE["emergency"])} · {esc(SITE["hours"])} · 전화 한 통이면 전국 어디든 즉시 출발</span>
  <span>긴급 문의 <a href="tel:{SITE["phone_tel"]}">{esc(SITE["phone_display"])}</a></span>
</div></div>
<header class="site-header"><div class="wrap"><nav class="nav" aria-label="주 메뉴">
  <a class="brand" href="{p}index.html" aria-label="{esc(SITE["brand"])} 홈">
    <span class="mark">{logo_svg()}</span>
    <span>{esc(SITE["brand"])}<small>전국 배관·누수·하수구 전문</small></span>
  </a>
  <ul class="menu">
    <li class="has-drop"><a href="{p}services/nusu.html">서비스</a>
      <div class="drop wide"><span class="drop-head">전문 시공 분야</span>{svc_links}</div>
    </li>
    <li class="has-drop"><a href="{p}regions/seoul.html">지역별 시공</a>
      <div class="drop regions"><span class="drop-head">전국 서비스 지역</span>{reg_links}</div>
    </li>
    <li><a href="{p}index.html#gallery">시공사례</a></li>
    <li><a href="{p}index.html#cost">비용안내</a></li>
    <li><a href="{p}index.html#about">회사소개</a></li>
    <li><a href="{p}index.html#faq">자주묻는질문</a></li>
  </ul>
  <div class="nav-right">
    <a class="nav-cta desk" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} {esc(SITE["phone_display"])}</a>
    <button class="hamb" aria-label="메뉴 열기" aria-expanded="false"><span></span></button>
  </div>
</nav></div></header>
'''

# ─────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────
def footer(depth=0):
    p = path_prefix(depth)
    svc_links = "".join(f'<li><a href="{p}services/{s["slug"]}.html">{esc(s["name"])}</a></li>' for s in SERVICES)
    reg_links = "".join(f'<li><a href="{p}regions/{slug}.html">{esc(full)}</a></li>' for slug, short, full, _ in REGIONS[:9])
    return f'''<footer class="site-footer"><div class="wrap">
  <div class="foot-grid">
    <div class="foot-brand">
      <span class="brand" style="display:inline-flex"><span class="mark">{logo_svg()}</span>
      <span>{esc(SITE["brand"])}<small>전국 배관·누수·하수구 전문</small></span></span>
      <p class="foot-biz">
        {esc(SITE["tagline"])}<br>
        상호: {esc(SITE["brand"])} · 대표: {esc(SITE["ceo"])}<br>
        사업자등록번호: {esc(SITE["biz_no"])}<br>
        주소: {esc(SITE["addr"])}<br>
        전화: <a href="tel:{SITE["phone_tel"]}">{esc(SITE["phone_display"])}</a> · {esc(SITE["email"])}
      </p>
    </div>
    <div><h4>전문 서비스</h4><ul>{svc_links}</ul></div>
    <div><h4>주요 서비스 지역</h4><ul>{reg_links}</ul></div>
    <div><h4>바로가기</h4><ul>
      <li><a href="{p}index.html#gallery">시공사례</a></li>
      <li><a href="{p}index.html#cost">비용안내</a></li>
      <li><a href="{p}index.html#about">회사소개</a></li>
      <li><a href="{p}index.html#faq">자주묻는질문</a></li>
      <li><a href="tel:{SITE["phone_tel"]}">긴급 상담 전화</a></li>
    </ul></div>
  </div>
  <div class="foot-bottom">
    <span>© <span id="year">2026</span> {esc(SITE["brand"])}. All rights reserved.</span>
    <span>본 사이트의 시공 사진·후기는 실제 현장 자료로 교체하여 사용하세요.</span>
  </div>
</div></footer>
<a class="em-fab" href="tel:{SITE["phone_tel"]}" aria-label="{esc(SITE["reserve"])} {esc(SITE["phone_display"])}">
  <span class="em-ring">{ICONS["phone"]}</span>
  <span class="em-t"><small>24시 · 지금 예약</small><b>전화예약</b></span>
  <span class="em-num">{esc(SITE["phone_display"])}</span>
</a>
<script src="{p}assets/js/main.js"></script>
</body></html>'''

def render(depth, body_parts):
    return "".join(body_parts).replace("{CSS}", path_prefix(depth) + "assets/css/style.css")

# ─────────────────────────────────────────────
# JSON-LD
# ─────────────────────────────────────────────
def ld_business():
    base = SITE["domain"]
    areas = ", ".join(f'{{"@type":"AdministrativeArea","name":"{full}"}}' for _,_,full,_ in REGIONS)
    services = ", ".join(f'"{kw}"' for s in SERVICES for kw in s["keywords"])
    return f'''<script type="application/ld+json">
{{
  "@context":"https://schema.org",
  "@type":"Plumber",
  "name":"{SITE['brand']}",
  "image":"{base}/assets/img/og-main.svg",
  "@id":"{base}/#business",
  "url":"{base}/",
  "telephone":"{SITE['phone_display']}",
  "priceRange":"₩₩",
  "address":{{"@type":"PostalAddress","streetAddress":"{SITE['addr']}","addressCountry":"KR"}},
  "openingHoursSpecification":{{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],"opens":"00:00","closes":"23:59"}},
  "areaServed":[{areas}],
  "makesOffer":[{services}],
  "founder":{{"@type":"Person","name":"{SITE['ceo']}"}},
  {agg_rating_ld()},
  "review":[{reviews_ld(REVIEWS)}]
}}
</script>'''

def ld_breadcrumb(items):
    base = SITE["domain"]
    li = ",".join(
        f'{{"@type":"ListItem","position":{i+1},"name":{json.dumps(n, ensure_ascii=False)},"item":"{base}/{u}"}}'
        for i,(n,u) in enumerate(items))
    return f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{li}]}}
</script>'''

def ld_service(name, desc, url):
    base = SITE["domain"]
    return f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Service","serviceType":"{name}","provider":{{"@type":"Plumber","name":"{SITE['brand']}","telephone":"{SITE['phone_display']}"}},"areaServed":"대한민국","description":"{desc}","url":"{base}/{url}"}}
</script>'''

# ─────────────────────────────────────────────
# 고객 후기 (고객 제공 후기 텍스트)
#  ※ 후기 본문은 실제 제공받은 내용입니다. 작성자명·날짜는 표기 예시이니
#    실제 정보로 교체하세요. 가짜 후기/별점을 구조화 데이터로 표기하면
#    검색엔진 정책 위반이 되므로, 반드시 실제 고객 후기만 사용하세요.
# ─────────────────────────────────────────────
REVIEWS = [
    # 누수탐지 중심
    {"author": "김○○ 고객님", "rating": 5, "service": "누수탐지", "date": "2026-06-18",
     "text": "아래층 천장에 물이 샌다고 해서 심장이 철렁했는데, 연락드리자마자 정말 빠르게 와주셨어요. 최첨단 장비로 세심하게 누수탐지를 해주시더니 다른 곳 안 깨고 딱 한 군데만 짚어서 바로 해결해 주시네요. 원인도 친절하게 설명해 주시고 마감까지 완벽하게 해주셔서 대만족입니다!"},
    {"author": "이○○ 고객님", "rating": 4, "service": "누수탐지", "date": "2026-06-09",
     "text": "다른 업체에서 못 찾고 헤매던 미세 누수를 여기서 단번에 찾아내 주셨습니다. 전문적인 기계로 꼼꼼하게 누수탐지하시는 모습 보고 신뢰가 확 갔어요. 이어진 배관공사도 신속하게 처리해 주셔서 정말 감사했습니다. 다만 당일 예약이 조금 밀려 방문 시간이 살짝 늦어져 별 하나 뺐어요!"},
    {"author": "박○○ 고객님", "rating": 5, "service": "누수탐지", "date": "2026-05-30",
     "text": "보일러 에러 코드가 계속 떠서 걱정했는데 정밀 누수탐지로 배관에 미세한 균열이 생긴 걸 잡아내 주셨어요. 과잉 진료(?) 없이 딱 필요한 부분만 배관공사를 진행해 주셔서 비용도 생각보다 정말 합리적으로 나왔습니다. 누수 고민하시는 분들 절대 망설이지 마세요!"},
    {"author": "최○○ 고객님", "rating": 4, "service": "누수탐지", "date": "2026-05-21",
     "text": "갑자기 수도요금이 평소보다 배로 나와서 걱정스러운 마음에 연락드렸습니다. 베테랑 사장님께서 오셔서 탐지기로 구석구석 봐주시더니 귀신같이 누수 지점을 찾아내시더라고요. 누수탐지부터 공사 마무리까지 깔끔히 해결해 주셔서 속이 시원합니다. 예약 잡기가 조금 힘들었지만 실력만큼은 확실해요."},
    {"author": "정○○ 고객님", "rating": 5, "service": "누수탐지", "date": "2026-05-12",
     "text": "아파트 아래층 화장실 천장 누수 때문에 골치 아팠는데, 사장님 덕분에 이웃 간에 얼굴 붉힐 일 없이 잘 해결했습니다. 정확한 원인 파악을 위한 누수탐지 단계부터 아주 체계적이었고, 손상된 부위의 배관공사 작업도 꼼꼼하게 마무리해 주셔서 무척 안심이 되었습니다."},
    {"author": "강○○ 고객님", "rating": 4, "service": "누수탐지", "date": "2026-05-03",
     "text": "화장실 바닥에서 물이 조금씩 배어 나와 의뢰했는데 역시 전문가는 다릅니다. 청음식, 가스식 장비 다 동원해서 정확히 누수탐지해 주셨고 원인 배관 교체 공사까지 신속하게 마쳐주셨어요. 워낙 꼼꼼하셔서 그런지 견적 단가는 조금 있는 편이지만, 하자 없이 한 번에 끝나서 아주 만족합니다."},
    {"author": "조○○ 고객님", "rating": 5, "service": "누수탐지", "date": "2026-04-24",
     "text": "밤늦게 천장에서 물이 비쳐서 급하게 연락드렸는데 친절히 응대해 주시고 다음 날 아침 일찍 방문해 주셨어요. 꼼꼼한 누수탐지 끝에 노후된 온수 파이프 문제인 것을 밝혀내고 바로 배관공사를 해주셨습니다. 신속하고 양심적인 서비스에 깊이 감동했습니다."},
    # 하수구막힘 중심
    {"author": "윤○○ 고객님", "rating": 5, "service": "하수구막힘", "date": "2026-04-15",
     "text": "싱크대 물이 안 내려가고 역류해서 온 집안에 냄새가 진동을 했는데, 사장님 덕분에 살았습니다! 하수구막힘 원인이 기름때라며 배관 내부를 내시경 카메라로 직접 보여주시며 뚫어주셨어요. 속이 다 뻥 뚫리는 기분입니다. 관리 팁까지 세심하게 알려주셔서 감동이에요."},
    {"author": "장○○ 고객님", "rating": 4, "service": "하수구막힘", "date": "2026-04-06",
     "text": "화장실 바닥 배수구가 꽉 막혀서 물바다가 되는 바람에 엄청 스트레스받았거든요. 인터넷 검색 후 연락드렸는데 장비도 정말 좋은 거 쓰시고 작업도 베테랑답게 잘 하시더라고요. 고질적인 하수구막힘 현상을 완벽하게 해결해 주셔서 감사해요. 작업 후 바닥 청소가 덜 된 부분이 살짝 아쉬웠지만 만족합니다!"},
    {"author": "임○○ 고객님", "rating": 5, "service": "하수구막힘", "date": "2026-03-28",
     "text": "가게 주방 세탁실 겸용 하수구가 막혀서 장사도 못 할 뻔했는데, 긴급 요청에 빠르게 와주셨어요. 강력한 장비로 고압 세척해 주시더니 그동안 쌓여있던 찌꺼기들이 쏟아져 나오더라고요. 완벽한 작업 덕분에 하수구막힘 골칫거리가 싹 사라졌습니다. 사업 번창하세요!"},
    {"author": "한○○ 고객님", "rating": 4, "service": "하수구막힘", "date": "2026-03-19",
     "text": "며칠 전부터 물 내려가는 속도가 시원치 않더니 결국 꽉 막혀버렸어요. 셀프로 해보려다 포기하고 불렀는데 역시 전문가의 손길은 다르네요. 꽉 막힌 원인을 단번에 파악하시고 전용 장비로 시원하게 하수구막힘을 뚫어주셨습니다. 비용은 생각보다 좀 나왔지만 제 기능 확실히 하니 돈이 안 아깝네요."},
    {"author": "오○○ 고객님", "rating": 5, "service": "하수구막힘", "date": "2026-03-10",
     "text": "아파트 메인 횡주관 문제로 빌라 1층인 저희 집 하수구가 계속 역류했어요. 너무 막막했는데 사장님께서 오셔서 꼼꼼하게 봐주셨습니다. 단순한 작업이 아니었는데도 끝까지 책임지고 하수구막힘 문제를 해결해 주셔서 감사해요. 배관 상태도 상세히 설명해 주셨습니다."},
    {"author": "서○○ 고객님", "rating": 4, "service": "하수구막힘", "date": "2026-02-28",
     "text": "싱크대 아래쪽에서 물이 새어 나와 보니 겉이 아니라 배관 속이 막혀서 역류하는 거였더라고요. 사장님이 꼼꼼하게 하수구막힘을 뚫어주신 후, 원인이었던 기름 슬러지들을 깨끗이 스케일링해 주셨습니다. 조금 퉁명스러우신 편이었지만 일 하나만큼은 정말 끝내주게 확실히 하십니다. 추천해요!"},
    {"author": "신○○ 고객님", "rating": 5, "service": "하수구막힘", "date": "2026-02-19",
     "text": "변기가 꽉 막혀서 뚫어뻥으로도 안 되길래 절망적인 마음으로 요청했습니다. 늦은 시간인데도 친절하게 방문해 주셨고, 막힘 원인이 장난감이었던 걸 쏙 빼내 주셨어요. 신속하게 변기 하수구막힘을 해결해 주셔서 정말 살았습니다. 사장님 최고예요!"},
    # 배관공사 중심
    {"author": "권○○ 고객님", "rating": 5, "service": "배관공사", "date": "2026-02-10",
     "text": "단독주택이라 겨울만 되면 배관 동파 때문에 늘 걱정이었는데, 이번에 노후된 설비를 싹 교체하는 배관공사를 진행했습니다. 꼼꼼하게 단열 처리까지 이중삼중으로 신경 써주셔서 겨울철 동파 우려를 덜었어요. 정직한 견적과 성실한 시공에 정말 만족스럽습니다."},
    {"author": "황○○ 고객님", "rating": 4, "service": "배관공사", "date": "2026-02-01",
     "text": "이사 갈 집 인테리어 하면서 욕실 구조 변경을 위해 배관공사를 의뢰했습니다. 원하던 구조가 나오기 까다로운 환경이었음에도 사장님께서 수압과 배수를 세심하게 고려해 완벽하게 라인을 잡아주셨어요. 기초 작업이 워낙 튼튼하게 잘 되어서 기쁩니다. 견적서 피드백이 살짝 늦었지만 공사는 완벽했어요!"},
    {"author": "안○○ 고객님", "rating": 5, "service": "배관공사", "date": "2026-01-23",
     "text": "상가 건물 2층인데 아래층으로 자꾸 미세한 누수가 있어서 결국 노후 라인을 전부 들어내는 대대적인 배관공사를 했습니다. 영업에 방해 안 되게 일정 조율도 잘 해주시고, 소음도 최소화해서 깔끔하게 작업 마무리해 주셨습니다. 책임감 있는 시공에 신뢰가 갑니다."},
    {"author": "송○○ 고객님", "rating": 4, "service": "배관공사", "date": "2026-01-14",
     "text": "수도계량기 쪽에서 소리도 나고 녹물도 조금씩 나오는 것 같아 정밀 진단을 받았습니다. 배관 노후화가 심하다 하여 녹슬지 않는 친환경 자재로 전체 배관공사를 완료했어요. 공사 후 수압도 좋아지고 맑은 물이 나와 안심입니다. 대공사라 소음이 엄청나서 이웃분들께 죄송했지만 결과는 대만족이에요."},
    {"author": "전○○ 고객님", "rating": 5, "service": "배관공사", "date": "2026-01-05",
     "text": "주방 싱크대 위치를 베란다 쪽으로 옮기면서 복잡한 배관공사가 필요했는데 솜씨 좋은 사장님을 만나 걱정을 덜었습니다. 배수 구배(기울기)를 기가 막히게 잡아주셔서 물 고임이나 악취 걱정 전혀 없이 시원하게 잘 내려가네요. 깔끔하고 숙련된 기술력에 감탄했습니다."},
    {"author": "홍○○ 고객님", "rating": 4, "service": "배관공사", "date": "2025-12-27",
     "text": "마당 수전 쪽 배관이 깨져서 마당 바닥이 한강이 되었어요. 당황해서 전화드렸는데 정말 빠르게 출동해 주셨습니다. 흙 파내고 꼼꼼하게 용접 및 엘보 부속 교체하는 배관공사를 뚝딱 진행해 주시더라고요. 마감 미장도 원래 마당처럼 깔끔히 해주셨습니다. 출장비가 좀 붙어서 아쉽지만 급한 불 꺼서 살았네요."},
]

def _agg():
    vals = [r["rating"] for r in REVIEWS]
    return round(sum(vals) / len(vals), 1), len(vals)

RATING_VALUE, RATING_COUNT = _agg()

def agg_rating_ld():
    return (f'"aggregateRating":{{"@type":"AggregateRating",'
            f'"ratingValue":"{RATING_VALUE}","reviewCount":"{RATING_COUNT}",'
            f'"bestRating":"5","worstRating":"1"}}')

def reviews_ld(subset):
    items = []
    for r in subset:
        items.append(
            '{"@type":"Review","author":{"@type":"Person","name":%s},'
            '"datePublished":"%s","reviewRating":{"@type":"Rating","ratingValue":"%d","bestRating":"5"},'
            '"reviewBody":%s}' % (json.dumps(r["author"], ensure_ascii=False), r["date"],
                                  r["rating"], json.dumps(r["text"], ensure_ascii=False)))
    return ",".join(items)

def stars_html(rating):
    full = int(round(rating))
    cells = "".join(f'<span class="star {"on" if i < full else "off"}">{ICONS["star"]}</span>' for i in range(5))
    return f'<span class="stars" role="img" aria-label="별점 5점 만점에 {rating}점">{cells}</span>'

def reviews_block(depth, key, heading="고객 후기", note=True, n=3):
    """지역별로 서로 다른 후기 n개를 노출(중복 방지)."""
    subset = picks(REVIEWS, n, key, "rv")
    cards = ""
    for r in subset:
        cards += (f'<article class="rv-card">'
                  f'<div class="rv-top">{stars_html(r["rating"])}<span class="rv-tag">{esc(r["service"])}</span></div>'
                  f'<p>“{esc(r["text"])}”</p>'
                  f'<div class="rv-by">{esc(r["author"])} · {esc(r["date"])}</div></article>')
    disclaimer = ('<p class="rv-note">※ 후기 본문은 고객이 제공한 내용이며, 표시된 작성자명·날짜는 예시입니다. 실제 정보로 교체해 사용하세요.</p>'
                  if note else "")
    return f'''<section class="block" id="reviews"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">고객 후기</span>
    <h2>{esc(heading)}</h2>
    <div class="rv-agg">{stars_html(RATING_VALUE)}<b>{RATING_VALUE}</b><span>/ 5.0 · 후기 {RATING_COUNT}건</span></div></div>
  <div class="rv-grid">{cards}</div>
  {disclaimer}
</div></section>'''

def ld_local(area_name, url, desc, with_reviews=True):
    """지역(시·도/구·군/동)별 LocalBusiness (+별점 집계)"""
    base = SITE["domain"]
    rating = ("," + agg_rating_ld()) if with_reviews else ""
    return f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Plumber","name":{json.dumps(SITE['brand']+" "+area_name, ensure_ascii=False)},"telephone":"{SITE['phone_display']}","areaServed":{{"@type":"AdministrativeArea","name":{json.dumps(area_name, ensure_ascii=False)}}},"url":"{base}/{url}","description":{json.dumps(desc, ensure_ascii=False)}{rating}}}
</script>'''

# 지역 FAQ (FAQPage 스키마 + 롱테일 Q&A). {area} 치환.
FAQ_POOL = [
    ("{area} 출동 비용이 따로 있나요?", "증상과 위치를 말씀해 주시면 예상 비용을 먼저 안내하고, 방문 진단 후 확정 견적을 드립니다. 동의 없이 추가 비용은 발생하지 않습니다."),
    ("{area}도 야간·주말에 출동하나요?", "네, 연중무휴 24시간 상담·출동합니다. 급하시면 언제든 전화 주시면 가까운 기술자가 즉시 출발합니다."),
    ("{area}에서 하수구가 자주 막히는데 재발 없이 되나요?", "관로 내시경으로 막힘 원인을 확인한 뒤 고압세척으로 근본 원인을 제거해 재발을 줄입니다. 구조적 문제는 개선 방법을 함께 안내합니다."),
    ("{area} 누수를 벽을 뜯지 않고 찾을 수 있나요?", "청음식·가스식 누수탐지 장비로 벽·바닥 속 지점을 비파괴 방식으로 찾아 손상을 최소화합니다."),
    ("{area}까지 얼마나 빨리 도착하나요?", "가까운 기술자가 배정되어 신속히 출발합니다. 전화 시 예상 도착 시간을 미리 안내해 드립니다."),
    ("{area}에서 변기·수전 교체도 당일 되나요?", "자재가 준비되면 대부분 당일 시공합니다. 제품 추천부터 설치·마감 점검까지 한 번에 처리합니다."),
    ("{area} 전화예약은 어떻게 하나요?", "24시간 전화 예약이 가능합니다. 증상과 희망 시간을 말씀해 주시면 방문 시간을 잡아드립니다."),
]

def ld_faq(pairs):
    body = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (json.dumps(q, ensure_ascii=False), json.dumps(a, ensure_ascii=False)) for q, a in pairs)
    return f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{body}]}}</script>'

def area_faq(depth, area, key):
    """지역별 FAQ 3개(변주) + FAQPage 스키마 반환 (html, ld)."""
    chosen = picks(FAQ_POOL, 3, key, "faq")
    pairs = [(q.format(area=area), a.format(area=area)) for q, a in chosen]
    html_fq = "".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in pairs)
    html = f'''<section class="block mist"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">자주 묻는 질문</span><h2>{esc(area)} 배관 시공 자주 묻는 질문</h2></div>
  <div class="faq">{html_fq}</div>
</div></section>'''
    return html, ld_faq(pairs)

def longtail_links(depth, disp, key, near_pairs):
    """롱테일 내부링크 블록: '지역+서비스키워드' 앵커 → 서비스 페이지, 인접지역 링크."""
    p = path_prefix(depth)
    combos = []
    for s in SERVICES:
        for kw in picks(s["keywords"], 2, key, "lt", s["slug"]):
            combos.append((f'{disp} {kw}', f'{p}services/{s["slug"]}.html'))
    # 지역별로 순서를 섞어 페이지마다 다른 앵커 노출
    order = sorted(range(len(combos)), key=lambda i: _hkey(key, "o", i))
    combos = [combos[i] for i in order][:10]
    combo_links = "".join(f'<a href="{u}">{ICONS["search"]} {esc(t)}</a>' for t, u in combos)
    near_links = "".join(f'<a href="{u}">{ICONS["pin"]} {esc(t)}</a>' for t, u in near_pairs)
    return f'''<section class="block"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">인기 시공 주제</span><h2>{esc(disp)}에서 많이 찾는 시공</h2></div>
  <div class="tag-cloud">{combo_links}{near_links}</div>
</div></section>'''

# ─────────────────────────────────────────────
# 이미지 (SVG 플레이스홀더)
# ─────────────────────────────────────────────
def make_placeholder(path, label, sub="실제 시공 사진으로 교체하세요", w=800, h=600):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#0A1A2F"/><stop offset=".55" stop-color="#12283F"/><stop offset="1" stop-color="#0B7C8A"/>
</linearGradient></defs>
<rect width="{w}" height="{h}" fill="url(#g)"/>
<g fill="none" stroke="#ffffff" stroke-opacity="0.06" stroke-width="2">
{''.join(f'<line x1="{i}" y1="0" x2="{i-160}" y2="{h}"/>' for i in range(0,w+320,80))}
</g>
<g transform="translate({w/2},{h/2-40})" fill="none" stroke="#0EA5B7" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
<path transform="translate(-26,-52) scale(2.2)" d="M12 2s6 6.5 6 11a6 6 0 1 1-12 0c0-4.5 6-11 6-11z"/>
</g>
<text x="50%" y="{h/2+70}" fill="#ffffff" font-family="Pretendard, sans-serif" font-size="34" font-weight="800" text-anchor="middle">{esc(label)}</text>
<text x="50%" y="{h/2+112}" fill="#9FB4C6" font-family="Pretendard, sans-serif" font-size="19" text-anchor="middle">{esc(sub)}</text>
<text x="50%" y="{h-34}" fill="#FF6A2B" font-family="Pretendard, sans-serif" font-size="18" font-weight="700" text-anchor="middle">{esc(SITE['brand'])}</text>
</svg>'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)

GALLERY = [
    ("누수탐지 현장", "leak-detection"), ("욕실 배관 누수공사", "bathroom-leak"),
    ("주방 배관 누수", "kitchen-leak"), ("수도 계량기 누수", "meter-leak"),
    ("변기 막힘 해결", "toilet-clog"), ("싱크대 하수구 막힘", "sink-clog"),
    ("세면대 막힘 뚫음", "basin-clog"), ("하수구 역류 처리", "drain-backflow"),
    ("배수구 고압세척", "high-pressure"), ("관로 내시경 진단", "endoscope"),
    ("싱크대 수전 교체", "kitchen-faucet"), ("화장실 수전 교체", "bath-faucet"),
    ("양변기 교체 시공", "toilet-replace"), ("세면대 교체", "basin-replace"),
    ("변기 부속 수리", "toilet-parts"), ("노후 배관 설비 교체", "pipe-replace"),
    ("상가 배관 공사", "commercial"), ("공장 배관 설비", "factory"),
    ("긴급 출동 현장", "emergency"), ("시공 완료 점검", "inspection"),
]

def build_images():
    d = os.path.join(ROOT, "assets", "img")
    os.makedirs(d, exist_ok=True)
    make_placeholder(os.path.join(d, "og-main.svg"),
                     f"{SITE['brand']}", "전국 24시간 배관·누수·하수구 출동", 1200, 630)
    for label, slug in GALLERY:
        make_placeholder(os.path.join(d, f"{slug}.svg"), label)
    print(f"  이미지 {len(GALLERY)+1}장 생성")

# ─────────────────────────────────────────────
# 공통 조각
# ─────────────────────────────────────────────
def service_cards(depth):
    """서비스 4개 카드 (지역 페이지 공용)"""
    p = path_prefix(depth)
    cards = ""
    for s in SERVICES:
        tags = "".join(f'<a href="{p}services/{s["slug"]}.html">{esc(k)}</a>' for k in s["keywords"][:5])
        cards += (f'<article class="svc-card"><div class="svc-ico">{ICONS[s["icon"]]}</div>'
                  f'<h3>{esc(s["name"])}</h3><p>{esc(s["desc"])}</p>'
                  f'<div class="svc-tags">{tags}</div></article>')
    return cards

def side_card(depth, area_full):
    p = path_prefix(depth)
    return f'''<aside class="side-card">
    <h3>{esc(area_full)} 24시간 상담</h3>
    <div class="num">{esc(SITE["phone_display"])}</div>
    <a class="btn btn-primary" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} 전화 상담</a>
    <ul>
      <li>{ICONS["check"]} {esc(area_full)} 전 지역 출동</li>
      <li>{ICONS["check"]} 연중무휴 24시간</li>
      <li>{ICONS["check"]} 출동 전 비용 사전고지</li>
      <li>{ICONS["check"]} 정품 자재·경력 기술자 시공</li>
    </ul>'''

# ─────────────────────────────────────────────
# 메인 페이지
# ─────────────────────────────────────────────
def build_index():
    title = f"{SITE['brand']} | 전국 배관공사·누수탐지·하수구막힘 24시간 출동"
    desc = "전국 배관공사 전문 스피드 배관공사. 누수탐지·누수공사, 하수구·배관 막힘, 변기·수전 교체, 고압세척까지 24시간 신속 출동. 출동 전 비용 안내, 정품 자재 시공."
    parts = [head(title, desc, "index.html", extra_ld=ld_business())]
    parts.append(header(0))

    # 히어로
    hero_points = "".join(f'<li>{ICONS["check"]} {esc(t)}</li>' for t in
        ["누수탐지부터 공사까지 원스톱", "하수구·변기·싱크대 막힘 즉시 해결", "출동 전 예상 비용 투명 안내", "정품 자재·시공 후 마감 점검"])
    parts.append(f'''<section class="hero"><div class="wrap">
  <div>
    <span class="eyebrow" style="color:#7FE3EC">전국 24시 긴급출동 · 전화 즉시 출발</span>
    <h1>물 새고 막혔을 땐,<br><span class="hl">스피드 배관공사</span></h1>
    <p class="lead"><b>24시 긴급출동</b> — 누수탐지·하수구막힘·배관설비·수전/변기 교체까지. 전화 한 통이면 전국 어디든 즉시 출발해 원인을 정확히 찾고 재발 없이 시공합니다.</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} 지금 전화 상담</a>
      <a class="btn btn-ghost" href="#services">서비스 둘러보기</a>
    </div>
    <div class="hero-badges">
      <div><b>24시간</b><span>연중무휴 출동</span></div>
      <div><b>전국</b><span>17개 시·도 대응</span></div>
      <div><b>사전고지</b><span>투명한 비용 안내</span></div>
    </div>
  </div>
  <aside class="hero-card">
    <h3>스피드 배관공사를 선택하는 이유</h3>
    <ul>{hero_points}</ul>
    <div class="callbox">
      <div><small>24시간 긴급 상담</small><div class="num">{esc(SITE["phone_display"])}</div></div>
      <a href="tel:{SITE["phone_tel"]}">전화하기</a>
    </div>
  </aside>
</div></section>''')

    # 신뢰 스트립
    strip = "".join(f'<span>{ICONS[i]} {t}</span>' for i,t in
        [("clock","연중무휴 24시간 출동"),("won","출동 전 비용 사전고지"),
         ("shield","정품 자재 사용"),("badge","경력 기술자 직접 시공"),("pin","전국 서비스망")])
    parts.append(f'<div class="trust-strip"><div class="wrap">{strip}</div></div>')

    # 서비스
    cards = ""
    for s in SERVICES:
        tags = "".join(f'<a href="services/{s["slug"]}.html">{esc(k)}</a>' for k in s["keywords"][:6])
        cards += f'''<article class="svc-card">
  <div class="svc-ico">{ICONS[s["icon"]]}</div>
  <h3>{esc(s["name"])}</h3>
  <p>{esc(s["desc"])}</p>
  <div class="svc-tags">{tags}</div>
</article>'''
    parts.append(f'''<section class="block" id="services"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">전문 시공 분야</span>
    <h2>배관의 모든 문제, 한 곳에서 해결</h2>
    <p>누수부터 막힘, 교체, 설비까지. 상황에 맞는 전문 시공을 제공합니다.</p></div>
  <div class="svc-cats">{cards}</div>
</div></section>''')

    # 프로세스
    steps = [("STEP 01","전화 접수","증상을 말씀해 주시면 현장 상황을 파악하고 예상 비용을 안내합니다."),
             ("STEP 02","신속 출동","가까운 기술자가 약속된 시간에 현장으로 출동합니다."),
             ("STEP 03","진단·견적","장비로 원인을 정확히 진단하고 확정 견적을 안내합니다."),
             ("STEP 04","시공·점검","동의 후 시공하고 마감·재발 여부까지 확인합니다.")]
    st = "".join(f'<div class="step"><div class="n">{n}</div><h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for n,t,d in steps)
    parts.append(f'''<section class="block mist"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">진행 절차</span>
    <h2>접수부터 시공까지 4단계</h2>
    <p>전화 한 통이면 됩니다. 비용은 언제나 시공 전에 먼저 안내합니다.</p></div>
  <div class="steps">{st}</div>
</div></section>''')

    # 지역
    rg = "".join(f'<a href="regions/{slug}.html">{esc(full)} {ICONS["arrow"]}</a>' for slug,short,full,_ in REGIONS)
    parts.append(f'''<section class="block" id="regions"><div class="wrap region-wrap">
  <div>
    <span class="eyebrow">전국 서비스 지역</span>
    <h2 style="font-size:34px;color:var(--ink);margin:12px 0 12px">우리 동네도 스피드 배관공사</h2>
    <p style="color:var(--muted);font-size:16px">서울·경기·부산을 비롯한 전국 17개 광역시·도, 시·군·구, 읍·면·동까지 배관·누수·하수구 시공을 제공합니다. 지역을 선택하면 우리 동네 서비스 안내를 확인할 수 있습니다.</p>
    <a class="btn btn-primary" style="margin-top:18px" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} 우리 지역 상담하기</a>
  </div>
  <div class="region-grid">{rg}</div>
</div></section>''')

    # 지역 × 서비스 롱테일 딥링크 허브 (주요 도시의 실제 구·동으로 바로 연결)
    hub_cols = ""
    picked_cities = []
    for sh in HIER:
        slug = sh["sido"]["slug"]
        for c in sh["cities"][:2]:
            if c["gus"]:
                gu = c["gus"][0]
                unit_disp = f'{c["name"]} {gu["name"]}'
                base_url = gu_url(slug, c["name"], gu["name"])
                dongs = dist_groups(gu["dist"])
            else:
                unit_disp = c["name"]
                base_url = city_url(slug, c["name"])
                dongs = dist_groups(c["unit"])
            picked_cities.append((sh["sido"]["full"], slug, c["name"], unit_disp, base_url, dongs))
    # 상위 10개 도시만 노출
    for full, slug, city, unit_disp, base_url, dongs in picked_cities[:10]:
        links = "".join(
            f'<a href="{base_url}{q(g["repr"])}.html">{esc(g["repr"])} 하수구막힘·누수</a>'
            for g in dongs[:6])
        hub_cols += (f'<div class="hub-col"><h3><a href="{base_url}">{esc(unit_disp)}</a></h3>'
                     f'<div class="hub-links">{links}</div></div>')
    parts.append(f'''<section class="block mist"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">지역별 인기 시공</span>
    <h2>우리 동네 배관·누수·하수구막힘 바로가기</h2>
    <p>자주 찾는 지역의 동별 안내로 바로 이동하세요. 전국 시·군·구·읍·면·동 전체는 지역 페이지에서 확인할 수 있습니다.</p></div>
  <div class="hub-grid">{hub_cols}</div>
</div></section>''')

    # 고객 후기 (별점) — 메인은 9개 노출
    parts.append(reviews_block(0, "home", heading="고객이 남긴 별점 후기", n=9))

    # 갤러리
    figs = "".join(f'<figure><img src="assets/img/{slug}.svg" alt="{esc(label)} 시공 사례" loading="lazy" width="800" height="600"><figcaption>{esc(label)}</figcaption></figure>' for label,slug in GALLERY)
    parts.append(f'''<section class="block mist" id="gallery"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">시공 사례</span>
    <h2>직접 시공한 현장을 확인하세요</h2>
    <p>실제 현장 사진과 후기는 신뢰의 핵심입니다. 아래 이미지는 실제 시공 사진으로 교체해 사용하세요.</p></div>
  <div class="gallery">{figs}</div>
</div></section>''')

    # 비용
    rows = [("누수탐지","벽·바닥 비파괴 탐지","현장 견적"),
            ("하수구·변기 막힘 뚫음","스프링/고압세척","현장 견적"),
            ("싱크대·세면대 수전 교체","자재 별도","현장 견적"),
            ("양변기 교체","철거·설치 포함","현장 견적"),
            ("고압세척·관로 내시경","관 길이·상태별","현장 견적")]
    tr = "".join(f'<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>' for a,b,c in rows)
    parts.append(f'''<section class="block" id="cost"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">비용 안내</span>
    <h2>비용은 언제나 시공 전에 안내합니다</h2>
    <p>현장 상황·자재·난이도에 따라 비용이 달라집니다. 아래 표는 예시이며, 실제 금액은 진단 후 확정 견적으로 안내드립니다.</p></div>
  <table class="cost-table">
    <thead><tr><th>서비스</th><th>내용</th><th>비용</th></tr></thead>
    <tbody>{tr}</tbody>
  </table>
  <p class="cost-note">※ 위 금액은 예시입니다. 방문·진단 후 확정 견적을 드리며, 동의 없이 추가 비용이 발생하지 않습니다. 정확한 가격은 <a href="tel:{SITE["phone_tel"]}">{esc(SITE["phone_display"])}</a>로 문의해 주세요.</p>
</div></section>''')

    # 회사소개 (E-E-A-T)
    tc = [("badge","현장 경력 기술자",f"{SITE['founded']}년부터 축적한 시공 경험으로 대표가 직접 현장을 책임집니다. 하도급이 아닌 자사 기술자가 시공합니다."),
          ("shield","정품 자재·사후 관리","검증된 정품 부속만 사용하며, 시공 후 마감 점검과 재발 시 A/S 안내까지 책임집니다."),
          ("doc","투명한 견적·정식 사업자",f"사업자등록({SITE['biz_no']}) 정식 업체로, 시공 전 확정 견적을 문서로 안내해 불필요한 추가 비용을 방지합니다.")]
    tcs = "".join(f'<div class="trust-c">{ICONS[i]}<h3>{esc(t)}</h3><p>{esc(d)}</p></div>' for i,t,d in tc)
    parts.append(f'''<section class="block mist" id="about"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">회사 소개</span>
    <h2>믿고 맡기는 스피드 배관공사</h2>
    <p>대표: {esc(SITE["ceo"])} · 상호: {esc(SITE["brand"])} · 정식 사업자 등록 업체</p></div>
  <div class="trust-cards">{tcs}</div>
</div></section>''')

    # FAQ
    faqs = [("출동 비용이 따로 있나요?","증상과 지역을 말씀해 주시면 전화로 예상 비용을 안내드립니다. 방문 진단 후 확정 견적을 드리며, 동의 없이 추가 비용이 발생하지 않습니다."),
            ("누수 위치를 벽을 뜯지 않고 찾을 수 있나요?","네. 청음식·가스식 누수탐지 장비로 벽이나 바닥 속 누수 지점을 비파괴 방식으로 찾아 손상을 최소화합니다."),
            ("변기·하수구가 자주 막히는데 재발 없이 처리되나요?","관로 내시경으로 막힘 원인을 확인한 뒤 고압세척 등으로 근본 원인을 제거해 재발을 줄입니다. 구조적 문제는 개선 방법을 함께 안내합니다."),
            ("전국 어디든 출동이 가능한가요?","서울·경기·부산 등 전국 17개 광역시·도 전역과 시·군·구, 읍·면·동 단위까지 서비스를 제공합니다. 지역별 안내 페이지에서 우리 동네를 확인하실 수 있습니다."),
            ("야간이나 주말에도 되나요?","연중무휴 24시간 상담·출동을 운영합니다. 긴급 상황은 언제든 전화 주세요.")]
    fq = "".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q,a in faqs)
    faq_ld = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + \
             ",".join('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}' % (json.dumps(q,ensure_ascii=False),json.dumps(a,ensure_ascii=False)) for q,a in faqs) + ']}</script>'
    parts.append(f'''<section class="block" id="faq"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">자주 묻는 질문</span>
    <h2>궁금한 점을 확인하세요</h2></div>
  <div class="faq">{fq}</div>
</div></section>{faq_ld}''')

    # 최종 CTA
    parts.append(f'''<section class="final-cta"><div class="wrap">
  <span class="eyebrow" style="color:#FFB59A;justify-content:center">지금 바로 상담</span>
  <h2>물이 새거나 막혔다면, 미루지 마세요</h2>
  <p>방치할수록 피해가 커집니다. 전화 한 통이면 전국 어디든 신속하게 출동합니다.</p>
  <a class="big-num" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} {esc(SITE["phone_display"])}</a>
</div></section>''')

    parts.append(footer(0))
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render(0, parts))
    print("  index.html")

# ─────────────────────────────────────────────
# 서비스 상세 페이지
# ─────────────────────────────────────────────
def build_services():
    for s in SERVICES:
        url = f"services/{s['slug']}.html"
        title = f"{s['name']} | {SITE['brand']} 전국 24시간 출동"
        desc = f"{s['desc']} {SITE['brand']}는 전국에서 {'·'.join(s['keywords'][:4])} 등을 전문 시공합니다. 출동 전 비용 안내."
        ld = ld_breadcrumb([("홈","index.html"),("서비스",url),(s["name"],url)]) + \
             ld_service(s["name"], s["desc"], url)
        parts = [head(title, desc, url, extra_ld=ld)]
        parts.append(header(1))
        chips = "".join(f'<span>{esc(k)}</span>' for k in s["keywords"])
        parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb"><a href="../index.html">홈</a> › 서비스 › {esc(s["name"])}</div>
  <h1>{esc(s["name"])}</h1>
  <p>{esc(s["lead"])}</p>
  <div class="chips">{chips}</div>
</div></section>''')

        pts = "".join(f'<li>{esc(x)}</li>' for x in s["points"])
        other = "".join(f'<a class="svc-tags" style="display:inline-block;margin:3px" href="{o["slug"]}.html">{esc(o["short"])}</a>' for o in SERVICES if o["slug"]!=s["slug"])
        side_reg = "".join(f'<li>{ICONS["pin"]}<a href="../regions/{slug}.html">{esc(full)}</a></li>' for slug,short,full,_ in REGIONS[:6])
        parts.append(f'''<section class="block"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(s["name"])}, 이렇게 진행합니다</h2>
    <p>{esc(s["lead"])}</p>
    <h3>주요 시공 내용</h3>
    <ul>{pts}</ul>
    <h3>이런 증상이라면 연락하세요</h3>
    <p>{esc('· '.join(s["keywords"]))} 관련 증상이 있다면 방치하지 말고 상담하세요. 증상과 지역을 알려주시면 예상 비용과 출동 가능 시간을 바로 안내드립니다. 비용·가격은 시공 전에 확정 견적으로 먼저 확인해 드립니다.</p>
    <h3>다른 서비스</h3>
    <div>{other}</div>
  </div>
  <aside class="side-card">
    <h3>{esc(s["short"])} 상담 문의</h3>
    <div class="num">{esc(SITE["phone_display"])}</div>
    <a class="btn btn-primary" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} 전화 상담</a>
    <ul>
      <li>{ICONS["check"]} 연중무휴 24시간 출동</li>
      <li>{ICONS["check"]} 출동 전 비용 사전고지</li>
      <li>{ICONS["check"]} 정품 자재·경력 기술자 시공</li>
    </ul>
    <h3 style="margin-top:20px;font-size:15px">주요 지역</h3>
    <ul>{side_reg}</ul>
  </aside>
</div></section>''')
        parts.append(footer(1))
        with open(os.path.join(ROOT, url), "w", encoding="utf-8") as f:
            f.write(render(1, parts))
    print(f"  services/ {len(SERVICES)}개")

# ─────────────────────────────────────────────
# 브레드크럼 (내부링크는 항상 루트기준 경로에 depth prefix 적용)
# ─────────────────────────────────────────────
def crumb(depth, items):
    p = path_prefix(depth)
    out = []
    for label, u in items:
        if u:
            out.append(f'<a href="{p}{u}">{esc(label)}</a>')
        else:
            out.append(esc(label))
    return " › ".join(out)

# ─────────────────────────────────────────────
# 광역시·도 페이지 (관할 행정시·시·군·구 목록)
# ─────────────────────────────────────────────
def build_regions():
    for sh in HIER:
        sido = sh["sido"]
        slug, short, full = sido["slug"], sido["short"], sido["full"]
        cities = sh["cities"]
        url = region_url(slug)
        city_names = "·".join(c["name"] for c in cities)
        n_city = len(cities)
        n_dong = sum(len(dist_groups(d)) for _, _, d in iter_units(sh))
        title = f"{full} 배관공사·누수탐지·하수구막힘 | {SITE['brand']}"
        desc = (f"{full} 전 지역 배관·누수·하수구 전문. {full} {n_city}개 시·군·구, {n_dong}개 읍·면·동 "
                f"어디든 24시간 출동. 누수탐지·막힘 뚫음·수전/변기 교체·고압세척.")
        rkey = ("region", slug)
        faq_html, faq_ld = area_faq(1, full, rkey)
        ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),(full,url)])
        ld += ld_local(full, url, f"{full} 배관·누수·하수구 전문 시공")
        ld += faq_ld
        parts = [head(title, desc, url, extra_ld=ld)]
        parts.append(header(1))
        parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb">{crumb(1, [("홈","index.html"),("지역별 시공",None),(full,None)])}</div>
  <h1>{esc(full)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{esc(full)} 전역에서 누수탐지·누수공사, 하수구·변기·싱크대 막힘, 수전·변기 교체, 고압세척까지 24시간 신속 출동합니다. 아래에서 우리 시·군·구를 선택하면 행정구·읍·면·동 단위 안내까지 확인할 수 있습니다.</p>
</div></section>''')

        # 시·군·구(구를 가진 시는 그 시) 목록
        links = ""
        for c in cities:
            if c["gus"]:
                sub = f'{len(c["gus"])}개 구'
            else:
                sub = f'{len(dist_groups(c["unit"]))}개 동'
            links += (f'<a href="{path_prefix(1)}{city_url(slug, c["name"])}">'
                      f'{esc(c["name"])} <small>({sub})</small> {ICONS["arrow"]}</a>')
        parts.append(f'''<section class="block"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">{esc(full)} 시·군·구</span>
    <h2>{esc(full)} 시·군·구별 배관 시공 안내</h2>
    <p>{esc(full)}는 {esc(city_names)} 등 {n_city}개 시·군·구로 이루어져 있습니다. 지역을 선택하면 행정구·행정동까지 안내합니다.</p></div>
  <div class="region-grid">{links}</div>
</div></section>''')

        # 서비스 카드 + 상담
        parts.append(f'''<section class="block mist"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(full)}에서 이용 가능한 서비스</h2>
    <p>천장 얼룩이나 원인 모를 수도요금 증가는 누수 신호일 수 있고, 물이 잘 안 내려가거나 역류한다면 배관 막힘일 수 있습니다. {esc(short)} 지역에서 이런 증상이 있다면 방치하지 말고 상담하세요.</p>
    <div class="svc-cats" style="grid-template-columns:1fr 1fr;margin-top:14px">{service_cards(1)}</div>
    <h3>비용·가격 안내</h3>
    <p>{esc(full)} 내 출동 비용과 시공 가격은 증상·자재·난이도에 따라 달라집니다. 전화로 증상을 알려주시면 예상 비용을 먼저 안내하고, 방문 진단 후 확정 견적을 드립니다. 동의 없이 추가 비용은 발생하지 않습니다.</p>
  </div>
  {side_card(1, full)}
  </aside>
</div></section>''')
        ridx = next(i for i, (s, _, _, _) in enumerate(REGIONS) if s == slug)
        near_pairs = [(REGIONS[(ridx + k) % len(REGIONS)][2],
                       f'{path_prefix(1)}{region_url(REGIONS[(ridx + k) % len(REGIONS)][0])}')
                      for k in (1, 2, 3)]
        parts.append(longtail_links(1, full, rkey, near_pairs))
        parts.append(reviews_block(1, rkey))
        parts.append(faq_html)
        parts.append(footer(1))
        d = os.path.join(ROOT, "regions")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(render(1, parts))
    print(f"  regions/ {len(HIER)}개 (광역시·도)")

# ─────────────────────────────────────────────
# 행정시 허브 페이지 (구를 가진 시) — 관할 행정구 목록
# 예: 경기도 수원시 → 장안구·권선구·팔달구·영통구
# ─────────────────────────────────────────────
def build_cityhubs():
    n = 0
    for sh in HIER:
        sido = sh["sido"]
        slug, full = sido["slug"], sido["full"]
        for c in sh["cities"]:
            if not c["gus"]:
                continue
            city = c["name"]
            area = f"{full} {city}"
            url = city_url(slug, city)
            gu_names = "·".join(g["name"] for g in c["gus"])
            n_dong = sum(len(dist_groups(g["dist"])) for g in c["gus"])
            title = f"{city} 배관공사·누수·하수구막힘 | {full} {SITE['brand']}"
            desc = (f"{full} {city} 배관·누수·하수구 전문. {gu_names} 등 {len(c['gus'])}개 구, "
                    f"{n_dong}개 동 어디든 24시간 출동. 누수탐지·하수구막힘·변기/수전 교체·고압세척.")
            ckey = ("city", slug, city)
            faq_html, faq_ld = area_faq(3, area, ckey)
            ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),
                                (full,region_url(slug)),(city,url)])
            ld += ld_local(area, url, f"{area} 배관·누수·하수구 전문 시공")
            ld += faq_ld
            parts = [head(title, desc, url, extra_ld=ld)]
            parts.append(header(3))
            parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb">{crumb(3, [("홈","index.html"),(full,region_url(slug)),(city,None)])}</div>
  <h1>{esc(area)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{esc(area)} 전역에서 누수탐지·누수공사, 하수구·변기·싱크대 막힘, 수전·변기 교체, 고압세척까지 24시간 신속 출동합니다. {esc(city)}는 {esc(gu_names)}로 이루어져 있습니다. 우리 구를 선택하면 행정동 안내까지 확인할 수 있습니다.</p>
</div></section>''')

            gu_links = "".join(
                f'<a href="{path_prefix(3)}{gu_url(slug, city, g["name"])}">{esc(g["name"])} '
                f'<small>({len(dist_groups(g["dist"]))}개 동)</small> {ICONS["arrow"]}</a>'
                for g in c["gus"])
            parts.append(f'''<section class="block"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">{esc(city)} 행정구</span>
    <h2>{esc(city)} 구별 배관 시공 안내</h2>
    <p>{esc(city)}는 {esc(gu_names)} 등 {len(c['gus'])}개 구로 이루어져 있습니다. 우리 구를 선택하세요.</p></div>
  <div class="region-grid">{gu_links}</div>
</div></section>''')

            parts.append(f'''<section class="block mist"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(city)}에서 이용 가능한 서비스</h2>
    <p>{esc(area)}의 오래된 주택부터 신축 아파트, 상가·사무실까지 현장 특성에 맞춰 시공합니다. 누수·막힘·교체·설비 어떤 상황이든 원인을 정확히 진단하고 재발 없이 처리합니다.</p>
    <div class="svc-cats" style="grid-template-columns:1fr 1fr;margin-top:14px">{service_cards(3)}</div>
    <h3>{esc(city)} 비용·가격 안내</h3>
    <p>{esc(area)} 내 출동 비용과 시공 가격은 증상·자재·난이도에 따라 달라집니다. 전화로 증상을 알려주시면 예상 비용을 먼저 안내하고, 방문 진단 후 확정 견적을 드립니다. 동의 없이 추가 비용은 발생하지 않습니다.</p>
  </div>
  {side_card(3, area)}
    <h3 style="margin-top:20px;font-size:15px">{esc(full)} 다른 지역</h3>
    <ul><li>{ICONS["pin"]}<a href="{path_prefix(3)}{region_url(slug)}">{esc(full)} 전체 보기</a></li></ul>
  </aside>
</div></section>''')
            near_pairs = [(g["name"], f'{path_prefix(3)}{gu_url(slug, city, g["name"])}') for g in c["gus"][:4]]
            parts.append(longtail_links(3, city, ckey, near_pairs))
            parts.append(reviews_block(3, ckey))
            parts.append(faq_html)
            parts.append(footer(3))
            outdir = os.path.join(ROOT, "regions", slug, city)
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
                f.write(render(3, parts))
            n += 1
    print(f"  regions/*/  {n}개 (행정시 허브)")

# ─────────────────────────────────────────────
# 단위 페이지(행정구 또는 구 없는 시/군/구) — 관할 읍·면·동 목록
# ─────────────────────────────────────────────
def build_units():
    n = 0
    for sh in HIER:
        sido = sh["sido"]
        slug, full = sido["slug"], sido["full"]
        for city, gu, dist in iter_units(sh):
            depth = 4 if gu else 3
            disp = f"{city} {gu}" if gu else city
            area = f"{full} {disp}"
            url = unit_url(slug, city, gu)
            groups = dist_groups(dist)                 # 숫자형 동은 대표 1개
            dong_names = "·".join(g["repr"] for g in groups)
            title = f"{disp} 배관공사·누수·하수구막힘 | {full} {SITE['brand']}"
            desc = (f"{full} {disp} 배관·누수·하수구 전문. {dong_names} 등 {len(groups)}개 동 어디든 "
                    f"24시간 출동. 누수탐지·하수구막힘·변기/수전 교체·고압세척.")
            bc = [("홈","index.html"),(full,region_url(slug))]
            if gu:
                bc.append((city, city_url(slug, city)))
            bc.append((disp if not gu else gu, None))
            ukey = (slug, city, gu or "", "unit")
            faq_html, faq_ld = area_faq(depth, area, ukey)
            ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),
                                (full,region_url(slug))]
                               + ([(city,city_url(slug,city))] if gu else [])
                               + [(disp, url)])
            ld += ld_local(area, url, f"{area} 배관·누수·하수구 전문 시공")
            ld += faq_ld
            parts = [head(title, desc, url, extra_ld=ld)]
            parts.append(header(depth))
            u_intro = pick(DONG_INTRO, *ukey).format(area=esc(area), dong=esc(disp))
            parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb">{crumb(depth, bc)}</div>
  <h1>{esc(area)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{u_intro} {esc(disp)} 내 우리 동네를 선택하면 동별 안내를 확인할 수 있습니다.</p>
</div></section>''')

            dong_links = "".join(
                f'<a href="{path_prefix(depth)}{dong_url(slug, city, gu, g["repr"])}">{esc(g["repr"])} {ICONS["arrow"]}</a>'
                for g in groups)
            parts.append(f'''<section class="block"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">{esc(disp)} 읍·면·동</span>
    <h2>{esc(disp)} 동별 배관 시공 안내</h2>
    <p>{esc(disp)}는 {esc(dong_names)} 등 {len(groups)}개 행정동으로 이루어져 있습니다. 우리 동네를 선택하세요. (○○1동·2동처럼 번호로 나뉜 동은 대표 이름 하나로 안내합니다.)</p></div>
  <div class="region-grid">{dong_links}</div>
</div></section>''')

            up = ""
            if gu:
                up = (f'<li>{ICONS["pin"]}<a href="{path_prefix(depth)}{city_url(slug, city)}">{esc(city)} 전체</a></li>'
                      f'<li>{ICONS["pin"]}<a href="{path_prefix(depth)}{region_url(slug)}">{esc(full)} 전체</a></li>')
            else:
                up = f'<li>{ICONS["pin"]}<a href="{path_prefix(depth)}{region_url(slug)}">{esc(full)} 전체 보기</a></li>'
            u_meth = " ".join(picks(METHODS, 2, *ukey, "m"))
            u_cost = pick(COSTS, *ukey, "c").format(area=esc(area), dong=esc(disp))
            parts.append(f'''<section class="block mist"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(disp)}에서 이용 가능한 서비스</h2>
    <p>{esc(area)}의 오래된 주택부터 신축 아파트, 상가·사무실까지 현장 특성에 맞춰 시공합니다. {u_meth}</p>
    <div class="svc-cats" style="grid-template-columns:1fr 1fr;margin-top:14px">{service_cards(depth)}</div>
    <h3>{esc(disp)} 비용·가격 안내</h3>
    <p>{u_cost} 동의 없이 추가 비용은 발생하지 않습니다.</p>
  </div>
  {side_card(depth, area)}
    <h3 style="margin-top:20px;font-size:15px">상위 지역</h3>
    <ul>{up}</ul>
  </aside>
</div></section>''')
            near_pairs = [(g["repr"], f'{path_prefix(depth)}{dong_url(slug, city, gu, g["repr"])}') for g in groups[:4]]
            parts.append(longtail_links(depth, disp, ukey, near_pairs))
            parts.append(reviews_block(depth, ukey))
            parts.append(faq_html)
            parts.append(footer(depth))
            outdir = os.path.join(ROOT, "regions", slug, city, gu) if gu else os.path.join(ROOT, "regions", slug, city)
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
                f.write(render(depth, parts))
            n += 1
    print(f"  regions/*/  {n}개 (행정구·시·군·구 = 동 목록)")

# ─────────────────────────────────────────────
# 읍·면·동 페이지 (행정동)
# ─────────────────────────────────────────────
def build_dongs():
    n = 0
    for sh in HIER:
        sido = sh["sido"]
        slug, full = sido["slug"], sido["full"]
        for city, gu, dist in iter_units(sh):
            depth = 4 if gu else 3
            disp = f"{city} {gu}" if gu else city
            unit_listing = unit_url(slug, city, gu)
            groups = dist_groups(dist)                 # 숫자형 동 → 대표 1개
            gcount = len(groups)
            for i, g in enumerate(groups):
                dong = g["repr"]
                members = [m["name"] for m in g["members"]]
                covers = (dong not in members) or len(members) > 1
                member_str = "·".join(members)
                url = dong_url(slug, city, gu, dong)
                area = f"{full} {disp} {dong}"
                key = (slug, city, gu or "", dong)          # 지역별 변주 키
                kind = area_kind(dong)
                cover_note = (f" ({member_str} 포함)" if covers else "")
                title = pick(DONG_TITLES, *key).format(disp=disp, dong=dong, brand=SITE["brand"])
                sym0 = pick(SYMPTOMS, *key, "d")
                desc = (f"{full} {disp} {dong}{cover_note} 배관·누수·하수구 전문. {sym0} "
                        f"누수탐지·하수구막힘·변기/수전 교체·고압세척까지 24시간 출동, 출동 전 비용 안내.")
                bc = [("홈","index.html"),(full,region_url(slug))]
                if gu:
                    bc.append((city, city_url(slug, city)))
                bc.append((gu if gu else city, unit_listing))
                bc.append((dong, None))
                dong_area = f"{disp} {dong}"
                faq_html, faq_ld = area_faq(depth, dong_area, key)
                ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),
                                    (full,region_url(slug))]
                                   + ([(city,city_url(slug,city))] if gu else [])
                                   + [(disp, unit_listing),(dong,url)])
                ld += ld_local(area, url, f"{area} 배관·누수·하수구 전문 시공")
                ld += faq_ld
                parts = [head(title, desc, url, extra_ld=ld)]
                parts.append(header(depth))
                intro = pick(DONG_INTRO, *key).format(area=esc(area), dong=esc(dong))
                parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb">{crumb(depth, bc)}</div>
  <h1>{esc(disp)} {esc(dong)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{intro} 출동 전 예상 비용을 먼저 안내합니다.</p>
</div></section>''')

                cover_block = ""
                if covers:
                    cover_block = (f'<p><b>{esc(dong)}</b>은(는) {esc(member_str)}을(를) 포함하는 지역입니다. '
                                   f'{esc(member_str)} 어디서든 동일하게 출동·시공합니다.</p>')

                # 이웃 행정동(내부 링크): 같은 단위의 앞뒤 대표 동
                near = []
                for k in range(1, 9):
                    if len(near) >= 8: break
                    j = (i + k) % gcount
                    if j == i: continue
                    near.append(groups[j]["repr"])
                near = near[:8]
                near_links = "".join(
                    f'<a href="{path_prefix(depth)}{dong_url(slug, city, gu, nb)}">{esc(nb)} {ICONS["arrow"]}</a>'
                    for nb in near)

                up = ""
                up += f'<li>{ICONS["pin"]}<a href="{path_prefix(depth)}{unit_listing}">{esc(disp)} 전체</a></li>'
                if gu:
                    up += f'<li>{ICONS["pin"]}<a href="{path_prefix(depth)}{city_url(slug, city)}">{esc(city)} 전체</a></li>'
                up += f'<li>{ICONS["pin"]}<a href="{path_prefix(depth)}{region_url(slug)}">{esc(full)} 전체</a></li>'

                # 지역별 변주 문단
                open_p = pick(DONG_OPEN, *key).format(area=esc(area), disp=esc(disp), dong=esc(dong), kind=esc(kind))
                syms = " ".join(picks(SYMPTOMS, 2, *key, "s"))
                meths = " ".join(picks(METHODS, 2, *key, "m"))
                cost_p = pick(COSTS, *key, "c").format(area=esc(area), dong=esc(dong))

                # 지역 고유 사실 정보(페이지마다 실제로 다른 데이터)
                chain = " › ".join([full] + ([city] if gu else []) + [disp if not gu else gu])
                fact_rows = [("상위 행정구역", esc(chain))]
                if covers:
                    fact_rows.append(("포함 세부 행정동", esc(member_str)))
                fact_rows.append((f"{esc(disp)} 행정동 수", f"{gcount}개"))
                if near:
                    fact_rows.append(("인접 행정동", esc('·'.join(near))))
                fact_tbl = "".join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in fact_rows)

                parts.append(f'''<section class="block"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(dong)} 배관 문제, 스피드 배관공사가 해결합니다</h2>
    <p>{open_p} {syms}</p>
    {cover_block}
    <p>{esc(dong)}에서 이런 증상이 있다면 방치하지 말고 상담하세요. {meths}</p>
    <h3>{esc(dong)} 행정 정보</h3>
    <table class="cost-table"><tbody>{fact_tbl}</tbody></table>
    <h3>{esc(dong)}에서 이용 가능한 서비스</h3>
    <div class="svc-cats" style="grid-template-columns:1fr 1fr;margin-top:14px">{service_cards(depth)}</div>
    <h3>{esc(dong)} 비용·가격 안내</h3>
    <p>{cost_p} 동의 없이 추가 비용은 발생하지 않습니다.</p>
    <h3>{esc(disp)} 인근 동네</h3>
    <div class="region-grid">{near_links}</div>
  </div>
  {side_card(depth, area)}
    <h3 style="margin-top:20px;font-size:15px">상위 지역</h3>
    <ul>{up}</ul>
  </aside>
</div></section>''')
                near_pairs = [(nb, f'{path_prefix(depth)}{dong_url(slug, city, gu, nb)}') for nb in near[:4]]
                parts.append(longtail_links(depth, dong_area, key, near_pairs))
                parts.append(reviews_block(depth, key))
                parts.append(faq_html)
                parts.append(footer(depth))
                outdir = os.path.join(ROOT, "regions", slug, city, gu) if gu else os.path.join(ROOT, "regions", slug, city)
                os.makedirs(outdir, exist_ok=True)
                with open(os.path.join(outdir, dong + ".html"), "w", encoding="utf-8") as f:
                    f.write(render(depth, parts))
                n += 1
    print(f"  regions/*/*/  {n}개 (대표 행정동)")

# ─────────────────────────────────────────────
# 사이트맵 (색인 + core + 시·도별) / robots
# ─────────────────────────────────────────────
def _urlset(urls):
    items = ""
    for loc, pr in urls:
        items += f'  <url><loc>{loc}</loc><changefreq>weekly</changefreq><priority>{pr}</priority></url>\n'
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'

def build_sitemap():
    base = SITE["domain"]
    sitemap_files = []

    # core: 메인 + 서비스 + 광역 페이지
    core = [(base + "/", "1.0")]
    core += [(f'{base}/services/{s["slug"]}.html', "0.8") for s in SERVICES]
    core += [(f'{base}/{region_url(slug)}', "0.8") for slug,_,_,_ in REGIONS]
    with open(os.path.join(ROOT, "sitemap-core.xml"), "w", encoding="utf-8") as f:
        f.write(_urlset(core))
    sitemap_files.append("sitemap-core.xml")

    # 시·도별: 행정시 허브 + 행정구/시군구 + 읍·면·동
    for sh in HIER:
        sido = sh["sido"]
        slug = sido["slug"]
        urls = []
        for c in sh["cities"]:
            if c["gus"]:
                urls.append((f'{base}/{city_url(slug, c["name"])}', "0.6"))   # 행정시 허브
        for city, gu, dist in iter_units(sh):
            urls.append((f'{base}/{unit_url(slug, city, gu)}', "0.6"))         # 행정구/시군구
            for g in dist_groups(dist):
                urls.append((f'{base}/{dong_url(slug, city, gu, g["repr"])}', "0.5"))
        fn = f"sitemap-{slug}.xml"
        with open(os.path.join(ROOT, fn), "w", encoding="utf-8") as f:
            f.write(_urlset(urls))
        sitemap_files.append(fn)

    # 색인
    idx = "".join(f'  <sitemap><loc>{base}/{fn}</loc></sitemap>\n' for fn in sitemap_files)
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{idx}</sitemapindex>\n'
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

    robots = f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n"
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)
    print(f"  sitemap.xml(색인) + {len(sitemap_files)}개 하위 사이트맵, robots.txt")

if __name__ == "__main__":
    print("빌드 시작…")
    build_images()
    build_index()
    build_services()
    build_regions()
    build_cityhubs()
    build_units()
    build_dongs()
    build_sitemap()
    print("완료!")
