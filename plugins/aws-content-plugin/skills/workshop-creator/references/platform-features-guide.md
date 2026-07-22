# Platform Features Guide (플랫폼 부가 기능)

`contentspec.yaml`/콘텐츠 작성과 직접 관련은 없지만, Workshop Studio 플랫폼이 제공하는 부가 기능들 — MCP Server, Atlas Agent, Content Quality Program(CQP).

---

## Workshop Studio MCP Server

Workshop Studio의 Content Catalog/Events API를 MCP(Model Context Protocol)로 노출하는 **읽기 전용** 공식 서버(`workshop-studio-mcp`)다. Kiro IDE/CLI, Claude Code, Cline 등 MCP 호환 클라이언트에서 워크숍/이벤트/빌드/참가자 정보를 직접 조회할 수 있다.

- 사용자 신원 조회(`whoami`), 콘텐츠 카탈로그(워크숍/빌드/권한/연결된 이벤트 목록, 리포지토리 자격증명), 이벤트(이벤트/팀/참가자/출력 조회, 팀 AWS 자격증명 발급, 콘솔 로그인 링크 생성, 퍼실리테이터 가이드 조회) 등 총 17개 도구를 제공한다.
- 서버 자체는 읽기 전용 API만 호출하지만, 일부 도구(`get_event_team_credentials` 등)는 팀 계정 접근용 임시 자격증명/링크를 반환하므로 그 자격증명으로는 쓰기 작업(예: 팀 계정에서 AWS API 호출)이 가능하다.
- Amazon 내부 인증 세션과 내부 배포 도구를 통해 설치한다 — 현재는 Amazon 내부 사용자 대상 기능이다.
- 기존 워크숍 저자가 자신의 워크숍 상태를 IDE에서 직접 조회/디버깅하고 싶을 때 유용하다.

## Workshop Studio Atlas Agent

Workshop Studio 콘솔에 내장된 **미리보기(preview) 단계** AI 대화형 어시스턴트. 현재 보고 있는 워크숍/이벤트 콘텍스트를 인식해 답변한다.

- 강점: Workshop Studio 공식 문서 + 커뮤니티 Q&A 기반 질의응답 (배포 실패 트러블슈팅, 모범 사례 등)
- 자신이 소유/권한을 가진 워크숍·이벤트에 대한 카탈로그/상태 조회 (퍼블릭 카탈로그 검색/추천은 불가)
- **쓰기 작업 불가** — 워크숍/이벤트를 생성·수정·삭제할 수 없음. 실시간 참가자 용량/권한 데이터도 접근 제한적 (콘솔에서 직접 확인 권장)
- 프리뷰 기능이라 모든 시나리오에서 완벽하게 동작하지 않을 수 있다.

## Content Quality Program (CQP)

게시된 Workshop Studio 콘텐츠의 품질 기준을 유지하고 우수 콘텐츠를 홍보하기 위한 프로그램 (과거 ImmersionDay·Content Champion 프로그램을 통합). TFC(Tech Field Community)가 콘텐츠를 검토·큐레이션하며, 향후 GenAI 기반 품질 스캐너 통합이 예정되어 있다.

> 이 플러그인의 `content-review-agent` 품질 게이트(Workshop은 Visual-Testing 면제 → 90점 스케일 PASS ≥77)는 CQP가 요구하는 "높은 품질 기준"과 방향이 같다 — CQP에 콘텐츠를 등록하기 전에 `content-review-agent` PASS를 먼저 통과시켜 두면 검토 과정에서 유리하다.

---

## 언제 참조하나

- 기존 워크숍의 빌드 상태/참가자 데이터를 IDE에서 바로 확인하고 싶다 → MCP Server
- 콘솔에서 문서 기반 질문에 빠른 답을 얻고 싶다 → Atlas Agent
- 콘텐츠를 공식 우수 콘텐츠로 홍보/등록하고 싶다 → CQP (소속 TFC와 협의)

---

## 체크리스트

- [ ] IDE에서 워크숍/이벤트 상태를 반복 조회해야 한다면 MCP Server 설치를 검토 (Amazon 내부 사용자 전용)
- [ ] Atlas Agent는 쓰기 작업이 불가함을 인지 — 생성/수정은 항상 콘솔 또는 API로
- [ ] 공식 우수 콘텐츠 등록을 원하면 콘텐츠 품질을 먼저 `content-review-agent`로 자체 검증한 뒤 TFC와 협의
