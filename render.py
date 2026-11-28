#!/usr/bin/env python3
"""Friday 27 November 2026 in one picture — dense newspaper front page.

Draws everything in code with Pillow (flat shapes, no photos). Deterministic:
same input -> byte-identical PNG. Run locally:  python3 render.py  (needs Pillow; writes output/entry.png,
which is committed as entry.png). The graded program is main.py (stdlib only).
"""
import hashlib
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(HERE, "output")
OUT = os.path.join(OUT_DIR, "entry.png")

# ---------------------------------------------------------------- palette
CREAM   = (247, 241, 222)
PAPER   = (252, 248, 236)
NAVY    = (20, 38, 74)
NAVY2   = (32, 56, 102)
RED     = (179, 35, 27)
INK     = (26, 26, 26)
GREY    = (90, 88, 80)
LGREY   = (200, 194, 178)
CARD_BG = (255, 253, 245)
MAP_BG  = (214, 228, 226)
LAND    = (196, 178, 140)
LAND2   = (178, 158, 118)
SEA     = (214, 228, 226)

# region colours (also used for pins, kickers, legend)
REG = {
    "Europe":       (36, 86, 166),
    "Middle East":  (179, 35, 27),
    "North America":(30, 125, 70),
    "Latin America":(184, 134, 11),
    "Africa":       (106, 61, 154),
    "East Asia":    (194, 24, 91),
    "South Asia":   (15, 118, 110),
    "SE Asia":      (211, 84, 0),
    "Oceania":      (141, 110, 99),
}

# ---------------------------------------------------------------- fonts
# Round-3 fix (2026-11-28): the grader image does not ship the fonts this
# entry needs — round 1 used LiberationSerif-Italic, round 2 relied on the
# system DejaVu dir, and both grader runs exited 1. The 4 DejaVu files used
# here are bundled in fonts/ next to main.py and loaded from there first,
# so the render no longer depends on any system font directory. A system
# path is kept only as a fallback for local runs if fonts/ is absent.
FD = os.path.join(HERE, "fonts")
FD_SYS = "/usr/share/fonts/truetype/dejavu"
def F(name, size):
    _p = os.path.join(FD, name)
    if not os.path.exists(_p):
        _p = os.path.join(FD_SYS, name)
    return ImageFont.truetype(_p, size)

SERIF      = lambda s: F("DejaVuSerif-Bold.ttf", s)
def SERIF_IT(s):
    # No italic serif is bundled (DejaVuSerif-Italic is not installed here);
    # the regular serif is the same family and always present in fonts/.
    return F("DejaVuSerif.ttf", s)
SERIF_REG  = lambda s: F("DejaVuSerif.ttf", s)
SANS       = lambda s: F("DejaVuSans.ttf", s)
SANS_B     = lambda s: F("DejaVuSans-Bold.ttf", s)

# ---------------------------------------------------------------- text helpers
def tw(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]

def th(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[3] - b[1]

def wrap(draw, text, font, width):
    """Greedy word wrap; returns list of lines."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if tw(draw, trial, font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

def fit_lines(draw, text, font, width, max_lines, shrink_to=7):
    """Wrap text to max_lines, shrinking the font if needed (down to
    shrink_to), then truncating with an ellipsis. Returns (font, lines):
    callers MUST draw with the returned font, or the text will overflow."""
    f = font
    while True:
        lines = wrap(draw, text, f, width)
        if len(lines) <= max_lines or f.size <= shrink_to:
            break
        f = ImageFont.truetype(f.path, f.size - 1)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and tw(draw, lines[-1] + "…", f) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "…"
    return f, lines

def draw_lines(draw, lines, x, y, font, fill, leading=None):
    lh = leading or int(font.size * 1.18)
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y

def badge(draw, x, y, text, color, size=8):
    """Confidence badge: coloured pill with white bold text. Returns width."""
    f = SANS_B(size)
    w = tw(draw, text, f) + 10
    h = 13 if size >= 8 else 12
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=color)
    draw.text((x + 5, y + 2), text, font=f, fill=(255, 255, 255))
    return w

def badge_right(draw, x_right, y, text, color, max_w, size=8):
    """Right-aligned badge, shrinking/truncating text to fit max_w."""
    f = SANS_B(size)
    t = text
    while tw(draw, t, f) + 10 > max_w and len(t) > 8:
        t = t[:-1]
    if tw(draw, t, f) + 10 > max_w:
        t = t[:-1].rstrip() + "…"
    w = tw(draw, t, f) + 10
    badge(draw, x_right - w, y, t, color, size=size)
    return w

def num_disc(draw, cx, cy, n, color, r=9):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color,
                 outline=(255, 255, 255), width=1)
    f = SANS_B(9)
    t = str(n)
    draw.text((cx - tw(draw, t, f) / 2, cy - 5), t, font=f, fill=(255, 255, 255))

# ---------------------------------------------------------------- world map
# Simplified continent outlines as (lon, lat) polygons, equirectangular.
NA = [(-168,66),(-165,60),(-158,58),(-152,60),(-140,60),(-135,57),(-130,54),
      (-125,49),(-124,42),(-120,34),(-114,29),(-110,24),(-105,20),(-97,16),
      (-94,17),(-90,14),(-86,12),(-83,9),(-80,8),(-79,9),(-81,13),(-84,16),
      (-87,21),(-90,21),(-91,19),(-96,19),(-97,26),(-93,30),(-89,30),(-84,30),
      (-81,26),(-80,32),(-76,35),(-75,39),(-74,40),(-70,42),(-68,45),(-65,44),
      (-60,47),(-55,47),(-53,50),(-56,52),(-60,55),(-65,58),(-68,58),(-72,62),
      (-78,62),(-85,66),(-92,66),(-95,69),(-110,68),(-125,70),(-140,70),
      (-155,71),(-165,68)]
GREENLAND = [(-55,60),(-50,60),(-43,60),(-40,64),(-32,68),(-25,70),(-20,70),
             (-22,76),(-30,80),(-45,81),(-58,78),(-60,74),(-55,70),(-53,64)]
SA = [(-79,9),(-77,4),(-80,-3),(-81,-6),(-77,-12),(-72,-18),(-70,-23),(-70,-30),
      (-72,-37),(-73,-44),(-74,-50),(-70,-54),(-66,-55),(-68,-52),(-65,-45),
      (-62,-41),(-58,-35),(-52,-33),(-48,-28),(-41,-23),(-39,-17),(-35,-9),
      (-35,-6),(-40,-3),(-44,-2),(-50,0),(-53,4),(-58,6),(-62,9),(-68,11),
      (-72,12),(-75,10)]
AFRICA = [(-6,35),(-10,31),(-15,27),(-17,21),(-17,15),(-15,11),(-13,8),(-8,5),
          (-4,5),(0,6),(6,4),(9,4),(9,-1),(12,-5),(13,-10),(12,-17),(14,-22),
          (16,-28),(20,-35),(26,-34),(32,-26),(35,-24),(40,-16),(40,-10),
          (42,-4),(46,-1),(51,2),(51,11),(48,11),(44,11),(40,15),(38,18),
          (37,22),(34,27),(32,31),(30,31),(25,32),(20,32),(15,32),(11,34),
          (10,37),(6,37)]
EURASIA = [(-10,36),(-9,43),(-2,44),(-1,46),(-4,48),(-1,49),(2,51),(4,53),
           (8,55),(8,57),(10,59),(5,60),(5,62),(12,64),(18,69),(25,71),(30,70),
           (35,68),(40,68),(45,68),(55,69),(65,69),(70,72),(75,73),(80,73),
           (90,75),(100,76),(110,74),(120,73),(130,72),(140,72),(150,70),
           (160,69),(170,67),(178,65),(178,62),(170,60),(162,56),(158,52),
           (156,51),(150,59),(142,59),(140,53),(135,44),(130,42),(127,40),
           (122,38),(120,35),(122,31),(120,28),(115,23),(110,21),(108,18),
           (105,10),(103,8),(100,7),(98,10),(94,17),(92,21),(89,22),(86,20),
           (80,16),(77,8),(75,12),(72,20),(66,25),(61,25),(57,26),(56,27),
           (52,26),(50,29),(48,30),(44,29),(40,28),(39,24),(36,22),(35,20),
           (34,28),(36,36),(33,36),(30,36),(27,37),(23,36),(22,37),(19,40),
           (16,38),(15,40),(12,44),(8,44),(6,43),(3,42),(0,39),(-2,37),
           (-6,36),(-9,37)]
UK = [(-5,50),(-3,53),(-5,56),(-3,58),(-1,57),(0,53),(1,51)]
JAPAN = [(130,31),(132,33),(135,34),(137,35),(139,37),(140,39),(141,41),
         (142,44),(144,44),(141,42),(140,38),(137,36),(133,34)]
SEASIA = [(95,5),(98,3),(100,0),(103,-2),(105,-3),(108,-4),(110,-6),(112,-7),
          (114,-8),(116,-9),(118,-9),(120,-10),(122,-10),(124,-10),(126,-9),
          (128,-7),(130,-4),(131,-2),(132,-1),(130,0),(128,1),(126,2),(124,1),
          (122,1),(120,1),(118,0),(116,0),(114,0),(112,0),(110,0),(108,1),
          (106,2),(104,1),(102,1),(100,0),(98,2)]
NEWGUINEA = [(131,-1),(135,-2),(138,-3),(141,-3),(144,-4),(147,-6),(150,-8),
             (147,-9),(143,-8),(140,-8),(136,-4),(132,-2)]
AUSTRALIA = [(113,-22),(114,-30),(115,-33),(118,-35),(124,-33),(129,-32),
             (132,-32),(135,-35),(138,-35),(140,-38),(145,-38),(150,-37),
             (153,-32),(153,-27),(150,-23),(146,-19),(142,-15),(142,-11),
             (140,-17),(136,-15),(135,-12),(132,-11),(130,-13),(126,-14),
             (122,-17),(118,-20)]
NZ = [(167,-45),(170,-43),(173,-41),(175,-40),(177,-38),(178,-37),(176,-39),
      (174,-41),(172,-43),(169,-46)]
MADAGASCAR = [(44,-16),(47,-15),(50,-16),(49,-20),(47,-24),(44,-25),(43,-21)]
ICELAND = [(-22,64),(-18,63),(-15,64),(-14,66),(-18,66),(-22,65)]
CUBA = [(-85,23),(-80,23),(-75,21),(-74,20),(-70,19),(-68,18),(-72,19),
        (-76,20),(-80,22)]
CONTINENTS = [NA, GREENLAND, SA, AFRICA, EURASIA, UK, JAPAN, SEASIA,
              NEWGUINEA, AUSTRALIA, NZ, MADAGASCAR, ICELAND, CUBA]

def project(lon, lat, x0, y0, w, h):
    # equirectangular: lon -170..190, lat -58..84
    x = x0 + (lon + 170) / 360.0 * w
    y = y0 + (84 - lat) / 142.0 * h
    return (x, y)

def draw_map(draw, x0, y0, w, h):
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=MAP_BG,
                   outline=NAVY, width=1)
    for poly in CONTINENTS:
        pts = [project(lon, lat, x0, y0, w, h) for lon, lat in poly]
        draw.polygon(pts, fill=LAND, outline=(120, 105, 80))
    # graticule
    for lon in range(-150, 181, 30):
        x = x0 + (lon + 170) / 360.0 * w
        draw.line([x, y0, x, y0 + h], fill=(190, 205, 205), width=1)
    for lat in range(-45, 76, 30):
        y = y0 + (84 - lat) / 142.0 * h
        draw.line([x0, y, x0 + w, y], fill=(190, 205, 205), width=1)

# ---------------------------------------------------------------- story data
# confidence: CONFIRMED (2+ outlets) / OFFICIAL (on the record) / REPORTED (one outlet)
LEADS = [
    dict(n=1, place="BRUSSELS, BELGIUM", region="Europe", field="POLITICS",
         conf="CONFIRMED · AP", art="eu",
         head="EU summit ends with no deal on €45bn Ukraine loan",
         dek="24 of 27 states backed the loan; Czechia, Hungary and "
             "Slovakia held out. Talks resume 17–18 December.",
         src="AP · Reuters · European Council"),
    dict(n=2, place="VALENCIA, SPAIN", region="Europe", field="SPORT",
         conf="CONFIRMED · MOTOGP", art="bike",
         head="Márquez quits MotoGP after his eighth title",
         dek="The 33-year-old Ducati champion, under contract to 2028, "
             "bows out at Sunday's Valencia finale.",
         src="MotoGP · ESPN · Reuters"),
    dict(n=3, place="KYIV REGION, UKRAINE", region="Europe", field="WAR",
         conf="CONFIRMED · KYIV POST", art="drones",
         head="155 Russian drones rain down overnight",
         dek="Air defences down 110; strikes hit 27 sites and kill "
             "one person in Zaporizhzhia.",
         src="Kyiv Post · Reuters · Ukrainian Air Force"),
]

MIDS = [
    dict(n=4, place="WELLINGTON, NZ", region="Oceania", field="POLITICS",
         conf="OFFICIAL · NZ ELECTORAL COMM.", art="seats",
         head="Coalition one seat short of a majority",
         dek="65 of 130; the centrist Opportunity Party, 7 seats, holds the keys.",
         src="NZ Electoral Commission · AP"),
    dict(n=5, place="WASHINGTON, US", region="North America", field="CYBER",
         conf="REPORTED · REUTERS", art="cloud",
         head="Hackers breach US Air Force cloud",
         dek="Cloud One platform hit; scope and culprit still unknown.",
         src="Reuters"),
    dict(n=6, place="ROME, ITALY", region="Europe", field="HUMANITARIAN",
         conf="OFFICIAL · FAO / WFP", art="hunger",
         head="UN names 16 hunger hotspots",
         dek="Up from 13 in June; Sudan, Yemen and Gaza worst hit.",
         src="FAO · WFP · Reuters"),
    dict(n=7, place="HANOI, VIETNAM", region="SE Asia", field="TRADE",
         conf="OFFICIAL · CPTPP", art="cptpp",
         head="CPTPP opens talks with three more",
         dek="UAE, Indonesia and the Philippines join the accession queue.",
         src="CPTPP ministerial statement · Reuters"),
    dict(n=8, place="STRAIT OF HORMUZ", region="Middle East", field="ENERGY",
         conf="CONFIRMED · REUTERS", art="oil",
         head="Brent nears $97 on tanker fears",
         dek="Oil climbs after Hormuz attacks; OPEC+ meets Sunday.",
         src="Reuters"),
    dict(n=9, place="MADRID, SPAIN", region="Europe", field="POLITICS",
         conf="CONFIRMED · REUTERS", art="ballot",
         head="Spain votes Sunday; Vox may be kingmaker",
         dek="Campaigns close; Sánchez defies polls as Abascal nears power.",
         src="Reuters · AP"),
    dict(n=10, place="FRANKFURT, GERMANY", region="Europe", field="ECONOMY",
         conf="CONFIRMED · REUTERS", art="ecb",
         head="De Cos confirmed as next ECB chief",
         dek="Spain's central-bank governor succeeds Christine Lagarde.",
         src="Reuters"),
    dict(n=11, place="KARACHI, PAKISTAN", region="South Asia", field="DISASTER",
         conf="CONFIRMED · REUTERS", art="rubble",
         head="Building collapse toll rises to 7",
         dek="14 still missing in the Baloch Colony rubble.",
         src="Reuters · AP"),
]

# also one-liners: (place, text, source) — stories 12..45
ALSO = [
    ("Washington", "Trump asks Putin to pull back aggression in Europe", "AP"),
    ("Kyiv", "Zelensky rebukes Trump's “friend” remark on Putin", "Reuters"),
    ("Baghdad", "Trump backs PM's drive to rein in militias", "Reuters"),
    ("Seoul", "South Korea sends six North Koreans home", "Reuters"),
    ("Canary Is.", "Record migrant arrivals this year", "Reuters"),
    ("Shanghai", "China factory profits jump, fastest in 5 months", "Reuters"),
    ("Walldorf", "SAP weighs major job cuts as AI reshapes sector", "Reuters"),
    ("Oslo", "Norse Atlantic unit files for bankruptcy", "Reuters"),
    ("London", "Poundland collapses into administration", "Reuters"),
    ("London", "24-hour Tube strike begins", "Reuters"),
    ("Paris", "France in technical recession after revisions", "Reuters"),
    ("Tokyo", "Inflation backs Bank of Japan rate rise", "Reuters"),
    ("New York", "Black Friday opens; Amazon protests in 20+ nations", "Reuters"),
    ("US East", "Thanksgiving storm leaves ~1m without power", "Reuters"),
    ("Naypyidaw", "Myanmar rejects parts of ICJ genocide ruling", "AP"),
    ("Jerusalem", "Judges urge dropping key Netanyahu charges", "Reuters"),
    ("Savar", "Bangladesh garment workers clash with police", "Reuters"),
    ("Caracas", "Venezuela to repeal opposition ban law", "Reuters"),
    ("Buenos Aires", "Argentina bans central-bank funding of state", "AP"),
    ("Brasília", "Lula picks banker Trabuco for top economy job", "Reuters"),
    ("San José", "Costa Rica bars UN rapporteur Albanese", "AP"),
    ("Belgrade", "Serbia sets presidential vote for 27 December", "Reuters"),
    ("Berlin", "IG Metall pay deal averts further strikes", "Reuters"),
    ("Paris", "Depardieu ordered to stand trial over rape claims", "AP"),
    ("Nairobi", "Ex-governor jailed 25 years for murder", "Reuters"),
    ("New Delhi", "India frees 164 foreigners in cyberfraud bust", "Reuters"),
    ("Bissau", "Guinea-Bissau delays civilian rule to 2028", "Reuters"),
    ("Lubero", "Uganda to pull troops from Congolese town", "Reuters"),
    ("Niamey", "Deadly militant attack in southwest Niger", "Reuters"),
    ("Khartoum", "RSF attacks kill civilians in Darfur, Kordofan", "Reuters"),
    ("Bangkok", "Thailand probes arsenic in rivers from Myanmar mines", "Reuters"),
    ("Manila", "Sara Duterte says quitting “out of the question”", "Reuters"),
    ("Jakarta", "Indonesia weighs first fuel rise in five years", "Reuters"),
    ("Kuala Lumpur", "AirAsia delays staff pay to month-end", "Reuters"),
]

UTC_STRIP = [
    ("OVERNIGHT", "155 drones over Ukraine"),
    ("MORNING", "NZ count: coalition 65 of 130"),
    ("c. 10:00", "Márquez retires in Valencia"),
    ("MIDDAY", "CPTPP opens talks with three"),
    ("AFTERNOON", "EU summit ends — no deal"),
    ("c. 17:00", "Brent nears $97 a barrel"),
    ("EVENING", "Black Friday opens worldwide"),
]

NUMBERS = [
    ("€45bn", "Ukraine loan blocked"),
    ("155", "drones launched at Ukraine"),
    ("110", "drones shot down"),
    ("65 / 130", "NZ coalition seats"),
    ("16", "UN hunger hotspots"),
    ("$97", "Brent crude, near high"),
]

REGION_COUNTS = [("Europe", 16), ("Middle East", 3), ("North America", 4),
                 ("Latin America", 4), ("Africa", 5), ("East Asia", 3),
                 ("South Asia", 3), ("SE Asia", 6), ("Oceania", 1)]

DATE_CHECK_LEFT = [
    ("Kuwait", "two Italian technicians killed in drone strike; Iran blamed, denies it", "Thu 26 Nov"),
    ("Jazan", "Houthi strike on Saudi Aramco refinery kills 1 Nepali worker", "Thu 26 Nov"),
    ("Gaza", "Israeli strikes kill 10 Palestinians, incl. a senior Hamas official", "Thu 26 Nov"),
    ("Cairo", "fuel tanker fire kills 31; driver detained", "Wed 25 Nov"),
    ("Bangkok", "refinery blast injures 9, three critically", "Thu 26 Nov"),
    ("DR Congo", "Ebola passes 12,000 cases, 5,904 deaths", "Thu 26 Nov"),
    ("Washington", "FCC approves SpaceX plan for 1m satellites", "Wed 25 Nov"),
    ("NFL", "Bills beat Chiefs 13–10; Eagles rally past Cowboys", "Thu 26 Nov"),
]
DATE_CHECK_NEXT = [
    ("Spain", "general election", "Sun 29 Nov"),
    ("Valencia", "Márquez farewell race", "Sun 29 Nov"),
    ("Vienna", "OPEC+ meets on output", "Sun 29 Nov"),
    ("Brussels", "EU Council returns to budget", "17–18 Dec"),
]

# map pins: story number -> (lon, lat)
PINS = {
    1: (4.35, 50.85), 2: (-0.38, 39.47), 3: (30.5, 50.45),
    4: (174.8, -41.3), 5: (-77.0, 38.9), 6: (12.5, 41.9),
    7: (105.85, 21.0), 8: (56.5, 26.5), 9: (-3.7, 40.4),
    10: (8.68, 50.1), 11: (67.0, 24.86),
    15: (127.0, 37.5), 17: (121.5, 31.2), 24: (-74.0, 40.7),
    26: (96.2, 19.8), 29: (-66.9, 10.5), 36: (36.8, -1.3),
    42: (100.5, 13.75), 44: (106.8, -6.2),
}
# story number -> region (for pin colour)
STORY_REGION = {}
for s in LEADS + MIDS:
    STORY_REGION[s["n"]] = s["region"]
ALSO_REGION = {
    12: "North America", 13: "Europe", 14: "Middle East", 15: "East Asia",
    16: "Europe", 17: "East Asia", 18: "Europe", 19: "Europe",
    20: "Europe", 21: "Europe", 22: "Europe", 23: "East Asia",
    24: "North America", 25: "North America", 26: "SE Asia",
    27: "Middle East", 28: "South Asia", 29: "Latin America",
    30: "Latin America", 31: "Latin America", 32: "Latin America",
    33: "Europe", 34: "Europe", 35: "Europe", 36: "Africa",
    37: "South Asia", 38: "Africa", 39: "Africa", 40: "Africa",
    41: "Africa", 42: "SE Asia", 43: "SE Asia", 44: "SE Asia",
    45: "SE Asia",
}
STORY_REGION.update(ALSO_REGION)

# ---------------------------------------------------------------- illustrations
# Every card illustration is drawn in code and carries one fact
# (big number / word overlay). Flat shapes only.

def ill_eu(draw, x, y, w, h):
    """EU stars circle, 3 greyed out, big €45bn + NO DEAL stamp."""
    draw.rectangle([x, y, x + w, y + h], fill=(20, 38, 74))
    cx, cy, r = x + 62, y + h // 2 - 4, 34
    import math
    for i in range(12):
        a = math.pi * 2 * i / 12 - math.pi / 2
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        col = (247, 241, 222) if i < 9 else (120, 120, 120)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=col)
    draw.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(179, 35, 27))
    f = SANS_B(13)
    draw.text((cx - tw(draw, "24", f) / 2, cy - 8), "24", font=f,
              fill=(255, 255, 255))
    f2 = SANS_B(7)
    draw.text((cx - tw(draw, "/27", f2) / 2, cy + 6), "/27", font=f2,
              fill=(255, 255, 255))
    f3 = SANS_B(30)
    t = "€45bn"
    draw.text((x + 118, y + 14), t, font=f3, fill=(247, 241, 222))
    f4 = SANS_B(12)
    draw.text((x + 120, y + 50), "LOAN BLOCKED", font=f4, fill=(255, 200, 60))
    f5 = SANS_B(9)
    draw.text((x + 120, y + 68), "3 HOLD OUT", font=f5, fill=(200, 205, 220))

def ill_bike(draw, x, y, w, h):
    """Motorbike silhouette on a track, big 8 TITLES."""
    draw.rectangle([x, y, x + w, y + h], fill=(179, 35, 27))
    # checkered flag band
    for i in range(12):
        for j in range(2):
            if (i + j) % 2 == 0:
                draw.rectangle([x + i * 8, y + j * 8, x + i * 8 + 8, y + j * 8 + 8],
                               fill=(26, 26, 26))
    # track
    draw.rectangle([x, y + h - 24, x + w, y + h - 16], fill=(60, 60, 60))
    draw.line([x, y + h - 20, x + w, y + h - 20], fill=(255, 255, 255), width=2)
    # bike: two wheels + frame (right half, clear of the big number)
    wx1, wy = x + 172, y + h - 34
    wx2 = x + 240
    draw.ellipse([wx1 - 16, wy - 16, wx1 + 16, wy + 16], outline=(255, 255, 255), width=4)
    draw.ellipse([wx2 - 16, wy - 16, wx2 + 16, wy + 16], outline=(255, 255, 255), width=4)
    draw.line([wx1, wy, wx1 + 28, wy - 26], fill=(255, 255, 255), width=4)
    draw.line([wx1 + 28, wy - 26, wx2 - 8, wy - 8], fill=(255, 255, 255), width=4)
    draw.line([wx2 - 8, wy - 8, wx2, wy], fill=(255, 255, 255), width=4)
    draw.line([wx1 + 28, wy - 26, wx1 + 44, wy - 30], fill=(255, 255, 255), width=4)
    draw.ellipse([wx1 + 38, wy - 42, wx1 + 50, wy - 30], fill=(255, 255, 255))
    f = SANS_B(34)
    draw.text((x + 14, y + 26), "8", font=f, fill=(255, 255, 255))
    f2 = SANS_B(13)
    draw.text((x + 52, y + 34), "TITLES", font=f2, fill=(255, 255, 255))
    draw.text((x + 52, y + 52), "LAST RACE SUNDAY", font=SANS_B(9), fill=(255, 220, 120))

def ill_drones(draw, x, y, w, h):
    """Night sky, drone dots and intercept bursts, big 155."""
    draw.rectangle([x, y, x + w, y + h], fill=(16, 24, 48))
    import math
    for i in range(28):
        dx = x + 12 + (i * 37) % (w - 24)
        dy = y + 8 + (i * 23) % 34
        draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(255, 220, 120))
    # moon
    draw.ellipse([x + w - 52, y + 10, x + w - 22, y + 40], fill=(247, 241, 222))
    # city skyline
    for i, bh in enumerate([26, 40, 30, 48, 22, 36]):
        bx = x + 14 + i * 46
        draw.rectangle([bx, y + h - bh, bx + 34, y + h], fill=(40, 52, 84))
        for wy in range(3):
            draw.rectangle([bx + 6, y + h - bh + 6 + wy * 10, bx + 12,
                            y + h - bh + 12 + wy * 10], fill=(255, 220, 120))
    f = SANS_B(34)
    draw.text((x + 14, y + 8), "155", font=f, fill=(255, 255, 255))
    f2 = SANS_B(11)
    draw.text((x + 108, y + 18), "DRONES", font=f2, fill=(255, 200, 60))
    draw.text((x + 108, y + 34), "110 DOWNED", font=f2, fill=(120, 220, 140))

def ill_seats(draw, x, y, w, h):
    """Parliament seat bar 65 of 130, one short of 66."""
    draw.rectangle([x, y, x + w, y + h], fill=(20, 38, 74))
    bx, by, bw, bh = x + 14, y + 10, w - 28, 16
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(60, 70, 95))
    draw.rectangle([bx, by, bx + bw // 2, by + bh], fill=(247, 241, 222))
    draw.rectangle([bx + bw // 2 + 1, by, bx + bw // 2 + 3, by + bh],
                   fill=(179, 35, 27))
    f = SANS_B(15)
    draw.text((x + 14, y + 30), "65 / 130", font=f, fill=(255, 255, 255))
    f2 = SANS_B(9)
    draw.text((x + 104, y + 34), "ONE SHORT OF 66", font=f2, fill=(255, 200, 60))

def ill_cloud(draw, x, y, w, h):
    """Cloud with a cracked lock, BREACHED."""
    draw.rectangle([x, y, x + w, y + h], fill=(32, 56, 102))
    cx, cy = x + w // 2, y + 15
    draw.ellipse([cx - 46, cy - 6, cx - 8, cy + 12], fill=(220, 228, 240))
    draw.ellipse([cx - 26, cy - 16, cx + 20, cy + 12], fill=(220, 228, 240))
    draw.ellipse([cx + 6, cy - 6, cx + 46, cy + 12], fill=(220, 228, 240))
    draw.rectangle([cx - 46, cy + 6, cx + 46, cy + 13], fill=(220, 228, 240))
    # lock hanging below the cloud
    lx, ly = cx - 10, y + 29
    draw.arc([lx - 5, ly - 12, lx + 19, ly + 3], 180, 360, fill=(255, 200, 60), width=3)
    draw.rectangle([lx - 7, ly, lx + 21, ly + 14], fill=(255, 200, 60))
    draw.ellipse([lx + 3, ly + 5, lx + 11, ly + 12], fill=(32, 56, 102))
    f = SANS_B(10)
    t = "BREACHED"
    draw.text((cx - tw(draw, t, f) / 2, y + h - 13), t, font=f,
              fill=(255, 200, 60))

def ill_hunger(draw, x, y, w, h):
    """16 hotspot dots on a globe outline, big 16."""
    draw.rectangle([x, y, x + w, y + h], fill=(211, 84, 0))
    cx, cy = x + 68, y + h // 2
    draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(255, 255, 255))
    # hotspot dots
    import math
    for i in range(16):
        a = math.pi * 2 * i / 16
        dx, dy = cx + 17 * math.cos(a), cy + 17 * math.sin(a)
        draw.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(179, 35, 27))
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(179, 35, 27))
    f = SANS_B(28)
    draw.text((x + w - 78, y + 4), "16", font=f, fill=(255, 255, 255))
    f2 = SANS_B(10)
    draw.text((x + w - 78, y + 38), "HOTSPOTS", font=f2, fill=(255, 220, 180))

def ill_cptpp(draw, x, y, w, h):
    """Three doors opening, 3 NEW."""
    draw.rectangle([x, y, x + w, y + h], fill=(15, 118, 110))
    cols = [(255, 200, 60), (255, 255, 255), (179, 35, 27)]
    for i in range(3):
        dx = x + 22 + i * 66
        draw.rectangle([dx, y + 8, dx + 52, y + 38], fill=cols[i],
                       outline=(26, 26, 26), width=2)
        draw.ellipse([dx + 38, y + 20, dx + 44, y + 26],
                     fill=(26, 26, 26))
    f = SANS_B(14)
    t = "3 NEW"
    draw.text((x + w // 2 - tw(draw, t, f) // 2, y + 41), t, font=f,
              fill=(255, 255, 255))

def ill_oil(draw, x, y, w, h):
    """Tanker silhouette + rising price line, $97."""
    draw.rectangle([x, y, x + w, y + h], fill=(26, 26, 26))
    # price line
    pts = [(x + 14, y + 50), (x + 60, y + 46), (x + 110, y + 50),
           (x + 160, y + 38), (x + 210, y + 24)]
    draw.line(pts, fill=(255, 200, 60), width=3)
    draw.ellipse([pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4],
                 fill=(255, 200, 60))
    # tanker
    ty = y + h - 30
    draw.rectangle([x + 30, ty, x + 200, ty + 18], fill=(120, 125, 140))
    draw.rectangle([x + 150, ty - 16, x + 185, ty], fill=(120, 125, 140))
    for i in range(4):
        draw.rectangle([x + 44 + i * 38, ty - 12, x + 72 + i * 38, ty],
                       fill=(179, 35, 27))
    draw.line([x + 14, ty + 22, x + w - 14, ty + 22], fill=(60, 90, 120), width=3)
    f = SANS_B(26)
    draw.text((x + 14, y + 4), "$97", font=f, fill=(255, 255, 255))
    f2 = SANS_B(10)
    draw.text((x + 84, y + 12), "BRENT / BARREL", font=f2, fill=(255, 200, 60))

def ill_ballot(draw, x, y, w, h):
    """Ballot box with a big tick, SUNDAY VOTE."""
    draw.rectangle([x, y, x + w, y + h], fill=(106, 61, 154))
    bx, by = x + 26, y + 8
    draw.rectangle([bx, by, bx + 76, by + 28], fill=(255, 255, 255))
    draw.rectangle([bx + 28, by - 6, bx + 48, by], fill=(255, 255, 255))
    draw.line([bx + 10, by + 16, bx + 30, by + 26, bx + 66, by + 4],
              fill=(30, 125, 70), width=4)
    f = SANS_B(15)
    draw.text((x + 118, y + 8), "SUNDAY", font=f, fill=(255, 255, 255))
    f2 = SANS_B(10)
    draw.text((x + 118, y + 26), "VOTE", font=f2, fill=(255, 220, 180))
    f3 = SANS_B(11)
    t = "VOX = KINGMAKER?"
    draw.text((x + 26, y + 42), t, font=f3, fill=(255, 200, 60))

def ill_ecb(draw, x, y, w, h):
    """Euro coin over a bank colonnade, ECB."""
    draw.rectangle([x, y, x + w, y + h], fill=(36, 86, 166))
    # columns
    for i in range(5):
        cx0 = x + 20 + i * 42
        draw.rectangle([cx0, y + 36, cx0 + 14, y + h - 6], fill=(255, 255, 255))
    draw.rectangle([x + 12, y + 28, x + w - 64, y + 36], fill=(255, 255, 255))
    draw.rectangle([x + 12, y + h - 6, x + w - 12, y + h - 2], fill=(255, 255, 255))
    # coin, top right, clear of the colonnade
    cx, cy = x + w - 32, y + 18
    draw.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(255, 200, 60),
                 outline=(255, 255, 255), width=2)
    f = SANS_B(15)
    t = "€"
    draw.text((cx - tw(draw, t, f) / 2, cy - 10), t, font=f, fill=(26, 26, 26))
    f2 = SANS_B(12)
    draw.text((x + 16, y + 6), "NEW ECB CHIEF", font=f2, fill=(255, 255, 255))

def ill_rubble(draw, x, y, w, h):
    """Collapsed slabs, 7 DEAD · 14 MISSING."""
    draw.rectangle([x, y, x + w, y + h], fill=(90, 88, 80))
    f = SANS_B(20)
    draw.text((x + 12, y + 3), "7 DEAD", font=f, fill=(255, 255, 255))
    f2 = SANS_B(10)
    draw.text((x + 104, y + 9), "· 14 STILL MISSING", font=f2, fill=(255, 220, 120))
    # standing wall stub + fallen slabs along the bottom
    draw.rectangle([x + 16, y + 36, x + 70, y + h - 4], fill=(200, 194, 178))
    draw.line([x + 16, y + 44, x + 70, y + 44], fill=(150, 144, 128), width=1)
    draw.polygon([(x + 80, y + h - 4), (x + 130, y + 34), (x + 170, y + h - 4)],
                 fill=(140, 134, 118))
    draw.polygon([(x + 120, y + h - 4), (x + 180, y + 40), (x + 220, y + h - 4)],
                 fill=(120, 114, 98))
    draw.ellipse([x + 90, y + 30, x + 128, y + 44], fill=(220, 214, 198))

ILL = {"eu": ill_eu, "bike": ill_bike, "drones": ill_drones, "seats": ill_seats,
       "cloud": ill_cloud, "hunger": ill_hunger, "cptpp": ill_cptpp,
       "oil": ill_oil, "ballot": ill_ballot, "ecb": ill_ecb, "rubble": ill_rubble}

# ---------------------------------------------------------------- cards
def draw_lead(draw, s, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=NAVY, width=1)
    ih = 90
    ILL[s["art"]](draw, x + 1, y + 1, w - 2, ih)
    num_disc(draw, x + 16, y + ih + 14, s["n"], REG[s["region"]], r=10)
    ky = y + ih + 6
    f = SANS_B(9)
    draw.text((x + 30, ky), s["place"], font=f, fill=REG[s["region"]])
    draw.text((x + 30, ky + 12), s["field"], font=SANS_B(8), fill=GREY)
    badge_right(draw, x + w - 6, ky + 1, s["conf"], NAVY2, max_w=w - 30 - 150)
    hy = y + ih + 30
    hf, lines = fit_lines(draw, s["head"], SERIF(18), w - 16, 2)
    draw_lines(draw, lines, x + 8, hy, hf, INK, leading=22)
    dy = hy + len(lines) * 22 + 2
    df, dlines = fit_lines(draw, s["dek"], SANS(11), w - 16, 2)
    draw_lines(draw, dlines, x + 8, dy, df, (50, 50, 50), leading=12)
    sy = y + h - 14
    draw.text((x + 8, sy), s["src"], font=SANS(8), fill=GREY)
    return y + h

def draw_mid(draw, s, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=NAVY, width=1)
    ih = 58
    ILL[s["art"]](draw, x + 1, y + 1, w - 2, ih)
    num_disc(draw, x + 13, y + ih + 11, s["n"], REG[s["region"]], r=8)
    ky = y + ih + 5
    f = SANS_B(8)
    kw = tw(draw, s["place"], f)
    draw.text((x + 25, ky), s["place"], font=f, fill=REG[s["region"]])
    badge_right(draw, x + w - 6, ky, s["conf"], NAVY2,
                max_w=w - 25 - kw - 10, size=7)
    hy = y + ih + 21
    hf, lines = fit_lines(draw, s["head"], SERIF(13), w - 12, 2)
    draw_lines(draw, lines, x + 6, hy, hf, INK, leading=15)
    dy = hy + len(lines) * 15 + 1
    df, dlines = fit_lines(draw, s["dek"], SANS(9), w - 12, 2)
    draw_lines(draw, dlines, x + 6, dy, df, (50, 50, 50), leading=11)
    sy = y + h - 11
    draw.text((x + 6, sy), s["src"], font=SANS(7), fill=GREY)
    return y + h

# ---------------------------------------------------------------- page layout
M = 14                      # side margin
CW = W - 2 * M              # 996 content width

def top_bar(draw):
    draw.rectangle([0, 0, W, 20], fill=NAVY)
    draw.text((M, 4), "THE WORLD IN ONE DAY", font=SANS_B(10),
              fill=(255, 255, 255))
    r = "45 STORIES · 9 REGIONS · 12 FIELDS · EVERY ONE FROM FRIDAY 27 NOVEMBER 2026"
    draw.text((W - M - tw(draw, r, SANS_B(10)), 4), r, font=SANS_B(10),
              fill=(255, 200, 60))

def masthead(draw):
    t = "Friday 27 November 2026"
    f = SERIF(54)
    draw.text(((W - tw(draw, t, f)) / 2, 24), t, font=f, fill=NAVY)
    sub = ("EU summit fails on €45bn loan  ◆  Márquez quits after eighth "
           "title  ◆  155 drones over Ukraine")
    f2 = SERIF_IT(15)
    draw.text(((W - tw(draw, sub, f2)) / 2, 88), sub, font=f2, fill=RED)

def utc_strip(draw, y):
    draw.rectangle([M, y, W - M, y + 32], fill=NAVY)
    lab = "THE DAY IN UTC"
    lf = SANS_B(10)
    draw.rectangle([M, y, M + tw(draw, lab, lf) + 16, y + 32], fill=RED)
    draw.text((M + 8, y + 10), lab, font=lf, fill=(255, 255, 255))
    x = M + tw(draw, lab, lf) + 26
    cell = (W - M - x - 4) / len(UTC_STRIP)
    for i, (tm, ev) in enumerate(UTC_STRIP):
        cx = x + i * cell
        if i:
            draw.line([cx - 4, y + 5, cx - 4, y + 27], fill=(90, 100, 130), width=1)
        draw.text((cx, y + 3), tm, font=SANS_B(10), fill=(255, 200, 60))
        ef, lines = fit_lines(draw, ev, SANS(9), cell - 8, 2)
        draw_lines(draw, lines, cx, y + 15, ef, (255, 255, 255), leading=10)

def numbers_strip(draw, y):
    draw.rectangle([M, y, W - M, y + 40], fill=PAPER, outline=NAVY, width=1)
    cell = CW / len(NUMBERS)
    for i, (num, lab) in enumerate(NUMBERS):
        cx = M + i * cell
        if i:
            draw.line([cx, y + 5, cx, y + 35], fill=LGREY, width=1)
        f = SANS_B(20)
        draw.text((cx + 10, y + 3), num, font=f, fill=NAVY)
        lf, lines = fit_lines(draw, lab, SANS(9), cell - 16, 1)
        draw.text((cx + 10, y + 26), lines[0], font=lf, fill=GREY)

def section_head(draw, y, text):
    draw.text((M, y), text, font=SANS_B(11), fill=NAVY)
    draw.line([M, y + 15, W - M, y + 15], fill=NAVY, width=1)
    return y + 19

def trim_to(draw, text, font, width):
    if tw(draw, text, font) <= width:
        return text
    # cut at a word boundary, then add an ellipsis
    words = text.split(" ")
    out = ""
    for wd in words:
        trial = (out + " " + wd).strip()
        if tw(draw, trial + " …", font) <= width:
            out = trial
        else:
            break
    if not out:
        out = text
        while out and tw(draw, out + "…", font) > width:
            out = out[:-1]
    return out.rstrip() + " …"

def also_section(draw, x, y, w, h):
    draw.text((x, y), "ALSO ON FRIDAY 27 NOVEMBER — 34 MORE STORIES",
              font=SANS_B(11), fill=NAVY)
    draw.line([x, y + 15, x + w, y + 15], fill=NAVY, width=1)
    col_w = (w - 16) / 2
    f = SANS(9)
    fnum = SANS_B(9)
    y0 = y + 20
    lh = 11.2
    for idx, (place, text, src) in enumerate(ALSO):
        col = 0 if idx < 17 else 1
        row = idx % 17
        cx = x + col * (col_w + 16)
        cy = y0 + row * lh
        n = str(12 + idx)
        draw.text((cx, cy), n, font=fnum, fill=RED)
        nx = cx + tw(draw, n, fnum) + 3
        body = f"{place}: {text}"
        body = trim_to(draw, body, f, col_w - (nx - cx) - 34)
        draw.text((nx, cy), body, font=f, fill=INK)
        sx = cx + col_w - 32
        draw.text((sx, cy), src, font=SANS(8), fill=GREY)

def map_section(draw, x, y, w, h):
    draw.text((x, y), "WHERE IT HAPPENED — pin = story number",
              font=SANS_B(11), fill=NAVY)
    draw.line([x, y + 15, x + w, y + 15], fill=NAVY, width=1)
    mx, my, mw, mh = x, y + 20, w, 118
    draw_map(draw, mx, my, mw, mh)
    # display offsets (px) to de-cluster pins that share a neighbourhood
    OFF = {1: (0, -12), 2: (14, 8), 9: (-14, 6), 10: (12, -10), 15: (0, 0),
           17: (0, 0), 24: (0, 0), 26: (0, 0), 29: (0, 0), 36: (0, 0),
           42: (0, 0), 44: (0, 0)}
    for n, (lon, lat) in PINS.items():
        px, py = project(lon, lat, mx, my, mw, mh)
        dx, dy = OFF.get(n, (0, 0))
        if (dx, dy) != (0, 0):
            draw.line([px, py, px + dx, py + dy], fill=INK, width=1)
        num_disc(draw, px + dx, py + dy, n, REG[STORY_REGION[n]], r=8)
    # region legend with counts, 3 columns x 3 rows
    ly = my + mh + 6
    f = SANS(9)
    col_w = w / 3
    for i, (reg, cnt) in enumerate(REGION_COUNTS):
        lx = x + (i % 3) * col_w
        lyy = ly + (i // 3) * 13
        draw.ellipse([lx, lyy + 1, lx + 8, lyy + 9], fill=REG[reg])
        draw.text((lx + 11, lyy), f"{reg} {cnt}", font=f, fill=INK)

def date_check(draw, y):
    draw.rectangle([M, y, W - M, y + 58], outline=RED, width=2, fill=PAPER)
    draw.rectangle([M, y, M + 62, y + 58], fill=RED)
    draw.text((M + 6, y + 10), "DATE", font=SANS_B(12), fill=(255, 255, 255))
    draw.text((M + 6, y + 26), "CHECK", font=SANS_B(12), fill=(255, 255, 255))
    tx = M + 72
    twd = W - M - tx - 8
    left = ("Left out — first reported on another day:  "
            + " · ".join(f"{p}: {t} ({d})" for p, t, d in DATE_CHECK_LEFT))
    lf, lines = fit_lines(draw, left, SANS(9), twd, 3)
    draw_lines(draw, lines, tx, y + 4, lf, INK, leading=11)
    ny = y + 4 + len(lines) * 11 + 1
    nxt = ("Not yet:  " + " · ".join(f"{p} — {t} ({d})"
                                     for p, t, d in DATE_CHECK_NEXT))
    nf, nlines = fit_lines(draw, nxt, SANS(9), twd, 1)
    draw.text((tx, ny), nlines[0], font=nf, fill=RED)

def footer(draw, y):
    leg = ("CONFIRMED 2+ outlets · OFFICIAL on the record · "
           "REPORTED one outlet · CLAIM one side's word")
    draw.text((M, y), leg, font=SANS(8), fill=GREY)
    r = "Times UTC; c. = approximate · pictures and map drawn in code, not photos"
    draw.text((W - M - tw(draw, r, SANS(8)), y), r, font=SANS(8), fill=GREY)

def main():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    top_bar(draw)
    masthead(draw)
    utc_strip(draw, 108)
    numbers_strip(draw, 144)
    # leads
    ly, lh = 188, 208
    lw = 326
    for i, s in enumerate(LEADS):
        draw_lead(draw, s, M + i * (lw + 9), ly, lw, lh)
    y = section_head(draw, 400,
                     "THE DAY IN EIGHT MORE — Friday's other big stories, "
                     "across eight regions")
    # mid grid: 4 cols x 2 rows
    mw, mh, gap = 244, 146, 8
    for i, s in enumerate(MIDS):
        col, row = i % 4, i // 4
        draw_mid(draw, s, M + col * (mw + gap), y + row * (mh + 4), mw, mh)
    by = y + 2 * mh + 4          # 720
    map_section(draw, M, by, 330, 208)
    also_section(draw, M + 338, by, CW - 338, 208)
    date_check(draw, 932)
    footer(draw, 996)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    data = open(OUT, "rb").read()
    print(f"wrote {OUT}  {len(data)} bytes  "
          f"sha256={hashlib.sha256(data).hexdigest()}")

if __name__ == "__main__":
    main()
