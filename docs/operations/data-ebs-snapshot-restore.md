# Data EBS 스냅샷 복원

이 문서는 Data EBS 스냅샷으로 SQLite 데이터를 되돌리는 절차를 기록한다. 어떤 경우에 어떤 방법을 쓰는지와 복구 규칙은 [Data EBS 백업·복구 전략](../data-ebs-backup-and-recovery.md)을 따른다.

## 전제

- 복구 규칙에 따라 03:00 전에는 EC2를 stop한다. 그날 03:00 DLM 스냅샷이 stop 상태에서 찍히게 하기 위해서다.
- 로컬에서 `infra/`와 `infra/data-ebs/`의 Terraform을 실행할 수 있다.
- EC2에는 `sqlite3`가 없다. DB는 backend 이미지(Python 3.12)의 `sqlite3` 모듈로 연다. SQL은 대화형 셸에 입력하지 말고, 명령 한 번으로 실행한다. 대화형 셸에서 한글 입력기 상태로 입력하다가 깨진 바이트가 섞여 셸이 종료된 적이 있다.

명령의 실행 위치는 각 단계 제목에 `[로컬]`, `[EC2]`로 표시한다.

## 볼륨 전체 교체

스냅샷으로 새 볼륨을 만들고 Data EBS를 통째로 교체한다. 기존 볼륨은 지우지 않고, 새 볼륨이 정상일 때까지 되돌릴 수단으로 남긴다.

```text
EC2 stop → 새 볼륨 생성 → data-ebs state 교체 → infra apply로 연결 교체
→ EC2 start → mount·DB 검사 → 앱 기동
```

### 0. 준비 [로컬]

사용할 스냅샷과 기존 볼륨 ID를 적어 둔다. 새 볼륨은 EC2와 같은 AZ에 만들어야 연결할 수 있다.

```bash
cd infra
export AWS_DEFAULT_REGION=ap-northeast-2
NEW_AZ=ap-northeast-2a   # data-ebs/terraform.tfvars의 availability_zone과 같아야 한다.
SNAP_ID=<snapshot-id>
OLD_VOL=$(terraform -chdir=data-ebs output -raw data_volume_id)
INSTANCE_ID=$(terraform output -raw instance_id)
```

네 값이 모두 채워졌는지 확인한다.

```bash
echo "$NEW_AZ $SNAP_ID $OLD_VOL $INSTANCE_ID"
```

### 1. EC2 stop [로컬]

연결을 바꾸는 동안 DB에 쓰지 않도록 멈춘다.

```bash
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
```

### 2. 새 볼륨 생성 [로컬]

`Backup` 태그가 없으면 DLM이 새 볼륨을 찍지 않는다. 생성할 때 함께 붙인다.

```bash
NEW_VOL=$(aws ec2 create-volume \
  --snapshot-id "$SNAP_ID" --availability-zone "$NEW_AZ" --volume-type gp3 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=store-expiration-tracker-sqlite-data},{Key=Backup,Value=store-expiration-tracker-sqlite-data}]' \
  --query VolumeId --output text)
aws ec2 wait volume-available --volume-ids "$NEW_VOL"
echo "$NEW_VOL"
```

### 3. data-ebs state를 새 볼륨으로 교체 [로컬]

`state rm`은 Terraform의 기록에서만 빼고 실제 볼륨은 지우지 않는다. `prevent_destroy`와 충돌하지 않는다.

```bash
terraform -chdir=data-ebs state rm aws_ebs_volume.sqlite_data
terraform -chdir=data-ebs import aws_ebs_volume.sqlite_data "$NEW_VOL"
terraform -chdir=data-ebs plan
```

plan에 볼륨 교체(`must be replaced`)나 삭제가 있으면 멈춘다. `No changes`가 목표다. import만 하면 output이 갱신되지 않을 수 있으므로, plan에 output 변경만 있으면 apply한다.

```bash
terraform -chdir=data-ebs apply
terraform -chdir=data-ebs output -raw data_volume_id   # NEW_VOL과 같아야 한다.
```

### 4. EC2에 새 볼륨 연결 [로컬]

```bash
terraform plan
```

바뀌는 것이 `aws_volume_attachment.sqlite_data` 교체뿐인지 확인한다. **`aws_instance.deployment`가 교체되면 apply하지 않는다.** Root EBS와 인증서가 함께 사라진다.

```bash
terraform apply
```

### 5. 기동과 mount 확인

```bash
aws ec2 start-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
```

[EC2] SSH로 접속해 확인한다. mount되지 않았으면 앱을 띄우지 않는다([Issue #110](https://github.com/J4EU/Store-Expiration-Tracker/issues/110)).

```bash
findmnt /srv/store-expiration-tracker/data
sudo ls -l /srv/store-expiration-tracker/data
```

복원한 볼륨은 XFS UUID가 같아 `/etc/fstab`을 고치지 않아도 mount된다.

### 6. DB 검사 [EC2]

앱을 띄우기 전에 읽기 전용으로 검사한다.

```bash
cd Store-Expiration-Tracker
docker compose -f compose.ec2.yaml run --rm --no-deps backend python -c "
import sqlite3
c = sqlite3.connect('file:/app/data/store_expiration_tracker.db?mode=ro', uri=True)
print(c.execute('PRAGMA integrity_check').fetchall())
print(c.execute('PRAGMA foreign_key_check').fetchall())
for t in ('products', 'expiration_states', 'discard_histories'):
    print(t, c.execute('SELECT count(*) FROM ' + t).fetchone()[0])
"
```

- `integrity_check`는 `[('ok',)]`, `foreign_key_check`는 `[]`이어야 한다.
- 빈 DB도 검사를 통과하므로, 행 수를 스냅샷 시점에 있어야 할 값과 비교한다.

### 7. 앱 기동 [EC2]

```bash
docker compose -f compose.ec2.yaml up --wait
```

[EC2 Manual Deploy Runbook](ec2-manual-deploy.md) 9단계로 확인하고, 화면에서 데이터를 본다.

### 되돌리기

새 볼륨에 문제가 있으면 EC2를 stop하고, 3단계의 `NEW_VOL` 자리에 `OLD_VOL`을 넣어 3단계부터 다시 한다.

### 마무리

새 볼륨을 정상으로 판단한 뒤 기존 볼륨을 정리한다.

- `OLD_VOL`에도 `Backup` 태그가 남아 있어 DLM이 두 볼륨을 모두 찍는다. 태그를 떼고 이름에 `-old`를 붙여 보관한다.
- 태그를 떼면 DLM이 `OLD_VOL`의 기존 스냅샷을 더는 관리하지 않는다. 보관 기간이 지나도 자동으로 지워지지 않는다.
- 새 볼륨의 자동 스냅샷이 정상으로 생기는 것을 확인한 뒤 `OLD_VOL`을 지운다. 볼륨 삭제는 되돌리기 어려우므로 따로 확인한 뒤 한다.

## 지운 스냅샷 되살리기 [로컬]

`Backup` 태그가 붙은 스냅샷은 지운 뒤 28일 동안 Recycle Bin에 남는다. 태그가 없는 스냅샷은 지우면 바로 사라진다.

```bash
aws ec2 list-snapshots-in-recycle-bin
aws ec2 restore-snapshot-from-recycle-bin --snapshot-id <snapshot-id>
```

되살린 스냅샷은 `completed` 상태로 돌아오고, `Backup`·DLM 태그와 만료 예정 시각도 지우기 전과 같다. DLM이 계속 관리한다.

## 복원 테스트 기록

2026-11-26에 볼륨 전체 교체 절차를 실행했다([Issue #98](https://github.com/J4EU/Store-Expiration-Tracker/issues/98)).

- 시나리오: 테스트 상품 1개를 SQL로 지운 뒤, 지우기 전에 생성된 03:13 자동 스냅샷으로 복원했다.
- 결과: `integrity_check`는 `ok`, `foreign_key_check`는 위반 없음. 상품·소비기한·폐기 이력이 지우기 전과 같았고, 화면에서 지운 상품이 다시 보였다.
- data-ebs import 후 plan은 `No changes`, infra plan은 `aws_volume_attachment` 교체 1건뿐이었다. EC2는 교체되지 않았다.

| 구간 | 시각(KST) |
| --- | --- |
| 시작(0단계 직후) | 13:57:15 |
| EC2 stop 완료 | 13:57:47 |
| 새 볼륨 생성 완료 | 13:58:08 |
| DB 검사 완료 | 14:02:39 |
| 화면에서 복구 확인 | 14:04:50 |

합계 약 7분 35초다. 명령과 판단 기준을 미리 준비하고 plan을 함께 확인한 조건이라, 실제 사고 때는 원인 파악과 판단에 시간이 더 걸릴 수 있다.
