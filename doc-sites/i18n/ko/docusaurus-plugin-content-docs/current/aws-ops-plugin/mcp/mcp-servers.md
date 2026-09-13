---
sidebar_position: 1
title: "MCP 연동"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="mcp-서버" />
<span id="개요" />
<span id="서버-상세" />
<span id="awsdocs-번들" />
<span id="awsapi-번들" />
<span id="awsknowledge-deploy-on-aws" />
<span id="awspricing-deploy-on-aws" />
<span id="awsiac-deploy-on-aws" />
<span id="에이전트별-mcp-사용" />
<span id="트러블슈팅" />
<span id="uvx-명령을-찾을-수-없음" />
<span id="mcp-서버-타임아웃" />
<span id="aws-자격-증명-오류" />
<span id="로그-레벨-조정" />


# MCP 연동

AWS 운영 플러그인은 Claude 매니페스트에 AWS 문서용 `awsdocs`와 AWS API 작업용 `awsapi`, 두 MCP 서버를 선언합니다. Codex는 자체 매니페스트가 참조하는 생성된 MCP 설정을 사용합니다. 외부 `deploy-on-aws` 플러그인과 함께 두 플러그인을 불러와 설정하면 선택적 `awsknowledge`, `awspricing`, `awsiac` 연동을 사용할 수 있습니다. 특히 `awspricing`은 비용 워크플로에 요금 데이터를 제공합니다. 이 서버들은 여기 포함되어 있지 않습니다.

## 설정 {#setup}

선언된 서버는 `uvx`로 실행합니다. 해당 실행 파일과 각 서버에 필요한 인증·설정을 준비합니다. 별도로 관리되는 서버 목록을 복사하지 말고 실제 매니페스트에서 패키지 이름, 인수, 환경 설정, 시간 제한을 확인합니다.

[Claude 서버 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/.claude-plugin/plugin.json) · [Codex 패키지 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/.codex-plugin/plugin.json)

## 연결 실패 진단 {#diagnose-connection-failures}

프로세스가 시작되는지 확인하고 로컬 로그, 선택한 계정·리전, 자격 증명 만료를 점검합니다. MCP 전송 실패와 서비스 권한 실패를 구분합니다. 문서 검색에는 정상 작동하는 서버가 필요하지만 검색 성공이 AWS API 권한을 입증하지는 않습니다.

AWS API MCP 패키지는 업스트림의 기존 연동입니다. 업스트림 마이그레이션 가이드를 참고해 AWS MCP 전환을 별도로 검토합니다. 이 문서 변경이 설정된 서버를 대체하지는 않습니다.

[AWS API MCP 마이그레이션 가이드](https://github.com/awslabs/mcp/blob/main/src/aws-api-mcp-server/MIGRATION.md)
