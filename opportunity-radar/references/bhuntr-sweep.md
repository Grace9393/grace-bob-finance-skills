# Sweeping 獎金獵人 (bhuntr.com) — field notes

Everything here was learned the hard way on 2026-08-04. Following it turns a
30-minute dead end into a 10-minute complete sweep.

## The site will not yield to WebFetch

bhuntr is a JS-rendered SPA. `WebFetch` returns only `找比賽 - 獎金獵人` — the
`<title>` — and nothing else, for both listing and detail pages. It looks like an
empty page rather than a failure, which is exactly how you end up reporting
"nothing found" when there are 400+ live competitions.

**Use a real browser tool** (`mcp__Claude_Browser__preview_start` with the URL, then
`navigate` / `get_page_text` / `read_page`). Nothing else works.

## The default listing is a trap

The landing list is sorted by 綜合 (general popularity) and is dominated by art,
photography, illustration, and creative-writing contests. A technology or business
sweep that reads only this list will miss almost everything relevant.

**Go straight to the category you need.** Filters are plain URLs:

| Category | URL fragment |
|---|---|
| 設計 Design | `?category=107,108,109,110` |
| 影像 Video | `?category=111,112` |
| 寫作 Writing | `?category=114,115` |
| **商業 Business (企劃／創業／程式競賽)** | **`?category=116,117,118`** |
| 音樂 Music | `?category=119,120,121` |
| 其他 Other | `?category=123,125,143` |
| 國際 International | `?location=international` |

For hackathons, AI, data, startup and government-innovation competitions, **`116,117,118`
is the only category that matters.** It held 92 open Taiwan entries when the general
list surfaced perhaps three of them.

`?location=international` returns a large count (157) but is overwhelmingly art and
photography — treat it as low yield and skim it, do not budget time for it.

## Pagination

`https://bhuntr.com/tw/competitions?page=2` **on its own silently redirects to the
home page.** You get page 1 content and no error. Combine it with a category:

```
https://bhuntr.com/tw/competitions?category=116,117,118&page=2
https://bhuntr.com/tw/competitions?category=116,117,118&page=3
```

Pages overlap — page 3 largely repeats page 2's tail. Two pages usually exhaust a
category. Confirm with JS rather than guessing:

```js
JSON.stringify({url: location.href,
                cards: document.querySelectorAll('a[href^="/tw/competitions/"]').length})
```

Two anchors are emitted per card, so `cards / 2` is the visible entry count.

Scrolling does **not** reliably load more; the cookie banner is pinned to the
bottom and interferes with the infinite-scroll trigger. Use the page parameter.

## Do not click the cookie banner

The banner offers only 「確定」 (accept) — no decline. Accepting a consent banner is
an action that needs the user's permission, and you do not need it: **every filter
and page is reachable by URL.** Navigate, don't click.

## Listing pages give relative dates; detail pages give exact ones

The listing shows only `投稿中：還有 27 天` or `還有 大約 2 個月`. The detail page
(`/tw/competitions/<slug>`) carries the real thing:

```
時間走期  投稿中
徵件期間  2026-07-14 15:00 至 2026-08-31 17:00
```

**Open the detail page for anything you intend to act on.** Convert a relative
countdown to a date only as a stopgap, and label it as an estimate.

## The eligibility gate is the whole ball game

Detail pages carry a 參加資格 block:

```
身分限制      不限                       <- anyone may enter
國籍/地區限制  不限
```

versus

```
身分限制      高中 高職 大學 五專 二專 二技 四技 碩士 …   <- students only
國籍/地區限制  除中、港、澳
```

A great many Taiwanese competitions are **students-only**, which disqualifies a
company or a working professional outright. Checking this *before* drafting an
entry is the single highest-value step in the sweep. Record it verbatim in the
eligibility column; when a competition is student-only, note the alternative route
in (mentor, judge, sponsor, challenge-setter) instead of dropping it.

## Detail-page sidebars leak other competitions' exact deadlines

Every detail page carries 「大家都在看」 and 「小酒館也推薦」 blocks listing other
competitions **with exact timestamps**:

```
2026 中華電信【智慧創新應用大賽】   2026-09-18 12:00
臺北市政府青年局 2026公共政策創意提案競賽   250,000 TWD   2026-10-16 23:59
楓之谷全球開發競賽   1,260,000 USD   2026-10-07 10:00
```

Two or three detail-page visits will hand you exact dates for a dozen competitions
you would otherwise have to open individually. Harvest these deliberately.

## Prize figures can disagree with the press

bhuntr showed OSSInt 2026 at NT$420,000 while the organiser's press release said
NT$500,000 total. Neither is necessarily wrong — listings often quote only the cash
pool. Cite the organiser's own figure and note the discrepancy rather than picking
one silently.

## Precision policy

Carry into the tracker only what the source actually stated:

| Source said | `deadline` field | Text field |
|---|---|---|
| `2026-08-31 17:00` | `2026-08-31` | `徵件 7/14–8/31 17:00` |
| `還有 27 天` | computed date | `約 8/31 截止（bhuntr 顯示剩 27 天）` |
| `大約 2 個月` | *(empty)* | `約 2 個月後截止（需查官網）` |
| page unreadable | *(empty)* | `截止日需向官網確認` |

Never upgrade "about two months" into a date. An invented deadline is worse than an
admitted gap, because nobody re-checks a cell that looks precise.

## Other aggregators worth a pass

- **Devpost** — the international online default; renders enough for `WebFetch`.
  Check `Rules` for country eligibility and whether submissions are actually open
  ("submissions open soon" is common and means not yet).
- **hackathon.com/country/taiwan/<year>** — thin, but occasionally unique.
- University 育成中心 and 高教深耕 pages republish competitions with the
  registration windows spelled out; they often surface in search when the
  organiser's own JS-rendered site does not.
