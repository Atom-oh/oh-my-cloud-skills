# Event Operations Guide (이벤트 운영 잡학 가이드)

콘텐츠 저자/운영자가 알아야 할 이벤트 운영 관련 기능들 — 참가자 서베이, 콘텐츠 파일 구조 규칙, 자동 시작, 사기 방지, Opportunity ID 요구사항, 빌드 히스토리 배경까지.

---

## Participant Survey (참가자 피드백 서베이)

이벤트가 프로비저닝되면 Workshop Studio가 **별도 설정 없이 자동으로** 표준 피드백 서베이를 생성한다. 이벤트 시작 시 활성화되고, 종료 7일 후 비활성화된다(결과 조회는 이후에도 계속 가능).

- 운영자: 이벤트 상세 헤더의 "Participant survey" 드롭다운에서 서베이 링크 확인/공유, 응답 리포트 실시간 조회(개별 응답, 집계 점수, 내보내기)
- 참가자: 이벤트 포털 사이드바의 "Share feedback" 링크로 접근 (이벤트 시작 후 노출, 별도 로그인 불필요)
- 서베이 권한은 이벤트 Administrator/Support Staff 권한과 자동 동기화된다
- **Grant의 `Disable Participant Survey` 제약이 걸린 이벤트는 서베이가 생성되지 않는다** — re:Invent 등 대형 행사에서 피드백을 별도 중앙 프로세스로 수집하는 경우

---

## Page Organization (콘텐츠 파일 구조 규칙)

모든 콘텐츠는 `/content` 루트 하위에 위치하며, 파일명 규칙은 `<name>.<localeCode>.md`다.

- **Index 파일**: 파일명이 `index`인 파일은 해당 폴더의 루트 경로에 로드된다. **모든 콘텐츠 하위 폴더는 반드시 index 파일을 가져야 한다.**
- **Named 파일**: `index`가 아닌 이름의 파일은 하위 페이지가 없는 독립 페이지를 만든다 (예: `welcome.en.md` → `/welcome`).
- **⚠️ Index/Named 이름 충돌은 빌드 실패를 유발한다** — `introduction/index.en.md` 폴더와 `introduction.en.md` 파일이 동시에 존재하면 둘 다 `/introduction` 경로를 만들려 하므로 충돌한다. 폴더명이나 파일명 중 하나를 바꿔야 한다.
- **경로 슬러그화**: 폴더/파일명에 대소문자·공백이 있어도 URL 경로는 자동으로 소문자+대시(`-`) 형태로 정규화된다 (예: `Lab modules/module 1.en.md` → `/lab-modules/module-1`).
- **네비게이션 유형**: Named 파일 또는 index만 있는 폴더 → Page Link(단순 링크)로 렌더링. 하위에 다른 named 파일이나 폴더가 더 있는 폴더 → Expandable Link(펼침 메뉴, 클릭 시 해당 index로 이동)로 렌더링.
- 정적 파일은 `/content`와 나란히 `/static` 폴더에 둔다 (`/static/img/aws-logo.png` → 콘텐츠에서 `/static/img/aws-logo.png`로 참조).

---

## Autostart (자동 시작)

기본 동작은 **운영자가 수동으로 이벤트를 시작**하는 것이다. `Autostart`를 활성화하면 예정된 시작 시각에 자동으로 시작된다.

| 상황 | Grant 없음 | Grant 있음 |
|------|-----------|-----------|
| Autostart 활성화 | 예정 시작 시각에 자동 시작 | 예정 시작 시각에 자동 시작 |
| Autostart 비활성화 | 프로비저닝 시작 후 **48시간** 뒤 자동 시작 | Grant의 provision lead time 허용치 + 48시간 뒤 자동 시작 |

- **프로비저닝 자체는 Autostart의 영향을 받지 않는다** — 프로비저닝은 항상 운영자가 수동으로 트리거해야 한다.
- 이벤트 생성 시 또는 생성 후 "Update Schedule"에서 언제든 토글 가능하다.
- Grant가 Autostart를 강제하도록 설정되어 있으면, 그 Grant로 만든 이벤트는 비활성화할 수 없다.

---

## Fraud Prevention (사기 방지)

Workshop Studio는 이벤트에 연관된 3종 계정(중앙 계정/팀 계정/인프라 계정)의 악성 활동을 자동 모니터링한다. 고위험 징후가 감지되면:

- **팀 계정**이 플래그되면 → 해당 팀이 자동 종료되고, 그 팀의 모든 참가자가 이벤트에서 **차단(ban)**된다 (운영자가 명시적으로 해제하지 않으면 재입장 불가)
- **중앙/인프라 계정**이 플래그되면 → 계정 접근이 즉시 차단된다 (이벤트 범위 내에서 운영자/참가자/팀 계정 애플리케이션 모두 접근 불가)
- 플래그되지 않은 나머지 계정은 정상적으로 계속 사용 가능
- 이벤트 상세 페이지에 사기 플래그 배너가 표시됨

**운영자 대응**: 이벤트/팀 조인 코드가 외부에 유출되지 않았는지 확인 → 종료된 팀 수를 확인해 이벤트 전체 종료가 필요한지 판단 → 중앙/인프라 계정이 종료된 경우, 이후 팀 추가(capacity 증설)가 해당 계정에 의존한다면 동작하지 않을 수 있음을 인지 → 남은 팀 계정도 비정상 활동(EC2 대량 생성, 대용량 아웃바운드 트래픽 등) 스팟 체크.

**예방 원칙**: least-privilege 참가자 IAM 정책, 참가자 허용목록(allowlist)을 프로덕션 이벤트에서 신중히 관리 — 특히 불특정 다수가 참여 가능한 공개 이벤트에서는 "Allow all" 허용목록을 쓰지 않는다.

---

## Opportunity/Campaign ID 요구사항

**퍼블릭 게시 콘텐츠 기반 프로덕션 이벤트**를 생성할 때는 유효한 Salesforce Opportunity/Campaign ID(15~18자 영숫자)가 필요하다. 테스트 이벤트와 내부 게시 콘텐츠 기반 이벤트는 면제된다.

- Opportunity가 없는 직군(직접/간접적으로 Opportunity 데이터 접근 권한이 없는 경우)이나, 퍼블릭 콘텐츠로 내부 이벤트를 운영하는 경우를 위한 **특수 목적 Opportunity ID**가 별도로 존재한다 (Workshop Studio 팀이 발급).
- 잘못된/만료된 ID를 쓰면 운영자와 매니저에게 알림이 가며, 이벤트 상세에서 언제든 값을 수정할 수 있다 (종료 후에도 수정 가능).
- **Grant로 생성한 이벤트는 Opportunity ID가 자동으로 채워진다** — 운영자가 직접 입력할 필요 없음.

---

## Embedded builds vs Hugo builds (배경)

Workshop Studio는 과거 **Hugo 기반 정적 사이트 빌드**를 사용했으나, 현재는 **embedded build**(마크다운+`manifest.json`을 웹 콘솔이 직접 렌더링하는 방식)로 전환되었다. 이 변경으로 빌드가 더 가볍고 빨라졌으며, AWS 웹사이트/문서와 동일한 룩앤필을 자동으로 갖게 되었다.

**Hugo 배경이 있는 저자가 흔히 겪는 함정**: Hugo shortcode(`{{% notice %}}` 등)와 embedded build의 directive 문법은 **서로 다른 시스템**이며 1:1로 대응하지 않는다 — 일부 Hugo shortcode는 대응하는 embedded directive가 없고, 반대도 마찬가지다. **이 저장소의 모든 워크숍 콘텐츠는 embedded build를 대상으로 하므로 Hugo shortcode는 절대 사용하지 않는다** — `workshop-agent.md`의 "CRITICAL: Correct Directive Syntax" 경고 및 `directives-complete.md` 참조. Front Matter 역시 embedded build에서는 YAML 형식이 항상 필수이다 (Hugo는 YAML/TOML/JSON을 선택적으로 허용했다).

---

## 체크리스트

- [ ] 콘텐츠 폴더 구조에서 index/named 파일명 충돌이 없는지 확인 (빌드 실패 원인)
- [ ] 대형 공개 행사가 아니면 참가자 허용목록을 신중히 설정 (사기 방지)
- [ ] 퍼블릭 콘텐츠로 프로덕션 이벤트를 만들 때 Opportunity ID 준비 여부 확인
- [ ] Hugo 출신 콘텐츠를 마이그레이션할 때는 shortcode를 그대로 옮기지 말고 반드시 embedded directive로 재작성
