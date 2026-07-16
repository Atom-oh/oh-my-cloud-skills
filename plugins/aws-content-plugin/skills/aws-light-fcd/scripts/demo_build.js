const kit = require("./deck_kit.js");
const arch = require("./arch_kit.js");
const { FiZap, FiSearch, FiGitBranch, FiShield } = require("react-icons/fi");

(async () => {
  const pres = kit.newDeck();

  // 1) COVER
  kit.cover(pres, {
    product: "Amazon Bedrock",
    subtitle: "Agentic AI 애플리케이션을 프로토타입에서\n프로덕션 단계까지 이끌어주는 통합 플랫폼 서비스",
    date: "June 11, 2026",
    presenter: { name: "오준석", title: "Senior Solutions Architect", org: "AWS Korea" },
  });

  // 2) AGENDA (content chapters only)
  const agIcons = await Promise.all([FiZap, FiSearch, FiGitBranch, FiShield].map(ic => arch.renderIcon(ic, "#" + kit.C.blue)));
  kit.agenda(pres, {
    pageNum: 2,
    items: [
      { num: "01", title: "무엇이 새로워졌나", desc: "두 모델의 정식 출시와 오픈 웨이트의 의미", iconData: agIcons[0] },
      { num: "02", title: "두 모델 들여다보기", desc: "규모, 컨텍스트, 추론, 안전성", iconData: agIcons[1] },
      { num: "03", title: "시작하는 두 가지 경로", desc: "Amazon Bedrock과 SageMaker JumpStart", iconData: agIcons[2] },
      { num: "04", title: "프로덕션 고려사항", desc: "선택 기준, 보안, 리전, 비용", iconData: agIcons[3] },
    ],
  });

  // 2.5) SECTION DIVIDER
  kit.sectionDivider(pres, {
    pageNum: 3, num: "01", title: "무엇이 새로워졌나",
    kicker: "두 모델의 정식 출시와 오픈 웨이트의 의미",
  });

  // 3) BIG STAT
  kit.bigStat(pres, {
    pageNum: 4, title: "AI 에이전트, 이미 현실이 되었습니다", bg: "glow",
    stats: [
      { num: "80%", lines: [{ t: "의 고객 서비스 이슈를" }, { t: "에이전틱 AI가 자율적으로 해결", blue: true }, { t: "2029년까지 운영비용 30% 절감" }], source: "Gartner, CXToday 2026" },
      { num: "51%", lines: [{ t: "의 기업이 이미" }, { t: "AI 에이전트를 프로덕션에 배포", blue: true }, { t: "85%가 2026년 말까지 도입 계획" }], source: "Ringly.io; NVIDIA State of AI 2026" },
    ],
  });

  // 4) AGENTCORE 3-CARD
  kit.agentcoreCards(pres, {
    pageNum: 5, headerIcon: "agentcore", headerTitle: "Amazon Bedrock AgentCore",
    subtitle: "어떤 프레임워크와 모델로도 고성능 에이전트를 안전하게, 대규모로 구축·배포·운영",
    cards: [
      { title: "가치 실현 시간 단축", icon: "runtime", desc: "인프라와 운영 부담 없이\n강력한 AI 에이전트를 구축" },
      { title: "유연성", icon: "ai_agent", desc: "어떤 프레임워크나\n모델로도 에이전트 생성" },
      { title: "신뢰성", icon: "policy_engine", desc: "조직이 신뢰할 수 있는\n안전하고 확장 가능한 배포" },
    ],
  });

  // 5) ARCHITECTURE DIAGRAM — declarative archFlow (preferred): columns only, no
  // hand-placed coordinates. GPU/추론 엔진 stages use raw primitives via the returned
  // geometry, since a mid-flow fan-out (2 GPU boxes + a Ray/vLLM pair) doesn't fit the
  // single-item-per-slot column model — the documented escape hatch, not the default.
  const { s, cols } = arch.archFlow(kit, pres, {
    pageNum: 6, title: "자동 확장 기능을 갖춘 추론 아키텍처",
    columns: [
      { items: [{ icon: "model_registry", label: "모델 레지스트리", step: 3 }] },
      { label: "컨테이너 레지스트리", items: [{ icon: "ecr", label: "Amazon ECR", step: 2 }] },
      { label: "스토리지", items: [
        { icon: "efs", label: "Amazon EFS", step: 4 },
        { icon: "s3", label: "Amazon S3" },
        { icon: "fsx", label: "Amazon FSx", iconSz: 0.48 },
      ] },
      { items: [] },  // GPU/추론 엔진 fan-out drawn manually below via cols[3]'s geometry
      { label: "서빙", items: [
        { icon: "api_gateway", label: "API Gateway", step: 6 },
        { icon: "load_balancer", label: "Elastic Load\nBalancing", iconSz: 0.55 },
      ] },
      { items: [{ chip: "사용자" }, { chip: "에이전트" }, { chip: "프로그램" }] },
    ],
    arrows: [[1, 2], [2, 3], [3, 4], [4, 5]],
    legend: ["컴퓨팅 프로비저닝", "컨테이너 실행", "모델 다운로드", "GPU 메모리 로드", "GPU 자동 확장", "엔드포인트 노출", "상호작용", "모니터링"],
  });
  const gpuCol = cols[3];
  s.addText("GPU", { x: gpuCol.x, y: gpuCol.y - 0.15, w: gpuCol.w, h: 0.3, fontFace: kit.FONT, fontSize: 12, bold: true, color: kit.C.body, align: "center" });
  s.addImage({ path: kit.awsIcon("gpu"), x: gpuCol.x + gpuCol.w / 2 - 0.45, y: gpuCol.y + 0.25, w: 0.9, h: 0.9 });
  s.addImage({ path: kit.awsIcon("gpu"), x: gpuCol.x + gpuCol.w / 2 - 0.45, y: gpuCol.y + 1.6, w: 0.9, h: 0.9 });
  s.addText("• • •", { x: gpuCol.x + gpuCol.w / 2 - 0.45, y: gpuCol.y + 1.23, w: 0.9, h: 0.25, fontFace: kit.FONT, fontSize: 14, color: kit.C.muted, align: "center", valign: "middle" });
  arch.groupBox(kit, pres, s, gpuCol.x, gpuCol.y + 2.55, gpuCol.w, 1.5, "추론 엔진");
  s.addImage({ path: kit.toolIcon("ray"), x: gpuCol.x + 0.4, y: gpuCol.y + 3.15, w: 0.42, h: 0.42 });
  s.addText("Ray", { x: gpuCol.x + 0.85, y: gpuCol.y + 3.15, w: 0.7, h: 0.42, fontFace: kit.FONT, fontSize: 14, bold: true, color: kit.C.ink, align: "left", valign: "middle", margin: 0 });
  s.addImage({ path: kit.toolIcon("vllm"), x: gpuCol.x + 1.4, y: gpuCol.y + 3.27, w: 0.62, h: 0.2 });
  arch.stepMarker(kit, pres, s, gpuCol.x + gpuCol.w / 2 + 0.14, gpuCol.y + 0.15, 5);
  arch.groupBox(kit, pres, s, cols[4].x, cols[4].y + cols[4].h + 0.15, cols[4].w, 1.3, "모니터링");
  arch.svc(kit, pres, s, cols[4].x + cols[4].w / 2, cols[4].y + cols[4].h + 0.4, "cloudwatch", "CloudWatch", 0.5);
  arch.stepMarker(kit, pres, s, cols[5].items[0].cx - 0.9, cols[5].items[0].cy - 0.35, 7);
  arch.stepMarker(kit, pres, s, cols[4].x + cols[4].w / 2 + 0.14, cols[4].y + cols[4].h + 0.05, 8);

  // 6) TITLE + VISUAL  (EKS slide-21 style responsibility diagram)
  kit.titleWithVisual(pres, {
    pageNum: 7,
    title: "GPU 지원 EKS\n클러스터 생성 옵션 1",
    caption: "자체 관리형 애드온을 사용하는 EKS",
    draw: (pres, s2, r) => {
      const C = kit.C, FONT = kit.FONT;
      // Customer responsibility box (orange)
      const custH = 3.55;
      s2.addShape(pres.shapes.RECTANGLE, { x: r.x, y: r.y, w: r.w, h: custH, fill: { type: "none" }, line: { color: "ED8B00", width: 1.5 } });
      s2.addImage({ path: kit.awsIcon("eks"), x: r.x + 0.12, y: r.y + 0.12, w: 0.42, h: 0.42 });
      s2.addText("고객 책임", { x: r.x + 0.62, y: r.y + 0.12, w: 2.5, h: 0.42, fontFace: FONT, fontSize: 14, bold: true, color: "ED8B00", align: "left", valign: "middle", margin: 0 });
      // GPU chips
      const gpuY = r.y + 0.72, chipW = 0.85, chipGap = 0.55, chipsTotal = chipW * 3 + chipGap * 2, chipStart = r.x + (r.w - chipsTotal) / 2;
      for (let i = 0; i < 3; i++) s2.addImage({ path: kit.awsIcon("gpu"), x: chipStart + i * (chipW + chipGap), y: gpuY, w: chipW, h: chipW });
      // add-on cells
      const addY = gpuY + chipW + 0.25, addH = 1.55, addX = r.x + 0.35, addW = r.w - 0.7;
      s2.addShape(pres.shapes.RECTANGLE, { x: addX, y: addY, w: addW, h: addH, fill: { type: "none" }, line: { color: "ED8B00", width: 1.2, dashType: "dash" } });
      const cells = ["네트워킹", "모니터링", "보안", "스토리지"], cw = (addW - 0.6) / 2, chh = 0.52, cx0 = addX + 0.2, cy0 = addY + 0.18;
      cells.forEach((t, i) => {
        const col = i % 2, row = Math.floor(i / 2), x = cx0 + col * (cw + 0.2), y = cy0 + row * (chh + 0.18);
        s2.addShape(pres.shapes.RECTANGLE, { x, y, w: cw, h: chh, fill: { color: C.grayTint }, line: { color: C.hairline, width: 0.75 } });
        s2.addText(t, { x, y, w: cw, h: chh, fontFace: FONT, fontSize: 12, color: C.body, align: "center", valign: "middle" });
      });
      // managed control plane
      const ctrlY = r.y + custH + 0.18, ctrlH = 0.5;
      s2.addShape(pres.shapes.RECTANGLE, { x: r.x + 0.18, y: ctrlY, w: r.w - 0.36, h: ctrlH, fill: { type: "none" }, line: { color: C.blue, width: 1.2, dashType: "dash" } });
      s2.addText("관리형 제어 플레인", { x: r.x + 0.18, y: ctrlY, w: r.w - 0.36, h: ctrlH, fontFace: FONT, fontSize: 13, color: C.ink, align: "center", valign: "middle" });
      // AWS responsibility box
      const awsY = ctrlY + ctrlH + 0.12, awsH = 0.62;
      s2.addShape(pres.shapes.RECTANGLE, { x: r.x, y: awsY, w: r.w, h: awsH, fill: { color: C.blueTint }, line: { color: C.blue, width: 1.5 } });
      s2.addImage({ path: kit.awsIcon("aws_cloud"), x: r.x + 0.12, y: awsY + 0.11, w: 0.4, h: 0.4 });
      s2.addText("AWS 책임", { x: r.x + 0.62, y: awsY, w: 3, h: awsH, fontFace: FONT, fontSize: 14, bold: true, color: C.blue, align: "left", valign: "middle", margin: 0 });
    },
  });

  // 7) PIPELINE
  kit.pipeline(pres, {
    pageNum: 8, title: "Bedrock 시작, 세 단계",
    steps: [
      { n: 1, title: "모델 액세스 요청", desc: "콘솔 '모델 액세스'에서\n두 OpenAI 모델 액세스 요청" },
      { n: 2, title: "플레이그라운드 평가", desc: "Chat/Test에서 카테고리를\nOpenAI로 선택해 테스트" },
      { n: 3, title: "API로 연결", desc: "엔드포인트 구성 후\nBedrock API 키로 인증·연결" },
    ],
  });

  // 8) WHY / WHAT
  kit.whyWhat(pres, {
    pageNum: 9, title: "신규 콘솔, 왜 나왔고 무엇이 다른가",
    subtitle: "생성형 AI 모델 환경 변화에 맞춰, 표준 호환 API와 프로젝트 중심 워크플로 제공",
    why: [
      { dot: kit.C.magenta, t: "모델 생태계의 확장", d: "GPT·Claude·오픈웨이트 등\n멀티 프로바이더 시대" },
      { dot: kit.C.purple, t: "표준 API 호환 요구", d: "OpenAI·Anthropic SDK 앱을\n최소 변경으로 AWS에서 운영" },
      { dot: kit.C.blue, t: "운영·거버넌스 부담", d: "프로젝트별 사용량·비용·키를\n통합, 프로토→프로덕션 가속" },
    ],
    what: [
      { n: "01", t: "표준 호환 API", d: "OpenAI Responses·Chat\nCompletions, Anthropic Messages", diff: "base URL·키만 바꿔 기존 코드 재사용", dc: kit.C.magenta },
      { n: "02", t: "Project 기반 운영", d: "모델 할당·평가·사용량·키를\n프로젝트 단위로 통합", diff: "앱 라이프사이클 단일 워크플로", dc: kit.C.purple },
      { n: "03", t: "비교·실행 가속", d: "Model catalog 최대 3개 비교\nLive API docs 즉시 실행", diff: "변수 자동 입력 스니펫 복사·실행", dc: kit.C.blue },
    ],
  });

  // 9) CHART WITH CALLOUT
  kit.chartWithCallout(pres, {
    pageNum: 10, title: "추론 비용, 1년 만에 급감", subtitle: "동일 워크로드 기준 월간 추론 비용 추이 (상대값)",
    chartType: "bar", chartColors: [kit.C.gradBlue], maxVal: 110,
    series: [{ name: "추론 비용", labels: ["2025 Q1", "Q2", "Q3", "Q4", "2026 Q1"], values: [100, 78, 55, 38, 24] }],
    callout: { big: "76%", lines: [{ t: "5분기 만에 추론 비용 " }, { t: "76% 절감", blue: true }, { t: ". 같은 예산으로 더 많은 추론 처리." }] },
  });

  // 10) CHIP GRID (EKS-23 style)
  kit.chipGrid(pres, {
    pageNum: 11, title: "광범위하고 심층적인 가속 컴퓨팅 포트폴리오",
    leftLabel: "GPU 및 AWS ML 가속기",
    vendorBoxes: [
      { name: "NVIDIA", color: "76B900", items: "H200, H100, A100, L4, L40S, A10G, T4" },
      { name: "AWS", color: kit.C.blueBright, items: "Trainium 가속기 · Inferentia 가속기" },
    ],
    rows: [
      { label: "훈련", groups: [{ color: "76B900", chips: ["P4d", "P4de", "P5", "P5e", "P5en", "P6"] }, { color: "ED8B00", chips: ["Trn1", "Trn2", "Trn3"] }] },
      { label: "추론", panel: true, groups: [{ color: "76B900", chips: ["G4", "G5", "G6", "G6e"] }, { color: "ED8B00", gapBefore: 1.6, chips: ["Inf1", "Inf2"] }] },
    ],
  });

  // 11) CLOSING (always last)
  kit.closing(pres, { pageNum: 12 });

  await pres.writeFile({ fileName: "kit_demo.pptx" });
  console.log("written kit_demo.pptx");
})();
