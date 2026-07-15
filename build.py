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
import os, html, json
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
}

def esc(s): return html.escape(s, quote=True)

def logo_svg():
    return ICONS["drop"]

# ─────────────────────────────────────────────
# URL 헬퍼 (한글 경로는 퍼센트 인코딩)
# ─────────────────────────────────────────────
def q(s):
    return quote(s, safe="")

def region_url(slug):
    return f"regions/{slug}.html"

def dist_url(slug, sgg):
    return f"regions/{slug}/{q(sgg)}/"

def dong_url(slug, sgg, dong):
    return f"regions/{slug}/{q(sgg)}/{q(dong)}.html"

def path_prefix(depth):
    return "../" * depth

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
  <span class="tb-note"><span class="blink"></span>{esc(SITE["hours"])} · 전국 어디든 신속 출동</span>
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
  "founder":{{"@type":"Person","name":"{SITE['ceo']}"}}
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

def ld_local(area_name, url, desc):
    """지역(시·도/구·군/동)별 LocalBusiness"""
    base = SITE["domain"]
    return f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Plumber","name":{json.dumps(SITE['brand']+" "+area_name, ensure_ascii=False)},"telephone":"{SITE['phone_display']}","areaServed":{{"@type":"AdministrativeArea","name":{json.dumps(area_name, ensure_ascii=False)}}},"url":"{base}/{url}","description":{json.dumps(desc, ensure_ascii=False)}}}
</script>'''

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
    <span class="eyebrow" style="color:#7FE3EC">전국 24시간 긴급출동</span>
    <h1>물 새고 막혔을 땐,<br><span class="hl">스피드 배관공사</span></h1>
    <p class="lead">누수탐지·하수구막힘·배관설비·수전/변기 교체까지. 전국 어디든 신속하게 출동해 원인을 정확히 찾고 재발 없이 시공합니다.</p>
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
# 광역시·도 페이지 (관할 시·군·구 목록)
# ─────────────────────────────────────────────
def build_regions():
    for sido in DATA:
        slug, short, full, districts = sido["slug"], sido["short"], sido["full"], sido["districts"]
        url = region_url(slug)
        dist_names = "·".join(d["disp"] for d in districts)
        n_dist = len(districts)
        n_dong = sum(len(d["dongs"]) for d in districts)
        title = f"{full} 배관공사·누수탐지·하수구막힘 | {SITE['brand']}"
        desc = (f"{full} 전 지역 배관·누수·하수구 전문. {full} {n_dist}개 시·군·구, {n_dong}개 읍·면·동 "
                f"어디든 24시간 출동. 누수탐지·막힘 뚫음·수전/변기 교체·고압세척.")
        ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),(full,url)])
        ld += ld_local(full, url, f"{full} 배관·누수·하수구 전문 시공")
        parts = [head(title, desc, url, extra_ld=ld)]
        parts.append(header(1))
        parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb"><a href="../index.html">홈</a> › 지역별 시공 › {esc(full)}</div>
  <h1>{esc(full)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{esc(full)} 전역에서 누수탐지·누수공사, 하수구·변기·싱크대 막힘, 수전·변기 교체, 고압세척까지 24시간 신속 출동합니다. 아래에서 우리 시·군·구를 선택하면 읍·면·동 단위 안내까지 확인할 수 있습니다.</p>
</div></section>''')

        # 시·군·구 목록
        dist_links = "".join(
            f'<a href="{slug}/{q(d["name"])}/">{esc(d["disp"])} <small>({len(d["dongs"])}개 동)</small> {ICONS["arrow"]}</a>'
            for d in districts)
        parts.append(f'''<section class="block"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">{esc(full)} 시·군·구</span>
    <h2>{esc(full)} 시·군·구별 배관 시공 안내</h2>
    <p>{esc(full)}는 {esc(dist_names)} 등 {n_dist}개 시·군·구로 이루어져 있습니다. 지역을 선택하세요.</p></div>
  <div class="region-grid">{dist_links}</div>
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
        parts.append(footer(1))
        d = os.path.join(ROOT, "regions")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(render(1, parts))
    print(f"  regions/ {len(DATA)}개 (광역시·도)")

# ─────────────────────────────────────────────
# 시·군·구 페이지 (행정구) — 관할 읍·면·동 목록
# ─────────────────────────────────────────────
def build_districts():
    n = 0
    for sido in DATA:
        slug, short, full = sido["slug"], sido["short"], sido["full"]
        for dist in sido["districts"]:
            name, disp, dongs = dist["name"], dist["disp"], dist["dongs"]
            url = dist_url(slug, name)                 # regions/<slug>/<구>/
            area = f"{full} {disp}"
            dong_names = "·".join(x["name"] for x in dongs)
            title = f"{disp} 배관공사·누수·하수구막힘 | {full} {SITE['brand']}"
            desc = (f"{full} {disp} 배관·누수·하수구 전문. {dong_names} 등 {len(dongs)}개 동 어디든 "
                    f"24시간 출동. 누수탐지·하수구막힘·변기/수전 교체·고압세척.")
            ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),
                                (full,region_url(slug)),(disp,url)])
            ld += ld_local(area, url, f"{area} 배관·누수·하수구 전문 시공")
            parts = [head(title, desc, url, extra_ld=ld)]
            parts.append(header(3))
            parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb"><a href="../../../index.html">홈</a> › <a href="../../{slug}.html">{esc(full)}</a> › {esc(disp)}</div>
  <h1>{esc(area)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{esc(area)} 전역에서 누수탐지·누수공사, 하수구·변기·싱크대 막힘, 수전·변기 교체, 고압세척까지 24시간 신속 출동합니다. {esc(disp)} 내 우리 동네를 선택하면 동별 안내를 확인할 수 있습니다.</p>
</div></section>''')

            dong_links = "".join(
                f'<a href="{q(x["name"])}.html">{esc(x["name"])} {ICONS["arrow"]}</a>' for x in dongs)
            parts.append(f'''<section class="block"><div class="wrap">
  <div class="sec-head"><span class="eyebrow">{esc(disp)} 읍·면·동</span>
    <h2>{esc(disp)} 동별 배관 시공 안내</h2>
    <p>{esc(disp)}는 {esc(dong_names)} 등 {len(dongs)}개 행정동으로 이루어져 있습니다. 우리 동네를 선택하세요.</p></div>
  <div class="region-grid">{dong_links}</div>
</div></section>''')

            parts.append(f'''<section class="block mist"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(disp)}에서 이용 가능한 서비스</h2>
    <p>{esc(area)}의 오래된 주택부터 신축 아파트, 상가·사무실까지 현장 특성에 맞춰 시공합니다. 누수·막힘·교체·설비 어떤 상황이든 원인을 정확히 진단하고 재발 없이 처리합니다.</p>
    <div class="svc-cats" style="grid-template-columns:1fr 1fr;margin-top:14px">{service_cards(3)}</div>
    <h3>{esc(disp)} 비용·가격 안내</h3>
    <p>{esc(area)} 내 출동 비용과 시공 가격은 증상·자재·난이도에 따라 달라집니다. 전화로 증상을 알려주시면 예상 비용을 먼저 안내하고, 방문 진단 후 확정 견적을 드립니다. 동의 없이 추가 비용은 발생하지 않습니다.</p>
  </div>
  {side_card(3, area)}
    <h3 style="margin-top:20px;font-size:15px">{esc(full)} 다른 지역</h3>
    <ul><li>{ICONS["pin"]}<a href="../../{slug}.html">{esc(full)} 전체 보기</a></li></ul>
  </aside>
</div></section>''')
            parts.append(footer(3))
            outdir = os.path.join(ROOT, "regions", slug, name)
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
                f.write(render(3, parts))
            n += 1
    print(f"  regions/*/  {n}개 (시·군·구 = 행정구)")

# ─────────────────────────────────────────────
# 읍·면·동 페이지 (행정동)
# ─────────────────────────────────────────────
def build_dongs():
    n = 0
    for sido in DATA:
        slug, short, full = sido["slug"], sido["short"], sido["full"]
        for dist in sido["districts"]:
            dname, disp, dongs = dist["name"], dist["disp"], dist["dongs"]
            dcount = len(dongs)
            for i, x in enumerate(dongs):
                dong = x["name"]
                url = dong_url(slug, dname, dong)
                area = f"{full} {disp} {dong}"
                title = f"{disp} {dong} 배관공사·누수·하수구막힘 | {SITE['brand']}"
                desc = (f"{full} {disp} {dong} 배관·누수·하수구 전문. {dong} 누수탐지, 하수구막힘, "
                        f"싱크대·세면대·변기 막힘, 수전/변기 교체, 고압세척까지 24시간 출동. 출동 전 비용 안내.")
                ld = ld_breadcrumb([("홈","index.html"),("지역별 시공","index.html#regions"),
                                    (full,region_url(slug)),(disp,dist_url(slug,dname)),(dong,url)])
                ld += ld_local(area, url, f"{area} 배관·누수·하수구 전문 시공")
                parts = [head(title, desc, url, extra_ld=ld)]
                parts.append(header(3))
                parts.append(f'''<section class="subhero"><div class="wrap">
  <div class="crumb"><a href="../../../index.html">홈</a> › <a href="../../{slug}.html">{esc(full)}</a> › <a href="./">{esc(disp)}</a> › {esc(dong)}</div>
  <h1>{esc(disp)} {esc(dong)} 배관공사·누수탐지·하수구막힘</h1>
  <p>{esc(area)}에서 누수가 의심되거나 하수구·변기·싱크대가 막혔다면 스피드 배관공사로 연락하세요. {esc(dong)} 인근에 신속하게 출동해 원인을 정확히 진단하고 재발 없이 시공합니다. 출동 전 예상 비용을 먼저 안내합니다.</p>
</div></section>''')

                # 이웃 행정동(내부 링크): 같은 구의 앞뒤 동
                near = []
                for k in range(1, 9):
                    if len(near) >= 8: break
                    j = (i + k) % dcount
                    if j == i: continue
                    near.append(dongs[j])
                near = near[:8]
                near_links = "".join(
                    f'<a href="{q(nb["name"])}.html">{esc(nb["name"])} {ICONS["arrow"]}</a>' for nb in near)

                parts.append(f'''<section class="block"><div class="wrap two-col">
  <div class="prose">
    <h2>{esc(dong)} 배관 문제, 스피드 배관공사가 해결합니다</h2>
    <p>{esc(area)}는 {esc(disp)}에 속한 지역으로, 오래된 주택과 아파트·상가가 함께 있어 배관 노후로 인한 누수·막힘 문의가 꾸준합니다. 천장이나 벽의 얼룩, 원인 모를 수도요금 증가는 누수 신호일 수 있고, 물이 잘 안 내려가거나 역류한다면 배관 막힘일 수 있습니다.</p>
    <p>{esc(dong)}에서 이런 증상이 있다면 방치하지 말고 상담하세요. 청음식·가스식 누수탐지 장비와 관로 내시경으로 정확히 진단한 뒤, 필요한 시공만 확정 견적으로 안내하고 진행합니다.</p>
    <h3>{esc(dong)}에서 이용 가능한 서비스</h3>
    <div class="svc-cats" style="grid-template-columns:1fr 1fr;margin-top:14px">{service_cards(3)}</div>
    <h3>{esc(dong)} 비용·가격 안내</h3>
    <p>{esc(area)} 출동 비용과 시공 가격은 증상·자재·난이도에 따라 달라집니다. 전화로 증상을 알려주시면 예상 비용을 먼저 안내하고, 방문 진단 후 확정 견적을 드립니다. 동의 없이 추가 비용은 발생하지 않습니다.</p>
    <h3>{esc(disp)} 인근 동네</h3>
    <div class="region-grid">{near_links}</div>
  </div>
  {side_card(3, area)}
    <h3 style="margin-top:20px;font-size:15px">상위 지역</h3>
    <ul>
      <li>{ICONS["pin"]}<a href="./">{esc(disp)} 전체</a></li>
      <li>{ICONS["pin"]}<a href="../../{slug}.html">{esc(full)} 전체</a></li>
    </ul>
  </aside>
</div></section>''')
                parts.append(footer(3))
                outdir = os.path.join(ROOT, "regions", slug, dname)
                os.makedirs(outdir, exist_ok=True)
                with open(os.path.join(outdir, dong + ".html"), "w", encoding="utf-8") as f:
                    f.write(render(3, parts))
                n += 1
    print(f"  regions/*/*/  {n}개 (읍·면·동 = 행정동)")

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

    # 시·도별: 시·군·구 + 읍·면·동
    for sido in DATA:
        slug = sido["slug"]
        urls = []
        for dist in sido["districts"]:
            urls.append((f'{base}/{dist_url(slug, dist["name"])}', "0.6"))
            for x in dist["dongs"]:
                urls.append((f'{base}/{dong_url(slug, dist["name"], x["name"])}', "0.5"))
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
    build_districts()
    build_dongs()
    build_sitemap()
    print("완료!")
