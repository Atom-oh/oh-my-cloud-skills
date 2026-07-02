---
sidebar_position: 5
title: Storage Agent
---

# Storage Agent

AWS/EKS 스토리지 트러블슈팅 전문 에이전트입니다. EBS, EFS, FSx CSI 드라이버를 다룹니다.

## 기본 정보

| 항목 | 값 |
|------|-----|
| Tools | Read, Write, Glob, Grep, Bash, AskUserQuestion |

## 트리거 키워드

| 영어 | 한국어 |
|------|--------|
| "EBS CSI", "EFS CSI", "FSx", "PVC", "PersistentVolume", "mount error", "volume attach" | "스토리지 오류", "볼륨 마운트", "PVC 바인딩" |

## 핵심 기능

1. **EBS CSI Driver** - 볼륨 프로비저닝, 어태치먼트, 스냅샷, 암호화
2. **EFS CSI Driver** - 공유 파일시스템, Access Points, 마운트 타겟
3. **FSx CSI Driver** - FSx for Lustre, NetApp ONTAP 연동
4. **PVC 수명주기** - 바인딩, 리사이징, Reclaim Policies, StorageClass
5. **마운트 트러블슈팅** - 마운트 오류, 권한 이슈, AZ 불일치

## 진단 명령어

### PVC/PV 상태

```bash
# PVC 상태
kubectl get pvc -A
kubectl describe pvc <name> -n <namespace>

# PV 상태
kubectl get pv
kubectl describe pv <pv-name>

# StorageClass
kubectl get storageclass
kubectl describe storageclass <name>

# CSI 드라이버 상태
kubectl get csidrivers
kubectl get pods -n kube-system -l app=ebs-csi-controller
kubectl get pods -n kube-system -l app=efs-csi-controller
```

### EBS 트러블슈팅

```bash
# EBS CSI 드라이버 로그
kubectl logs -n kube-system -l app=ebs-csi-controller -c ebs-plugin --tail=30

# 볼륨 어태치먼트
aws ec2 describe-volumes --filters Name=tag:kubernetes.io/created-for/pvc/name,Values=<pvc-name>
aws ec2 describe-volume-status --volume-ids <vol-id>

# 노드 어태치먼트 확인
kubectl get volumeattachments
```

### EFS 트러블슈팅

```bash
# EFS 마운트 타겟
aws efs describe-mount-targets --file-system-id <fs-id>

# EFS CSI 드라이버 로그
kubectl logs -n kube-system -l app=efs-csi-controller -c efs-plugin --tail=30

# Security Group NFS 포트(2049) 확인
aws ec2 describe-security-groups --group-ids <sg-id> --query 'SecurityGroups[].IpPermissions[?FromPort==`2049`]'
```

## 의사결정 트리

```mermaid
flowchart TD
    START[스토리지 이슈] --> TYPE{이슈 유형?}

    TYPE -->|PVC Pending| PVC[PVC 이벤트 확인]
    TYPE -->|마운트 오류| MOUNT[파드 이벤트 확인]
    TYPE -->|성능| PERF[IOPS/처리량 확인]

    PVC --> PVC_SC{StorageClass OK?}
    PVC_SC -->|No| PVC_FIX_SC[StorageClass 생성/수정]
    PVC_SC -->|Yes| PVC_CSI{CSI Driver Running?}
    PVC_CSI -->|No| PVC_FIX_CSI[CSI 드라이버 설치/재시작]
    PVC_CSI -->|Yes| PVC_AZ{AZ 일치?}
    PVC_AZ -->|No| PVC_FIX_AZ[WaitForFirstConsumer 사용 또는 Multi-AZ]
    PVC_AZ -->|Yes| PVC_IAM[IRSA 권한 확인]

    MOUNT --> MOUNT_TYPE{스토리지 타입?}
    MOUNT_TYPE -->|EBS| MOUNT_EBS[볼륨 어태치먼트, 디바이스 확인]
    MOUNT_TYPE -->|EFS| MOUNT_EFS[마운트 타겟, SG 포트 2049 확인]
    MOUNT_TYPE -->|FSx| MOUNT_FSX[Lustre 클라이언트, SG 확인]

    PERF --> PERF_TYPE{스토리지 타입?}
    PERF_TYPE -->|EBS| PERF_EBS[볼륨 타입, IOPS, 처리량 확인]
    PERF_TYPE -->|EFS| PERF_EFS[처리량 모드, 버스트 크레딧 확인]
```

## 일반적인 오류와 해결책

| 오류 | 원인 | 해결책 |
|------|------|--------|
| PVC `Pending` (이벤트 없음) | StorageClass 누락 | CSI provisioner로 StorageClass 생성 |
| PVC `Pending` (provisioning failed) | CSI 드라이버 오류, IAM | CSI 로그 확인, IRSA 검증 |
| `FailedAttachVolume` | AZ 불일치, 볼륨 사용 중 | `WaitForFirstConsumer` 사용, 오래된 어태치먼트 확인 |
| `MountVolume.SetUp failed` | 파일시스템 손상, 권한 | fsck, securityContext 확인 |
| EFS 마운트 타임아웃 | SG에 포트 2049 누락 | 마운트 타겟 SG에 NFS inbound 규칙 추가 |
| `volume already attached` | 오래된 VolumeAttachment | 오래된 VolumeAttachment 삭제, 강제 detach |

## MCP 서버 연동

| MCP 서버 | 용도 |
|----------|------|
| `awsdocs` | EBS/EFS/FSx CSI 드라이버 문서, StorageClass 참조 |
| `awsapi` | `ec2:DescribeVolumes`, `efs:DescribeMountTargets`, `ec2:DescribeVolumeStatus` |
| `awsknowledge` | 스토리지 아키텍처 모범 사례 |

## 사용 예시

### PVC Pending 문제 해결

```
PVC가 Pending 상태에서 바인딩이 안 돼.
```

Storage Agent가 자동으로 호출되어 다음을 수행합니다:
1. PVC 이벤트 및 상태 확인
2. StorageClass 설정 검증
3. CSI 드라이버 상태 확인
4. AZ 일치 여부 검증
5. 문제 해결 단계 안내

### EFS 마운트 실패 진단

```
EFS 볼륨 마운트가 타임아웃 돼.
```

Storage Agent가 다음을 수행합니다:
1. EFS 마운트 타겟 상태 확인
2. Security Group NFS 포트 검증
3. 네트워크 연결성 테스트
4. 수정 방법 안내

## 출력 형식

```
## Storage Diagnosis
- **Storage Type**: [EBS / EFS / FSx]
- **Component**: [PVC / PV / CSI Driver / Mount]
- **Symptom**: [관찰된 현상]
- **Root Cause**: [파악된 원인]

## Resolution
1. [단계별 수정 방법]

## Verification
```bash
kubectl get pvc <name> -n <namespace>
kubectl describe pod <pod> -n <namespace> | grep -A5 "Volumes:"
```
```
