# Workshop Assets Guide (에셋 관리 가이드)

마크다운 콘텐츠 외에 참가자에게 제공해야 하는 모든 파일("에셋")을 다루는 방법. 저장 위치에 따라 **Repository Assets**(`/static`)와 **S3 Assets**(`/assets`)로 나뉘며, 용도가 서로 다르다.

---

## Repository Assets vs S3 Assets — 무엇을 어디에 둘까

| | Repository Assets (`/static`) | S3 Assets (`/assets`) |
|---|---|---|
| 적합한 파일 | CloudFormation 템플릿, IAM 정책, 텍스트 기반 코드 (버전 관리 필요) | Lambda 배포 패키지(zip), 바이너리, 대량 이미지 등 텍스트가 아닌 파일 |
| 저장 위치 | 콘텐츠 git 리포지토리 | S3 스테이징 버킷 (콘텐츠별 고유 prefix) |
| 스캔 시점 | 커밋 푸시 → 빌드 시 | 업로드 시 |
| 마크다운에서 참조 | `:assetUrl` directive | `:assetUrl` directive |
| CloudFormation에서 참조 | **불가** (마크다운에서만 접근 가능) | Magic Variables (`{{.AssetsBucketName}}`/`{{.AssetsBucketPrefix}}`) |
| 고정 공개 URL(ASU) 생성 | **불가** | 가능 |
| 한도 | 파일 수 1000개, 파일당 1GB, 총합 3GB | 파일 수 500개, 파일당 1GB, 총합 3GB (Repository Assets와 별도 한도) |

핵심 판단 기준: **CloudFormation 템플릿이 그 파일에 접근해야 하면 반드시 S3 Assets**를 써야 한다 (Repository Assets는 마크다운 콘텐츠에서만 접근 가능, 인프라 프로비저닝 과정에서는 접근 불가).

### S3 Assets 업로드/동기화

Workshop Studio 콘솔의 Credentials 버튼에서 임시 자격 증명과 `aws s3 sync` 명령을 받아 사용한다.

```bash
# 로컬 → S3 (에셋 변경분 업로드)
aws s3 sync ./assets s3://<workshop-staging-bucket>/<prefix>/assets/

# S3 → 로컬 (기존 에셋 내려받기)
aws s3 sync s3://<workshop-staging-bucket>/<prefix>/assets/ ./assets
```

> ⚠️ **에셋 변경은 새 빌드를 트리거해야 반영된다.** `/assets`를 수정만 하고 콘텐츠 커밋/푸시를 하지 않으면 기존 빌드/게시된 결과물에는 반영되지 않는다 — 에셋을 먼저 동기화한 뒤 콘텐츠 커밋을 푸시하는 순서를 지킨다.

---

## Assets Scanning (자산 스캔)

모든 에셋은 참가자에게 노출되기 전 자동 스캔된다 — Repository Assets는 빌드 시, S3 Assets는 업로드 시.

**스캔 항목**: 멀웨어, 정적 코드 분석(보안 취약점) — 코드 스캔은 보호 대상 파일 형식(`.yaml`, `.yml`, `.json`, `.template`, `.py`, `.sh`, `.bash`)에만 적용되고, 그 외 파일(이미지/바이너리 등)은 멀웨어 스캔만 받는다.

| 스캔 결과 | 의미 | 빌드/게시 | ASU 생성/동기화 |
|-----------|------|-----------|------------------|
| `pass` | 이상 없음 | 허용 | 허용 |
| `code_findings` | 코드 취약점 발견 (멀웨어 없음) | 허용 (경고만) | 허용 |
| `malware_detected` | 멀웨어 발견 | 차단 | 차단 |
| `code_and_malware` | 둘 다 발견 | 차단 | 차단 |
| `fail` | 스캔 프로세스 자체 오류 (타임아웃 등, 콘텐츠 문제 아님) | 차단 | 차단 |

- **코드 취약점(code findings)은 non-blocking** — 빌드/게시/ASU 생성을 막지 않고 경고만 남는다.
- **멀웨어 발견 시**: Repository Assets는 빌드 실패, S3 Assets는 해당 파일이 스테이징 버킷에서 truncate(키는 유지, 내용 삭제)된다.
- **스캔 실패(fail)는 멀웨어 발견이 아니다** — 스캐너 자체 오류이므로 재시도(커밋 재푸시 또는 파일 재업로드)로 해결한다.

---

## Asset Static URLs (ASU) — S3 Assets 전용 고정 공개 URL

일반 에셋 URL(`:assetUrl` directive로 생성되는 서명 URL)은 **빌드/이벤트에 종속**되어 있어 빌드가 바뀌면 링크도 바뀐다. ASU는 **빌드와 독립적으로 고정된** S3/HTTPS URL을 제공하며, 아래와 같은 경우에만 사용한다:

- CloudFormation 파라미터로 얻을 수 없는 결정적(deterministic) URL이 스크립트 등에 필요한 경우
- 참가자가 자신의 환경에서 그대로 사용할 One-Click Launch Stack URL이 필요한 경우 (S3 스킴 URL 요구)
- 참가자 계정에 배포되는 CloudFormation 템플릿이 참조하는 Lambda 배포 패키지 등 결정적 URL이 필요한 경우

**주의사항**: ASU는 콘텐츠 빌드/게시 상태와 무관하게 라이프사이클이 독립적이고, 업데이트 시 **기존 URL을 즉시 덮어쓴다** — 진행 중이거나 예정된 이벤트에도 즉시 영향을 준다. 새 자산 버전을 스테이징 버킷에 올려도 ASU가 자동으로 갱신되지 않으며, 명시적으로 "Sync static URLs"를 눌러야 갱신된다 (버전 고정으로 인한 실수 방지). 삭제 시에는 진행 중인 이벤트에서 사용 중인지 반드시 확인한다. 지원 리전(17개 주요 상용 리전)에 자동 복제된다.

---

## Amazon EC2 SSH Keypair

참가자가 계정 내 리소스(EC2 등)에 SSH로 접근해야 할 때 Workshop Studio가 자동 생성해주는 키페어.

```yaml
awsAccountConfig:
  ec2KeyPair: true   # 기본값 false

infrastructure:
  cloudformationTemplates:
    - templateLocation: static/sample-stack.json
      label: Sample Stack
      parameters:
        - templateParameter: KeyPair
          defaultValue: "{{.EC2KeyPairName}}"
```

- 고정 이름 `ws-default-keypair`가 부여되지만, 하드코딩 대신 항상 `{{.EC2KeyPairName}}` Magic Variable로 참조한다.
- **배포 리전에서 생성된 뒤, 이벤트의 접근 가능 리전(accessibleRegions) 전체로 자동 임포트**된다 — 참가자는 어느 접근 가능 리전에서든 동일한 키페어를 쓸 수 있다.
- 참가자는 이벤트 대시보드의 "Get EC2 SSH key" 메뉴에서 프라이빗 키를 다운로드한다.

상세 contentspec 스키마: `references/contentspec-complete.md`

---

## 체크리스트

- [ ] CloudFormation이 접근해야 하는 파일 → S3 Assets (`/assets`), 아니면 Repository Assets (`/static`)
- [ ] 에셋 변경 후 반드시 콘텐츠 커밋/푸시로 새 빌드를 트리거
- [ ] 시크릿/자격증명은 Repository Assets에 커밋하지 않는다 (git 히스토리에 영구 저장됨)
- [ ] ASU는 정말 고정 URL이 필요한 경우에만 — 업데이트가 진행 중인 이벤트에 즉시 영향을 준다는 점을 인지
- [ ] EC2 키페어가 필요하면 `ec2KeyPair: true` + `{{.EC2KeyPairName}}` 매직 변수 사용, 이름 하드코딩 금지
