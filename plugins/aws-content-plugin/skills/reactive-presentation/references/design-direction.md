# Design Direction — 슬라이드 시각 디자인 원칙

> Anthropic **frontend-design** 스킬의 원칙을 reactive-presentation 프레임워크에 맞게 증류한
> 문서입니다. **Phase 2(Content Authoring) 시작 전과 Phase 8(Screenshot 검증) 자기비평 때** 읽으세요.
> 토큰/클래스 상세는 [colors-reference.md](colors-reference.md), 작성 규칙은 [authoring-rules.md](authoring-rules.md).

---

## 1. 핵심 원칙 (frontend-design 요약)

1. **주제에 뿌리내리기 (Ground it in the subject)** — 디자인 선택은 발표 주제의 세계에서
   나온다. AWS 기술 덱이면 AWS의 실제 디자인 재료(Cloudscape, Squid Ink `#232F3E`,
   Smile Orange, 콘솔 UI, 터미널/mono 타이포)가 출발점이다. 고객 브랜드 PPTX가 있으면
   **그 브랜드가 항상 우선**한다(Phase 1 추출 → `--pptx-*` 토큰이 테마 전체에 흐름).
2. **타이포그래피가 인격이다** — 디스플레이 서체(제목)와 본문 서체를 의도적으로 페어링하고,
   자간/굵기/스케일을 명확히. 제목은 콘텐츠 전달 수단이 아니라 기억에 남는 디자인 요소다.
3. **구조는 정보다** — 번호 마커(01/02/03), eyebrow, 구분선은 콘텐츠의 **진짜 구조**(순서가
   의미를 갖는 프로세스, 모듈 번호)를 인코딩할 때만 사용한다. 장식용 번호는 금지.
4. **모션은 절제된 오케스트레이션** — 흩어진 효과 여러 개보다 의도된 한 순간이 낫다.
   fragment는 "말하는 순서"를 인코딩할 때만. 과한 애니메이션은 오히려 AI 생성물처럼 보인다.
5. **대담함은 한 곳에만 (Signature element)** — 덱을 기억하게 만드는 요소는 하나로 충분하다.
   나머지는 조용하고 규율 있게. "집을 나서기 전 액세서리 하나를 빼라" (Chanel).

## 2. Anti-default 캘리브레이션 — 피해야 할 3가지 "AI 기본값 룩"

frontend-design 스킬이 지목하는, 주제와 무관하게 반복 등장하는 템플릿 룩:

| # | 룩 | 특징 |
|---|-----|------|
| 1 | 웜 크림 + 세리프 + 테라코타 | `#F4F1EA` 근처 배경, 고대비 세리프 제목, 테라코타 포인트 |
| 2 | 근흑 배경 + 형광 단색 포인트 | near-black + acid green/vermilion 하나 |
| 3 | 신문 조판 | hairline rule, border-radius 0, 조밀한 다단 |

> 이 프레임워크의 **구(舊) 라이트 기본값이 정확히 룩 #1**이었다. 현행 기본 테마는 이를
> AWS 주제 기반 아이덴티티(콘솔 그레이 캔버스 + Squid Ink 텍스트 + Smile Orange 액센트 +
> Cloudscape 블루 텍스트 액센트)로 교체했다. 브리프가 명시적으로 특정 룩을 요구하면 브리프가
> 이긴다 — 그 외에는 위 3개 룩으로 "자유 축을 낭비"하지 말 것.
> 구 웜 룩이 필요한 덱은 `theme.preset: paper`로 의도적으로 선택한다.

## 3. 덱별 디자인 플랜 (Phase 2 진입 전, 2-pass)

**Pass 1 — 플랜 작성** (플래닝 질문의 "Design refs" 답과 함께, 생각 안에서 간결하게):

- **Subject**: 주제·청중·이 덱의 단 하나의 목적을 한 문장으로.
- **Palette**: 4–6개의 named hex. 기본 테마 토큰을 쓰면 이 단계는 "기본 팔레트 채택 +
  액센트 유지/변경"만 선언. PPTX 추출 시 매니페스트 색이 팔레트다.
- **Type**: 역할 2+ (display / body / mono-utility). 기본값: Space Grotesk(라틴 디스플레이,
  한글은 Pretendard 폴백) / Pretendard / JetBrains Mono. 바꿀 이유가 주제에 있으면 명시.
- **Layout**: 대표 슬라이드 1–2장의 레이아웃 컨셉 한 문장씩.
- **Signature**: 이 덱이 기억될 단 하나의 요소. 프레임워크 기본 시그니처는
  **beam rule**(슬라이드 헤더 아래 액센트 그라디언트 헤어라인). 덱 고유 시그니처를
  추가하려면 `:::css`로 하나만 — 기본 시그니처와 경쟁시키지 말 것.

**Pass 2 — 자기비평**: 플랜이 "비슷한 브리프에 냈을 결과물과 같은가?"를 점검. 같다면 그
부분을 수정하고 무엇을 왜 바꿨는지 한 줄로 남긴다. 통과 후에만 Remarp 작성 시작.

## 4. 프레임워크 테마 시스템

| 선택 | frontmatter | 결과 |
|------|-------------|------|
| 기본 (라이트) | (없음) | 콘솔 그레이 캔버스 `#eaedee` + 화이트 카드 + Squid Ink 텍스트 + Smile Orange 액센트 |
| 다크 | `theme: { mode: dark }` | Squid-ink night (`#0f1b2a` 계열) + `#ff9900` 액센트 |
| 웜 페이퍼(구 기본) | `theme: { preset: paper }` | 웜 크림 + 테라코타 (의도적 선택일 때만) |
| 브랜드 PPTX | Phase 1 추출 | `--pptx-*`가 모든 프리셋보다 우선 |

- 슬라이드 단위 대비: `@theme: dark` 디렉티브로 커버/섹션 슬라이드만 다크 전환 가능.
  **주의**: 이 전환은 DOM/CSS 콘텐츠에 적용된다. `:::canvas` 다이어그램의 색상(`Colors`)과
  Mermaid 테마는 **덱 루트 테마 기준**으로 해석되므로, 덱 테마와 다른 `@theme` 슬라이드에
  canvas/mermaid를 두지 말 것 (커버/섹션 강조는 텍스트·CSS 슬라이드로). 런타임에 테마를
  바꾸는 커스텀 코드는 `refreshThemeColors()` 호출 후 `remarp:theme-colors` 이벤트를 받아
  canvas를 다시 그려야 한다.
- 모든 마크업은 역할 토큰(`var(--accent)` 등)만 사용 — hex 하드코딩 금지
  (colors-reference.md). 그래야 테마/브랜드 전환이 전체에 일괄 반영된다.

## 5. 타이포그래피 규칙

- `h1`/`h2` = `--font-display` + `--tracking-tight`. 한글 제목은 Pretendard로 폴백되므로
  안전하다. `h3` = `--text-accent`(라이트: Cloudscape 블루) — 액센트 오렌지와 역할 분리.
- **Eyebrow** (`.eyebrow`): mono·uppercase·`--tracking-wide`·액센트. 모듈 번호("MODULE 02"),
  섹션 카테고리("HANDS-ON") 등 **실제 구조**에만. 매 슬라이드 장식으로 반복하지 말 것.
- 그라디언트 텍스트는 템플릿 답안이다 — 사용하지 않는다(구 `.title-slide h1`에서 제거됨).

## 6. 절제 체크리스트 (Phase 8 스크린샷 자기비평 시)

- [ ] 시그니처 요소가 **하나**인가? (beam rule 외에 덱 고유 장식을 추가했다면 그것 하나만)
- [ ] 액센트 오렌지가 슬라이드당 1–2곳 이하인가? (진행바/활성 탭/마커/beam은 프레임워크 몫)
- [ ] 번호·eyebrow가 진짜 구조를 인코딩하는가?
- [ ] fragment 순서가 발화 순서와 일치하는가? 불필요한 fade가 없는가?
- [ ] 본문 대비 4.5:1 이상, 카드가 캔버스 위에서 분리되어 보이는가?
- [ ] 뺄 수 있는 액세서리가 하나 있는가? 있다면 뺀다.

## 7. 슬라이드 카피 (요약 — 상세는 authoring-rules.md §2·§3)

카피도 디자인 재료다: 능동태, 명령형 제목보다 주장형 제목(Title Voice), 시스템 구현이 아니라
청중이 인식하는 이름으로. 채우기용 문구·AI-tell 표현은 authoring-rules §2의 금지 목록을 따른다.
