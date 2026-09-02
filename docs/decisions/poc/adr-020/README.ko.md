# ADR-020 PoC — Archify + 공식 AWS 아이콘 + 슬라이드 임베드

`../../ADR-020-archify-interactive-diagrams.md`의 PoC 게이트 2건에 대한 증거.
처음부터 끝까지 재현하는 방법 (리포 변경 불필요):

```bash
git clone --depth 1 https://github.com/tt-a1i/archify /tmp/archify
cd /tmp/archify/archify

# 1. AWS 스펙 검증 + 렌더 (검증기가 라벨 겹침을 구체적인 labelDy 수정값과 함께
#    보고하므로, 제안된 값을 적용하면 됨).
node bin/archify.mjs validate architecture <this-dir>/aws-eks-web.architecture.json
node bin/archify.mjs render   architecture <this-dir>/aws-eks-web.architecture.json /tmp/poc-aws.html

# 2. icon-map.json에 명시된 공식 아이콘을 번들 아이콘 세트에서 추출
#    (plugins/aws-content-plugin/skills/reactive-presentation/assets/aws-icons.zip,
#    Architecture-Service-Icons */64/*.svg) → 디렉터리에 저장.

# 3. 공식 아이콘 주입 (Archify는 수정하지 않음) 후 재검사:
python3 <this-dir>/inject_aws_icons.py /tmp/poc-aws.html <this-dir>/icon-map.json <icons-dir> <this-dir>/poc-aws-icons.html
node bin/archify.mjs check <this-dir>/poc-aws-icons.html   # 수정된 아티팩트에서도 여전히 통과

# 4. 슬라이드 임베드: poc-slide.html이 1920x1080에서 다이어그램을 iframe으로 포함.
```

## 게이트 결과 (2026-09-01)

**Gate A — 의존(depend), 포크하지 않음.** Archify의 네이티브 `brand` 필드로는 AWS
아이콘을 넣을 수 없다: 내장 카탈로그(107개 마크, Simple Icons 기반)에 AWS 항목이
0개이고(Simple Icons가 AWS/Amazon 마크를 제거함), 스키마의 유일한 다른 형태는
다이제스트 고정 네트워크 캡처(`{url, sha256}`)로 — 로컬 벡터 형태가 없다. 대신
렌더 후 주입(post-render injection)이 동작하는데, 출력물이 안정적인 훅을 갖기
때문이다: 모든 노드 그룹은 `<g id="node-<id>" data-node-id=...>`이고 그 `<rect>`는
스펙 자체의 좌표를 그대로 사용한다. 시행착오로 확인한 주입 계약 (둘 다 필수):

- 아이콘은 **노드 rect들 뒤에** 삽입 — SVG는 문서 순서로 페인트되므로, 첫 자식으로
  넣은 아이콘은 불투명한 노드 몸체에 덮인다;
- 위치는 중첩 `<svg x= y=>`가 아니라 `<g transform="translate() scale()">`으로 지정
  — 뷰어의 스타일시트가 중첩 svg 지오메트리는 오버라이드할 수 있지만 transform
  속성은 건드릴 수 없다;
- 아이콘 내부 id(그라디언트)는 노드별로 네임스페이스 처리.

이 방식은 출력 마크업 형태에 결합되므로, 의존성은 **버전 고정**이 필수이고 Archify
업그레이드 시 크게 실패하도록 구조 프로브(`id="node-"`와 스펙 좌표 rect 존재 검증)로
지켜야 한다.

**Gate B — iframe 임베드 동작.** 다이어그램을 1920×1080 슬라이드에 iframe으로 넣은
상태(`poc-slide.html`)에서: 로드 시 포커스는 부모 문서에 유지되고
(`document.activeElement === BODY`), ArrowRight 2회가 부모의 키 핸들러에 도달하며
(발표자가 다이어그램을 클릭하기 전까지 Remarp 네비게이션에 영향 없음), 아티팩트는
~716 KB 자립형이고, headless Playwright로 깨끗하게 캡처된다(증거 PNG는 위 재현 절차로 재생성 — 커밋하지 않음) —
`export_pptx.py`가 쓰는 것과 같은 캡처 경로다.

아직 검증하지 않은 것 (구현 단계 항목이지 게이트 차단 요소는 아님): 실제
`:::archify` 블록을 포함해 `remarp_to_slides.py`로 빌드한 완전한 덱, `export_pptx.py`
전 구간 실행, 다이어그램 클릭 후 Escape로 포커스 복귀.
