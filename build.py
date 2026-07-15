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
import os, html, json, re, datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DATE = datetime.date.today().isoformat()   # 사이트맵 lastmod

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
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect width='24' height='24' rx='5' fill='%230EA5B7'/%3E%3Cpath d='M12 4s5 5.5 5 9a5 5 0 0 1-10 0c0-3.5 5-9 5-9z' fill='white'/%3E%3C/svg%3E">
<link rel="preload" href="{{FONT}}" as="font" type="font/woff2" crossorigin>
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
    <li><a href="{p}guides/index.html">생활정보</a></li>
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
      <li><a href="{p}guides/index.html">배관 생활정보</a></li>
      <li><a href="{p}index.html#gallery">시공사례</a></li>
      <li><a href="{p}index.html#cost">비용안내</a></li>
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
    p = path_prefix(depth)
    return ("".join(body_parts)
            .replace("{CSS}", p + "assets/css/style.css")
            .replace("{FONT}", p + "assets/fonts/PretendardVariable.woff2"))

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

def ld_site():
    """WebSite + Organization (브랜드 엔티티 강화)."""
    base = SITE["domain"]
    return f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"WebSite","@id":"{base}/#website","url":"{base}/","name":"{SITE['brand']}","inLanguage":"ko-KR","publisher":{{"@id":"{base}/#org"}}}},
{{"@type":"Organization","@id":"{base}/#org","name":"{SITE['brand']}","url":"{base}/","logo":"{base}/assets/img/og-main.svg","telephone":"{SITE['phone_display']}","email":"{SITE['email']}","address":{{"@type":"PostalAddress","streetAddress":"{SITE['addr']}","addressCountry":"KR"}},"areaServed":"KR","contactPoint":{{"@type":"ContactPoint","telephone":"{SITE['phone_display']}","contactType":"customer service","areaServed":"KR","availableLanguage":"Korean"}}}}
]}}
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
    parts = [head(title, desc, "index.html", extra_ld=ld_site() + ld_business())]
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

    # 생활정보(정보성 롱테일) 링크
    gcards = "".join(
        f'<a class="guide-card" href="guides/{g["slug"]}.html"><span class="g-cat">{esc(g["cat"])}</span>'
        f'<h3>{esc(g["title"])}</h3><p>{esc(g["desc"])}</p>'
        f'<span class="g-more">자세히 보기 {ICONS["arrow"]}</span></a>' for g in GUIDES[:6])
    parts.append(f'''<section class="block" id="guides"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">배관 생활정보</span>
    <h2>집에서 먼저 해보는 셀프 가이드</h2>
    <p>변기·하수구 막힘 뚫는 법, 누수 자가진단, 겨울 동파 예방까지. 급할 때 도움이 되는 정보를 모았습니다.</p></div>
  <div class="guide-grid">{gcards}</div>
  <div style="text-align:center;margin-top:22px"><a class="btn btn-ghost" href="guides/index.html">생활정보 전체 보기 {ICONS["arrow"]}</a></div>
</div></section>''')

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
# 생활정보(정보성 롱테일 가이드) — 실제로 도움이 되는 고유 콘텐츠
#  slug, title, cat, service(연결 서비스), date(발행), desc, lead, html(본문), faq
# ─────────────────────────────────────────────
GUIDES = [
    {
        "slug": "byeongi-makhim-tulnun-beop", "cat": "막힘", "service": "makhim", "date": "2026-06-02",
        "title": "변기 막힘, 집에서 뚫는 법과 절대 하면 안 되는 것",
        "desc": "변기가 막혔을 때 집에서 안전하게 뚫는 순서와, 오히려 상황을 악화시키는 금지 행동을 정리했습니다.",
        "lead": "변기가 막히면 당황해서 물을 계속 내리기 쉬운데, 그러면 넘칩니다. 순서대로 침착하게 시도하면 대부분 집에서 해결됩니다.",
        "html": """
<h2>먼저, 물을 더 내리지 마세요</h2>
<p>변기 물이 평소보다 천천히 내려가거나 차오른다면 <b>추가로 물을 내리지 마세요.</b> 변기 뒤 탱크 뚜껑을 열어 물마개(플로트)를 손으로 올리면 물이 더 차는 것을 막을 수 있습니다. 바닥에 신문지·수건을 깔아 넘침에 대비합니다.</p>
<h2>집에서 시도하는 순서</h2>
<ol>
  <li><b>주방세제 + 따뜻한 물</b>: 세제 한 컵을 넣고 <b>따뜻한 물</b>(끓는 물 금지)을 부어 10~20분 두면 기름·유기물이 부드러워집니다.</li>
  <li><b>압축기(플런저·뚫어뻥)</b>: 배수구에 밀착시켜 상하로 힘 있게 여러 번 펌프질합니다. 물이 어느 정도 잠겨 있어야 압력이 걸립니다.</li>
  <li><b>페트병 압력법</b>: 압축기가 없을 때, 입구를 막고 눌러 순간 압력을 주는 임시 방법입니다.</li>
  <li><b>관선(스프링)</b>: 위 방법으로도 안 되면 이물질이나 구조적 막힘일 수 있습니다.</li>
</ol>
<h2>절대 하면 안 되는 것</h2>
<ul>
  <li><b>끓는 물 붓기</b> — 도기에 균열이 생겨 변기를 통째로 교체해야 할 수 있습니다.</li>
  <li><b>물 계속 내리기</b> — 순식간에 넘쳐 바닥·아랫집 피해로 이어집니다.</li>
  <li><b>철사·옷걸이로 무리하게 쑤시기</b> — 도기 내부가 긁히거나 깨질 수 있습니다.</li>
  <li><b>물티슈·기저귀·음식물 흘려보내기</b> — 물에 풀리지 않아 막힘의 가장 흔한 원인입니다.</li>
</ul>
""",
        "faq": [
            ("뚫어뻥으로도 안 뚫려요. 어떻게 하나요?", "장난감·수건 같은 고형물이 걸렸거나 배관 깊은 곳이 막힌 경우입니다. 무리하면 도기가 파손될 수 있으니 관선·내시경 장비로 원인을 확인해 제거하는 편이 안전합니다."),
            ("물티슈는 변기에 버려도 되나요?", "'물에 녹는다'고 표기된 제품도 실제로는 잘 풀리지 않아 막힘의 주원인이 됩니다. 변기에는 화장지 외에 아무것도 버리지 않는 것이 좋습니다."),
        ],
    },
    {
        "slug": "hasugu-naemsae-wonin", "cat": "막힘", "service": "seolbi", "date": "2026-05-20",
        "title": "하수구에서 냄새가 올라올 때 — 원인 5가지와 해결법",
        "desc": "화장실·싱크대 하수구 냄새의 원인 5가지와 집에서 할 수 있는 해결법, 전문가가 필요한 경우를 정리했습니다.",
        "lead": "하수구 냄새는 대부분 '봉수(물막이)'가 마르거나 배관에 찌꺼기가 쌓여 생깁니다. 원인을 알면 해결이 쉽습니다.",
        "html": """
<h2>냄새의 흔한 원인 5가지</h2>
<ol>
  <li><b>봉수(트랩의 물) 증발</b> — 오래 안 쓴 배수구는 냄새를 막아주던 물이 말라 하수 냄새가 올라옵니다.</li>
  <li><b>트랩 없음·파손</b> — 배수구에 트랩이 없거나 깨졌으면 냄새가 그대로 역류합니다.</li>
  <li><b>기름·머리카락 찌꺼기 부패</b> — 배관 벽에 눌어붙은 슬러지가 부패해 악취를 냅니다.</li>
  <li><b>배관 균열·연결 불량</b> — 이음새 틈으로 냄새가 샙니다.</li>
  <li><b>통기(공기) 문제</b> — 물 내릴 때 '꼬르륵' 소리가 나면 통기관 쪽을 의심합니다.</li>
</ol>
<h2>집에서 할 수 있는 해결</h2>
<ul>
  <li>안 쓰는 배수구에도 <b>가끔 물을 흘려 봉수를 유지</b>합니다.</li>
  <li>배수구 <b>트랩·거름망</b>을 설치하고 주기적으로 청소합니다.</li>
  <li><b>베이킹소다 + 식초</b>를 붓고 30분 뒤 따뜻한 물로 헹구면 가벼운 찌꺼기·냄새가 줄어듭니다.</li>
  <li>세면대·변기 <b>바닥 실리콘</b>이 벌어졌으면 다시 마감합니다.</li>
</ul>
""",
        "faq": [
            ("청소해도 냄새가 계속 나요.", "배관 안쪽에 오래 쌓인 슬러지나 균열이 원인일 수 있습니다. 고압세척으로 관 내부를 씻어내거나 내시경으로 상태를 확인하면 근본 원인을 잡을 수 있습니다."),
            ("여러 곳에서 동시에 냄새가 나요.", "공용 배관(횡주관) 쪽 문제일 가능성이 큽니다. 개별 청소로는 한계가 있어 전문 점검을 권합니다."),
        ],
    },
    {
        "slug": "sudoyogeum-nusu-jindan", "cat": "누수", "service": "nusu", "date": "2026-05-06",
        "title": "수도요금이 갑자기 많이 나올 때 — 누수 자가진단 체크리스트",
        "desc": "수도요금이 평소의 2배 이상 나왔다면 누수를 의심해야 합니다. 집에서 할 수 있는 누수 자가진단 방법을 정리했습니다.",
        "lead": "쓰지도 않았는데 요금이 급증했다면 어딘가 물이 새고 있을 가능성이 높습니다. 아래 순서로 확인해 보세요.",
        "html": """
<h2>1분 계량기 테스트</h2>
<p>집 안 모든 수도·세탁기·보일러를 잠근 뒤 <b>수도 계량기</b>를 보세요. 은색 <b>별 모양(팽이) 표시가 계속 돌아가면</b> 어딘가에서 물이 새고 있다는 신호입니다.</p>
<h2>새는 곳 좁히기</h2>
<ul>
  <li><b>변기</b>: 물탱크에 식용색소를 몇 방울 넣고 20분 뒤 변기 물이 색으로 물들면 부속 누수(가장 흔함)입니다.</li>
  <li><b>보일러</b>: 사용하지 않는데 압력이 자꾸 떨어지면 난방·급탕 배관 누수를 의심합니다.</li>
  <li><b>벽·천장</b>: 얼룩·곰팡이·물방울이 반복되면 매립 배관 누수 가능성이 있습니다.</li>
  <li><b>온수만 요금 급증</b>: 온수 배관 쪽 누수일 수 있습니다.</li>
</ul>
<h2>집에서 vs 전문가</h2>
<p>변기 부속·수전 패킹처럼 눈에 보이는 곳은 부품 교체로 해결되기도 합니다. 하지만 <b>벽·바닥 속</b> 누수는 청음식·가스식 <b>누수탐지</b> 장비로 지점을 찾아야 벽을 뜯지 않고 최소 시공으로 잡을 수 있습니다.</p>
""",
        "faq": [
            ("계량기 별이 아주 천천히 돌아요.", "미세 누수일 수 있습니다. 방치하면 요금이 계속 새고 곰팡이·구조 손상으로 이어지니 조기에 탐지받는 것이 좋습니다."),
            ("벽을 꼭 뜯어야 하나요?", "아닙니다. 비파괴 누수탐지로 지점을 먼저 특정하면 해당 부위만 최소로 열어 시공할 수 있습니다."),
        ],
    },
    {
        "slug": "gyeoul-baegwan-dongpa-yebang", "cat": "설비", "service": "seolbi", "date": "2026-01-08",
        "title": "겨울철 배관 동파 예방법과 얼었을 때 안전하게 녹이는 법",
        "desc": "한파에 수도·계량기가 얼지 않도록 예방하는 법과, 이미 얼었을 때 안전하게 녹이는 방법을 정리했습니다.",
        "lead": "배관 동파는 예방이 최선입니다. 한 번 터지면 누수·수리 비용이 크게 늘어나니 미리 대비하세요.",
        "html": """
<h2>동파 예방 체크리스트</h2>
<ul>
  <li><b>노출 배관·계량기함 보온</b>: 보온재나 헌 옷·수건으로 감싸고 계량기함은 비닐로 찬바람을 막습니다.</li>
  <li><b>한파·장기 외출 시 물 조금 틀어두기</b>: 수돗물을 <b>가늘게</b> 흘려두면 얼음이 잘 얼지 않습니다.</li>
  <li><b>실내 온도 유지</b>: 외출 시에도 난방을 완전히 끄지 말고 최소 온도를 유지합니다.</li>
  <li><b>보일러 동파 방지 모드</b> 사용, 외출 모드로 순환시킵니다.</li>
</ul>
<h2>얼었을 때 — 안전하게 녹이기</h2>
<ol>
  <li>따뜻한 물수건을 감싸거나 <b>헤어드라이어</b>로 <b>천천히</b> 녹입니다.</li>
  <li>계량기·노출관은 <b>미지근한 물</b>을 부어가며 녹입니다(끓는 물 금지 — 급격한 온도차로 파열).</li>
  <li><b>토치·열풍기 과열은 금지</b>입니다. 배관 파열·화재 위험이 있습니다.</li>
</ol>
""",
        "faq": [
            ("녹였더니 물이 새요.", "얼면서 배관이 이미 갈라졌을 수 있습니다. 노출관은 부속 교체, 매립관은 누수탐지 후 해당 부위만 시공합니다."),
            ("계량기가 터졌어요.", "계량기 동파는 관리사무소·상수도사업소 또는 전문 업체에 연락해 교체·복구해야 합니다."),
        ],
    },
    {
        "slug": "singkeudae-makhim-tulnun-beop", "cat": "막힘", "service": "makhim", "date": "2026-04-10",
        "title": "싱크대 하수구 막힘 — 원인별로 뚫는 법",
        "desc": "싱크대 물이 안 내려갈 때 원인별 해결법과, 재발을 막는 관리 습관을 정리했습니다.",
        "lead": "싱크대 막힘은 대부분 기름과 음식물 찌꺼기가 뭉친 슬러지 때문입니다. 원인을 알면 손쉽게 뚫을 수 있습니다.",
        "html": """
<h2>집에서 시도하는 방법</h2>
<ol>
  <li><b>따뜻한 물 + 주방세제</b>로 굳은 기름을 녹입니다.</li>
  <li><b>베이킹소다 한 컵 + 식초 한 컵</b>을 붓고 거품이 끝나면 따뜻한 물로 헹굽니다.</li>
  <li><b>압축기</b>로 배수구를 밀착해 펌프질합니다.</li>
  <li>싱크대 아래 <b>S자 트랩</b>을 분리해 안쪽 찌꺼기를 직접 제거합니다(아래 양동이 받치기).</li>
</ol>
<h2>재발을 막는 습관</h2>
<ul>
  <li>기름은 하수구에 붓지 말고 굳혀서 버립니다.</li>
  <li>배수구 <b>거름망</b>으로 음식물을 걸러냅니다.</li>
  <li>주기적으로 따뜻한 물을 흘려 기름이 굳지 않게 합니다.</li>
</ul>
""",
        "faq": [
            ("트랩까지 청소했는데 안 내려가요.", "벽 속 배관이나 공용관까지 막힌 경우입니다. 고압세척으로 관 내부를 씻어내면 재발 없이 뚫립니다."),
            ("뜨거운 물을 부어도 되나요?", "따뜻한 물은 괜찮지만 끓는 물은 배관 종류에 따라 변형을 줄 수 있어 권하지 않습니다."),
        ],
    },
    {
        "slug": "semyeondae-baesugu-makhim", "cat": "막힘", "service": "makhim", "date": "2026-03-18",
        "title": "세면대·욕실 배수구 막힘 셀프 해결법",
        "desc": "머리카락·비누때로 막힌 세면대와 욕실 배수구를 집에서 뚫는 방법과 예방법입니다.",
        "lead": "세면대·욕실 배수구 막힘의 주범은 머리카락과 비누때 뭉치입니다. 도구 하나면 대부분 해결됩니다.",
        "html": """
<h2>집에서 뚫는 방법</h2>
<ol>
  <li><b>머리카락 제거 도구</b>(길고 톱니 있는 플라스틱)를 넣어 뭉친 머리카락을 끌어올립니다.</li>
  <li>세면대 <b>팝업(마개)</b>을 분리해 걸린 이물질을 청소합니다.</li>
  <li><b>베이킹소다 + 식초</b> 후 따뜻한 물로 헹궈 비누때를 녹입니다.</li>
  <li><b>소형 압축기</b>로 배수구를 밀착해 펌프질합니다.</li>
</ol>
<h2>예방</h2>
<ul>
  <li>배수구에 <b>헤어 캐처</b>를 놓아 머리카락을 걸러냅니다.</li>
  <li>월 1회 정도 베이킹소다·식초로 관리합니다.</li>
</ul>
""",
        "faq": [
            ("자꾸 반복해서 막혀요.", "배관 안쪽에 비누때가 두껍게 쌓였거나 구배(기울기) 문제일 수 있습니다. 반복된다면 배관 점검을 권합니다."),
            ("역류까지 생겨요.", "아래쪽 공용 배관 문제일 수 있어, 개별 청소보다 전문 점검이 필요합니다."),
        ],
    },
    {
        "slug": "byeongi-mul-gyesok-heureum", "cat": "교체", "service": "gyoche", "date": "2026-02-26",
        "title": "변기 물이 계속 조금씩 흐를 때 — 원인과 부속 교체",
        "desc": "변기 물탱크에서 물이 계속 새면 수도요금이 조용히 늘어납니다. 원인이 되는 부속과 집에서 확인·교체하는 법을 정리했습니다.",
        "lead": "변기에서 '쫄쫄' 물 흐르는 소리가 멈추지 않는다면 탱크 안 부속 문제일 가능성이 큽니다. 대부분 부속 교체로 해결됩니다.",
        "html": """
<h2>어디서 새는지 먼저 확인</h2>
<ul>
  <li><b>변기 안쪽으로 계속 물이 흐름</b> — 플래퍼(고무마개)·플러시밸브가 노후해 밀봉이 안 되는 경우입니다.</li>
  <li><b>넘침관으로 물이 넘침</b> — 필밸브(볼탭)의 수위 조절이 잘못됐습니다.</li>
  <li><b>물 채우는 소리가 멈추지 않음</b> — 필밸브 고장일 수 있습니다.</li>
</ul>
<h2>집에서 점검·조치</h2>
<ol>
  <li>탱크 뚜껑을 열고 <b>식용색소</b>를 몇 방울 넣어 변기로 색이 새는지 봅니다(플래퍼 밀봉 확인).</li>
  <li>플래퍼에 물때·변형이 있으면 새 것으로 교체합니다.</li>
  <li>필밸브 <b>수위를 넘침관보다 2~3cm 낮게</b> 조절합니다.</li>
  <li>부속은 규격만 맞으면 철물점·마트에서 구입해 교체할 수 있습니다.</li>
</ol>
""",
        "faq": [
            ("부속만 갈면 되나요, 변기를 통째로 바꿔야 하나요?", "대부분 필밸브·플래퍼 같은 부속 교체로 해결됩니다. 도기에 균열이 있거나 바닥에서 물이 새면 변기 교체를 검토합니다."),
            ("어떤 부속을 사야 할지 모르겠어요.", "필밸브·플래퍼는 호환 제품이 많습니다. 모델과 탱크 안 사진을 보여주시면 맞는 부속과 교체를 안내해 드립니다."),
        ],
    },
    {
        "slug": "sudo-kkokji-mulsaem", "cat": "교체", "service": "gyoche", "date": "2026-02-14",
        "title": "수도꼭지에서 물이 샐 때 — 원인과 셀프 점검",
        "desc": "수전 손잡이 아래나 연결부에서 물이 새는 원인과, 집에서 확인할 수 있는 부분을 정리했습니다.",
        "lead": "수도꼭지 물샘은 대부분 내부 패킹·카트리지 마모나 연결부 풀림입니다. 위치를 보면 원인을 좁힐 수 있습니다.",
        "html": """
<h2>새는 위치로 원인 좁히기</h2>
<ul>
  <li><b>손잡이 아래에서 똑똑</b> — 내부 카트리지·패킹(고무 오링) 마모입니다.</li>
  <li><b>수전과 벽/싱크대 연결부</b> — 나사 풀림이나 테프론테이프 노후입니다.</li>
  <li><b>토출구에서 잠가도 계속</b> — 카트리지 불량으로 완전 차단이 안 되는 경우입니다.</li>
</ul>
<h2>집에서 할 수 있는 조치</h2>
<ol>
  <li>먼저 <b>각지 밸브(수전 아래 잠금)</b>나 계량기 밸브로 물을 잠급니다.</li>
  <li>연결부 누수는 분리 후 <b>테프론테이프를 다시 감아</b> 조립합니다.</li>
  <li>내부 누수는 같은 규격 <b>카트리지·패킹으로 교체</b>합니다.</li>
</ol>
""",
        "faq": [
            ("패킹만 갈아도 되나요?", "손잡이 아래 누수는 패킹·카트리지 교체로 해결되는 경우가 많습니다. 수전 본체가 부식·파손됐다면 교체가 낫습니다."),
            ("벽에 묻힌 수전이 새요.", "벽 매립 수전 누수는 타일·벽체 작업이 필요할 수 있어 전문 시공을 권합니다."),
        ],
    },
    {
        "slug": "nusu-makhim-biyong-gaideu", "cat": "비용", "service": "nusu", "date": "2026-01-30",
        "title": "누수·하수구 수리 비용은 무엇으로 정해질까",
        "desc": "누수탐지·하수구 뚫음·배관공사 비용이 달라지는 요인과, 바가지 없이 견적받는 법을 정리했습니다.",
        "lead": "배관 수리는 현장마다 조건이 달라 '정찰가'가 어렵습니다. 대신 비용을 결정하는 요인을 알면 견적을 합리적으로 판단할 수 있습니다.",
        "html": """
<h2>비용을 결정하는 요인</h2>
<ul>
  <li><b>증상 종류</b> — 단순 막힘 뚫음과 누수탐지·배관 교체는 난이도가 다릅니다.</li>
  <li><b>위치</b> — 노출 배관보다 벽·바닥 <b>매립 배관</b>이 손이 더 갑니다.</li>
  <li><b>배관 길이·상태</b> — 노후·부식이 심하면 작업 범위가 커집니다.</li>
  <li><b>사용 장비</b> — 누수탐지기·관로 내시경·고압세척 등 장비에 따라 달라집니다.</li>
  <li><b>자재·접근성·시간대</b> — 자재 등급, 층수·접근성, 야간/긴급 여부가 반영됩니다.</li>
</ul>
<h2>바가지 없이 견적받는 법</h2>
<ol>
  <li>전화로 <b>증상과 지역</b>을 말하고 예상 범위를 먼저 안내받습니다.</li>
  <li>방문 진단 후 <b>확정 견적</b>을 받고, <b>동의 전에는 작업하지 않는지</b> 확인합니다.</li>
  <li>지나치게 싼 유인 뒤 현장에서 금액을 올리는 곳은 주의합니다.</li>
</ol>
""",
        "faq": [
            ("출장비가 따로 있나요?", "업체마다 다릅니다. 전화 시 출장·진단 비용 포함 여부를 미리 확인하세요. 스피드 배관공사는 출동 전 예상 비용을 먼저 안내합니다."),
            ("견적보다 비용이 더 나올 수 있나요?", "추가 작업이 필요하면 반드시 사전에 설명하고 동의를 받은 뒤 진행합니다. 동의 없이 비용이 늘지 않습니다."),
        ],
    },
    {
        "slug": "setakgi-baesu-yeongnyu", "cat": "막힘", "service": "makhim", "date": "2026-01-16",
        "title": "세탁기 배수가 안 되거나 역류할 때",
        "desc": "세탁 중 물이 안 빠지거나 배수구가 역류할 때 원인과 집에서 점검할 부분을 정리했습니다.",
        "lead": "세탁기 배수 문제는 호스나 배수구 이물질이 원인인 경우가 많습니다. 순서대로 점검해 보세요.",
        "html": """
<h2>집에서 점검하는 순서</h2>
<ol>
  <li><b>배수 호스</b>가 꺾이거나 눌리지 않았는지, 끝이 빠지지 않았는지 봅니다.</li>
  <li>세탁기 <b>배수 필터</b>(앞쪽 하단 커버 안)를 열어 실밥·이물질을 청소합니다.</li>
  <li>바닥 <b>배수구</b> 거름망의 머리카락·찌꺼기를 제거합니다.</li>
  <li>배수구에 호스를 너무 깊이 꽂으면 <b>사이펀 현상</b>으로 역류할 수 있어 위치를 조정합니다.</li>
</ol>
""",
        "faq": [
            ("호스·필터 청소해도 물이 안 빠져요.", "바닥 배수구 안쪽이나 공용 배관이 막혔을 수 있습니다. 이 경우 관선·고압세척으로 배관 내부를 뚫어야 합니다."),
            ("세탁할 때마다 배수구가 넘쳐요.", "배수 용량을 넘어서거나 배관이 좁아진 상태일 수 있어 전문 점검을 권합니다."),
        ],
    },
    {
        "slug": "cheunggan-nusu-daecheo", "cat": "누수", "service": "nusu", "date": "2025-12-18",
        "title": "아랫집 천장 누수(층간 누수) — 원인과 슬기로운 대처",
        "desc": "아랫집 천장에 물이 새 이웃과 얽혔을 때, 원인 규명과 대처 순서를 정리했습니다.",
        "lead": "층간 누수는 감정보다 '원인 규명'이 먼저입니다. 어디서 새는지 정확히 찾아야 책임과 해결 방법이 분명해집니다.",
        "html": """
<h2>흔한 원인</h2>
<ul>
  <li>위층 <b>욕실 방수층·배관</b> 누수</li>
  <li><b>급수·난방 배관</b>의 미세 균열</li>
  <li>결로(누수로 오인되는 경우도 많음)</li>
</ul>
<h2>대처 순서</h2>
<ol>
  <li>사진·영상으로 <b>상황을 기록</b>합니다.</li>
  <li>감정적 대응보다 <b>원인 규명(누수탐지)</b>을 먼저 합니다. 지점이 확인돼야 책임 구분과 수리가 명확해집니다.</li>
  <li>공동주택은 <b>관리사무소</b>에 알리고, 필요 시 <b>일상생활 배상책임보험</b> 적용 여부를 확인합니다.</li>
</ol>
""",
        "faq": [
            ("누수 책임이 위층인가요, 아랫집인가요?", "새는 지점이 어디냐에 따라 다릅니다. 비파괴 누수탐지로 원인을 특정하면 책임과 수리 범위를 객관적으로 판단할 수 있습니다."),
            ("벽·천장을 꼭 뜯어야 하나요?", "먼저 누수탐지로 지점을 좁히면 해당 부위만 최소로 열어 확인·시공할 수 있습니다."),
        ],
    },
    {
        "slug": "onsu-an-naol-ttae", "cat": "설비", "service": "seolbi", "date": "2025-12-04",
        "title": "온수가 안 나올 때 — 원인 구분과 점검",
        "desc": "냉수는 나오는데 온수만 안 나올 때, 보일러 문제인지 배관 문제인지 구분하는 법입니다.",
        "lead": "온수만 안 나오는지, 물 전체가 안 나오는지에 따라 원인이 갈립니다. 순서대로 확인해 보세요.",
        "html": """
<h2>먼저 구분하기</h2>
<ul>
  <li><b>냉수는 되고 온수만 안 됨</b> — 보일러 또는 온수 배관 쪽 문제입니다.</li>
  <li><b>물 전체가 안 나옴</b> — 단수, 계량기·배관 동파를 확인합니다.</li>
</ul>
<h2>점검 포인트</h2>
<ol>
  <li>보일러 <b>전원·에러코드</b>와 온수 설정을 확인합니다.</li>
  <li>겨울철이면 <b>동파</b> 여부를 확인합니다(노출 배관·계량기).</li>
  <li>특정 수전만 온수가 약하면 그 <b>수전 내부·필터</b> 막힘일 수 있습니다.</li>
</ol>
""",
        "faq": [
            ("보일러는 정상인데 온수가 약해요.", "온수 배관의 부분 막힘이나 노후, 수전 카트리지 문제일 수 있습니다. 여러 곳이 동시에 약하면 배관 점검을 권합니다."),
            ("갑자기 온수·냉수가 다 안 나와요.", "단수나 동파를 먼저 확인하고, 아니라면 옥내 배관 문제일 수 있어 점검이 필요합니다."),
        ],
    },
    {
        "slug": "hasugu-yakpum-jueui", "cat": "막힘", "service": "makhim", "date": "2025-11-20",
        "title": "하수구 뚫는 약품, 써도 될까? — 주의사항",
        "desc": "시중 하수구 세정제를 쓸 때의 효과와 한계, 배관·안전상 주의점을 정리했습니다.",
        "lead": "하수구 약품은 가벼운 유기물엔 도움이 되지만, 완전 막힘이나 고형물에는 효과가 없고 잘못 쓰면 위험합니다.",
        "html": """
<h2>알아둘 점</h2>
<ul>
  <li>강알칼리·산성 세정제는 <b>배관을 손상</b>시키거나 다른 약품과 섞이면 <b>유독가스</b>가 발생할 수 있습니다.</li>
  <li>물이 완전히 막힌 곳에 부으면 약품이 고여 있어 <b>효과가 없고 위험</b>합니다.</li>
  <li>장난감·수건 같은 <b>고형물</b>에는 소용이 없습니다.</li>
</ul>
<h2>안전하게 쓰려면</h2>
<ol>
  <li>가벼운 냄새·유기물엔 <b>베이킹소다+식초</b>나 효소 세정제를 권합니다.</li>
  <li>사용 시 <b>환기</b>하고 <b>장갑</b>을 끼며, 다른 약품과 <b>절대 섞지 않습니다.</b></li>
  <li>약품을 부어도 안 뚫리면 <b>무리하지 말고</b> 물리적으로 제거해야 합니다.</li>
</ol>
""",
        "faq": [
            ("약품을 여러 번 부어도 안 뚫려요.", "완전 막힘이나 고형물일 가능성이 큽니다. 관선·고압세척으로 물리적으로 제거하는 편이 안전하고 확실합니다."),
            ("변기에도 세정제를 써도 되나요?", "변기 막힘엔 효과가 제한적이고 도기·부속 손상 위험이 있어 권하지 않습니다."),
        ],
    },
    {
        "slug": "supap-yakhal-ttae", "cat": "설비", "service": "seolbi", "date": "2025-11-06",
        "title": "수압이 약할 때 — 원인과 해결",
        "desc": "물이 시원하게 안 나올 때 확인할 원인과 집에서 할 수 있는 조치를 정리했습니다.",
        "lead": "수압 저하는 수전 끝 막힘처럼 간단한 원인부터 배관 노후까지 다양합니다. 범위를 좁혀 보세요.",
        "html": """
<h2>흔한 원인</h2>
<ul>
  <li>수전 끝 <b>에어레이터(거름망)</b>에 석회질·이물질이 낌</li>
  <li><b>필터·감압밸브</b> 설정 문제</li>
  <li>배관 <b>노후·녹</b>으로 관 내부가 좁아짐</li>
  <li>단수·동파, 또는 여러 집이 동시에 약하면 <b>공용 배관</b> 문제</li>
</ul>
<h2>집에서 할 수 있는 조치</h2>
<ol>
  <li>수전 끝 <b>에어레이터를 분리해 청소</b>합니다(가장 흔한 해결).</li>
  <li>집 전체가 약한지, 특정 수전만 약한지 비교합니다.</li>
  <li>온수만 약하면 온수 배관 쪽을 의심합니다.</li>
</ol>
""",
        "faq": [
            ("청소해도 집 전체 수압이 약해요.", "배관 노후·부분 막힘이나 감압밸브 문제일 수 있습니다. 배관 상태 점검 후 세척·교체가 필요할 수 있습니다."),
            ("갑자기 약해졌어요.", "단수·동파를 먼저 확인하세요. 아니라면 배관 이물질·누수 가능성을 점검해야 합니다."),
        ],
    },
    {
        "slug": "isa-interior-baegwan-jeomgeom", "cat": "설비", "service": "seolbi", "date": "2025-10-22",
        "title": "이사·인테리어 전 배관 점검 체크리스트",
        "desc": "입주·리모델링 전에 배관을 미리 점검하면 분쟁과 재공사를 예방할 수 있습니다. 체크리스트로 정리했습니다.",
        "lead": "배관 문제는 입주 후 발견하면 해결이 번거롭습니다. 이사·인테리어 전에 아래 항목을 확인하세요.",
        "html": """
<h2>점검 체크리스트</h2>
<ul>
  <li>천장·싱크대 하부·세면대 아래 <b>누수 흔적(얼룩·곰팡이)</b></li>
  <li>각 수전의 <b>수압</b>과 <b>온수</b> 정상 여부</li>
  <li>싱크대·세면대·바닥 배수구의 <b>배수 속도</b></li>
  <li>변기 <b>부속 상태</b>와 물 새는 소리</li>
  <li>노후 수전·밸브, 계량기 <b>1분 테스트</b>(누수 확인)</li>
  <li>겨울이면 <b>동파 이력</b>과 노출 배관 보온 상태</li>
</ul>
<h2>이럴 땐 미리 공사</h2>
<p>주방·욕실 위치를 바꾸는 리모델링이나 노후 라인 교체는 마감 전에 <b>배관공사</b>를 함께 진행해야 나중에 뜯는 일을 막을 수 있습니다.</p>
""",
        "faq": [
            ("입주 전에 점검하면 뭐가 좋나요?", "누수·막힘·노후를 미리 잡으면 입주 후 분쟁이나 재시공을 줄일 수 있고, 인테리어 일정과 맞춰 한 번에 처리할 수 있습니다."),
            ("구조를 바꾸는데 배관도 옮길 수 있나요?", "수압·배수 구배를 고려해 라인을 다시 잡는 배관공사로 가능합니다. 마감 전에 진행하는 것이 좋습니다."),
        ],
    },
    {
        "slug": "baegwan-upche-goreuneun-beop", "cat": "정보", "service": "nusu", "date": "2025-10-08",
        "title": "좋은 배관 업체 고르는 법 — 바가지 안 당하기",
        "desc": "믿을 수 있는 배관 업체를 고르는 기준과, 과잉 수리·바가지를 피하는 팁을 정리했습니다.",
        "lead": "급할수록 아무 데나 부르기 쉽지만, 몇 가지만 확인하면 실패 확률을 크게 줄일 수 있습니다.",
        "html": """
<h2>확인하면 좋은 것</h2>
<ul>
  <li><b>사업자 등록·연락처·주소</b>가 명확한지</li>
  <li><b>출동 전 예상 비용</b>을 안내하는지</li>
  <li><b>동의 전에는 작업하지 않고</b>, 확정 견적을 제시하는지</li>
  <li><b>정품 자재</b> 사용과 <b>시공 후 점검·A/S</b> 안내</li>
  <li><b>실제 시공사례·후기</b>가 있는지</li>
</ul>
<h2>이런 곳은 주의</h2>
<ul>
  <li>지나치게 싼 금액으로 유인한 뒤 현장에서 크게 올리는 곳</li>
  <li>원인 설명 없이 <b>과도한 교체·전체 공사</b>부터 권하는 곳</li>
  <li>견적을 문서·사진으로 남기지 않는 곳</li>
</ul>
""",
        "faq": [
            ("전화로도 대략 비용을 알 수 있나요?", "증상과 지역을 말씀해 주시면 예상 범위를 안내받을 수 있습니다. 정확한 금액은 방문 진단 후 확정 견적으로 정해집니다."),
            ("과잉 수리인지 어떻게 아나요?", "원인과 필요한 작업을 근거와 함께 설명하는지, 대안을 제시하는지 보세요. 스피드 배관공사는 원인 진단 후 필요한 시공만 안내합니다."),
        ],
    },
]

def build_guides():
    p1 = path_prefix(1)
    # 목록 페이지
    url = "guides/index.html"
    title = f"배관 생활정보 · 셀프 가이드 | {SITE['brand']}"
    desc = "변기·싱크대·하수구 막힘 뚫는 법, 누수 자가진단, 겨울 동파 예방 등 집에서 바로 쓰는 배관 생활정보 모음."
    ld = ld_breadcrumb([("홈", "index.html"), ("생활정보", url)])
    cards = ""
    for g in GUIDES:
        cards += (f'<a class="guide-card" href="{q(g["slug"])}.html">'
                  f'<span class="g-cat">{esc(g["cat"])}</span>'
                  f'<h3>{esc(g["title"])}</h3><p>{esc(g["desc"])}</p>'
                  f'<span class="g-more">자세히 보기 {ICONS["arrow"]}</span></a>')
    parts = [head(title, desc, url, extra_ld=ld)]
    parts.append(header(1))
    parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb">{crumb(1, [("홈","index.html"),("생활정보",None)])}</div>
  <h1>배관 생활정보</h1>
  <p>변기·하수구 막힘, 누수 자가진단, 동파 예방까지. 집에서 바로 시도할 수 있는 방법을 정리했습니다. 스스로 해결이 어려우면 <a href="tel:{SITE["phone_tel"]}">{esc(SITE["emergency"])}</a>로 문의하세요.</p>
</div></section>
<section class="block"><div class="wrap"><div class="guide-grid">{cards}</div></div></section>''')
    parts.append(footer(1))
    with open(os.path.join(_ensure_dir("guides"), "index.html"), "w", encoding="utf-8") as f:
        f.write(render(1, parts))

    # 개별 글
    for i, g in enumerate(GUIDES):
        gurl = f"guides/{g['slug']}.html"
        svc = next(s for s in SERVICES if s["slug"] == g["service"])
        gtitle = f"{g['title']} | {SITE['brand']}"
        art_ld = (f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article",'
                  f'"headline":{json.dumps(g["title"], ensure_ascii=False)},'
                  f'"description":{json.dumps(g["desc"], ensure_ascii=False)},'
                  f'"inLanguage":"ko-KR","datePublished":"{g["date"]}","dateModified":"{BUILD_DATE}",'
                  f'"author":{{"@type":"Organization","name":{json.dumps(SITE["brand"], ensure_ascii=False)}}},'
                  f'"publisher":{{"@type":"Organization","name":{json.dumps(SITE["brand"], ensure_ascii=False)},'
                  f'"logo":{{"@type":"ImageObject","url":"{SITE["domain"]}/assets/img/og-main.svg"}}}},'
                  f'"mainEntityOfPage":"{SITE["domain"]}/{gurl}"}}</script>')
        ld = (ld_breadcrumb([("홈", "index.html"), ("생활정보", "guides/index.html"), (g["title"], gurl)])
              + art_ld + ld_faq(g["faq"]))
        faq_fq = "".join(f'<details><summary>{esc(qq)}</summary><p>{esc(aa)}</p></details>' for qq, aa in g["faq"])
        # 관련 글(다른 가이드) 링크
        rel = [x for x in GUIDES if x["slug"] != g["slug"]][:3]
        rel_links = "".join(f'<li>{ICONS["doc"]}<a href="{q(x["slug"])}.html">{esc(x["title"])}</a></li>' for x in rel)
        parts = [head(gtitle, g["desc"], gurl, extra_ld=ld)]
        parts.append(header(1))
        parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb">{crumb(1, [("홈","index.html"),("생활정보","guides/index.html"),(g["cat"],None)])}</div>
  <h1>{esc(g["title"])}</h1>
  <p>{esc(g["lead"])}</p>
  <div class="g-meta">{ICONS["clock"]} 최종 업데이트 {esc(BUILD_DATE)} · {esc(SITE["brand"])}</div>
</div></section>''')
        parts.append(f'''<section class="block"><div class="wrap two-col">
  <article class="prose article">{g["html"]}
    <h2>이럴 땐 전문가에게 맡기세요</h2>
    <p>위 방법으로 해결되지 않거나 반복해서 문제가 생긴다면 배관 안쪽·공용관 문제일 수 있습니다. {esc(SITE["brand"])}는 <a href="{p1}services/{svc["slug"]}.html">{esc(svc["name"])}</a>를 포함해 누수·막힘·설비 전반을 {esc(SITE["emergency"])}로 처리합니다. 무리한 자가 시공으로 배관·기물이 손상되기 전에 상담하세요.</p>
    <h2>자주 묻는 질문</h2>
    <div class="faq">{faq_fq}</div>
    <h3>관련 생활정보</h3>
    <ul class="rel-list">{rel_links}</ul>
  </article>
  <aside class="side-card">
    <h3>{esc(svc["short"])} 상담 · {esc(SITE["reserve"])}</h3>
    <div class="num">{esc(SITE["phone_display"])}</div>
    <a class="btn btn-primary" href="tel:{SITE["phone_tel"]}">{ICONS["phone"]} 전화 상담</a>
    <ul>
      <li>{ICONS["check"]} {esc(SITE["emergency"])}·연중무휴</li>
      <li>{ICONS["check"]} 출동 전 비용 사전고지</li>
      <li>{ICONS["check"]} 정품 자재·경력 기술자</li>
    </ul>
    <h3 style="margin-top:20px;font-size:15px">전문 서비스</h3>
    <ul>{"".join(f'<li>{ICONS["pin"]}<a href="{p1}services/{s2["slug"]}.html">{esc(s2["name"])}</a></li>' for s2 in SERVICES)}</ul>
  </aside>
</div></section>''')
        parts.append(footer(1))
        with open(os.path.join(_ensure_dir("guides"), f'{g["slug"]}.html'), "w", encoding="utf-8") as f:
            f.write(render(1, parts))
    print(f"  guides/ {len(GUIDES)+1}개 (생활정보)")

def _ensure_dir(*parts):
    d = os.path.join(ROOT, *parts)
    os.makedirs(d, exist_ok=True)
    return d

# ─────────────────────────────────────────────
# 사이트맵 (색인 + core + 시·도별) / robots
# ─────────────────────────────────────────────
def _urlset(urls):
    items = ""
    for loc, pr in urls:
        items += (f'  <url><loc>{loc}</loc><lastmod>{BUILD_DATE}</lastmod>'
                  f'<changefreq>weekly</changefreq><priority>{pr}</priority></url>\n')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}</urlset>\n'

def build_sitemap():
    base = SITE["domain"]
    sitemap_files = []

    # core: 메인 + 서비스 + 광역 페이지
    core = [(base + "/", "1.0")]
    core += [(f'{base}/services/{s["slug"]}.html', "0.8") for s in SERVICES]
    core += [(f'{base}/guides/index.html', "0.7")]
    core += [(f'{base}/guides/{g["slug"]}.html', "0.7") for g in GUIDES]
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
    idx = "".join(f'  <sitemap><loc>{base}/{fn}</loc><lastmod>{BUILD_DATE}</lastmod></sitemap>\n' for fn in sitemap_files)
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{idx}</sitemapindex>\n'
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

    robots = (f"User-agent: *\nAllow: /\n"
              f"Disallow: /404.html\n\nSitemap: {base}/sitemap.xml\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)
    print(f"  sitemap.xml(색인) + {len(sitemap_files)}개 하위 사이트맵, robots.txt")

# ─────────────────────────────────────────────
# 404 페이지 (noindex)
# ─────────────────────────────────────────────
def build_404():
    # 깊은 경로에서도 깨지지 않도록 self-contained(인라인 스타일·절대경로) 구성
    html_doc = f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>페이지를 찾을 수 없습니다 (404) | {esc(SITE['brand'])}</title>
<meta name="robots" content="noindex, follow">
<style>
  body{{margin:0;font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;
    background:linear-gradient(160deg,#0A1A2F,#12283F);color:#fff;min-height:100vh;
    display:grid;place-items:center;text-align:center;padding:24px}}
  .box{{max-width:520px}}
  .code{{font-size:84px;font-weight:900;letter-spacing:-.04em;color:#0EA5B7;line-height:1}}
  h1{{font-size:24px;margin:14px 0 8px}} p{{color:#C7D6E4;margin:0 0 24px;line-height:1.6}}
  .row{{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}}
  a.btn{{display:inline-flex;align-items:center;gap:8px;padding:13px 22px;border-radius:12px;
    font-weight:800;text-decoration:none}}
  .p{{background:#FF6A2B;color:#fff}} .g{{background:rgba(255,255,255,.12);color:#fff}}
</style></head><body>
<div class="box">
  <div class="code">404</div>
  <h1>페이지를 찾을 수 없습니다</h1>
  <p>주소가 바뀌었거나 삭제된 페이지일 수 있습니다.<br>아래에서 원하시는 곳으로 이동하세요.</p>
  <div class="row">
    <a class="btn p" href="/">홈으로</a>
    <a class="btn g" href="/index.html#regions">지역별 시공 보기</a>
    <a class="btn g" href="tel:{SITE["phone_tel"]}">{esc(SITE["reserve"])} {esc(SITE["phone_display"])}</a>
  </div>
</div></body></html>'''
    with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("  404.html")

if __name__ == "__main__":
    print("빌드 시작…")
    build_images()
    build_index()
    build_services()
    build_regions()
    build_cityhubs()
    build_units()
    build_dongs()
    build_guides()
    build_sitemap()
    build_404()
    print("완료!")
