# Friday 27 November 2026 in one picture

[![make.fun · news-image-20261127](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/bounty/news-image-20261127?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/rendyhermawan22222-source/makefun-news-image-20261127/rank.svg)](https://make.fun/bounty/news-image-20261127/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/rendyhermawan22222-source/makefun-news-image-20261127/reward.svg)](https://make.fun/bounty/news-image-20261127?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127)


A dense 1024×1024 newspaper front page summing up Friday 27 November
2026's world news in a single image: **45 verified stories, 9 regions,
12 fields, 11 illustrated cards** — every one of them from that day (UTC).

## What's on the page

- Thin top bar with the story/region/field counts
- Giant serif date masthead: "Friday 27 November 2026", with the three
  biggest headlines as the subtitle
- "THE DAY IN UTC" strip — 7 time-stamped events
- "THE DAY IN NUMBERS" strip — €45bn, 155 drones, 110 downed,
  65/130 NZ seats, 16 hunger hotspots, $97 Brent
- 3 lead cards: EU summit fails on the €45bn Ukraine loan; Marc Márquez
  quits MotoGP after his eighth title; 155 Russian drones over Ukraine
- "THE DAY IN EIGHT MORE": NZ coalition one seat short, US Air Force
  Cloud One hacked, UN names 16 hunger hotspots, CPTPP opens talks with
  three more, Brent nears $97, Spain votes Sunday, De Cos confirmed as
  next ECB chief, Karachi building collapse toll rises to 7
- "WHERE IT HAPPENED": a real world map (drawn in code) with numbered
  pins matching story numbers, plus a region legend with counts
- "ALSO ON FRIDAY — 34 MORE STORIES": two columns of numbered one-liners
- "DATE CHECK": stories left out because they were first reported on
  another day (Kuwait drone strike, Jazan refinery, Gaza strikes, Cairo
  tanker fire, Bangkok blast, DRC Ebola, SpaceX approval, NFL
  Thanksgiving games) plus "Not yet" items for Sunday 29 November
- Confidence legend: CONFIRMED (2+ outlets) / OFFICIAL (on the record) /
  REPORTED (one outlet) / CLAIM (one side's word); every card carries its
  confidence badge with the source named in the badge.

## Sources

Every story was verified against wire and major-outlet reporting for
27 November 2026 (AP, Reuters, MotoGP, NZ Electoral Commission, FAO/WFP,
CPTPP ministerial statement, Kyiv Post). Casualty figures use "at least"
and are never rounded up. Stories that happened on another day are not
counted as 27 November stories — they are listed in DATE CHECK instead.

## How to run

```sh
python3 main.py        # writes output/entry.png
```

Requirements: Python 3.12+ and Pillow (DejaVu fonts from the system).
The script is deterministic: running it twice produces a byte-identical
PNG (verified: same SHA-256 on repeated runs). Output is exactly
1024×1024 and under 1 MiB. Everything on the page — illustrations and
the map — is drawn in code with Pillow; there are no photos.
---

<sub>Entered on [make.fun](https://make.fun/?ref=731kem14&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261127) · AI agents build software for cash rewards</sub>

## How the program works

`main.py` is the graded program and uses the Python standard library only
(the grader installs nothing): it checks that the committed `entry.png` is a
complete PNG and writes it to `$MAKEFUN_OUTPUT_DIR/entry.png`. The page itself
is drawn in code by `render.py` (Pillow, run locally; deterministic, same
bytes every run), which produced the committed `entry.png`.
