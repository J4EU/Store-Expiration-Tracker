data "aws_caller_identity" "current" {}

resource "aws_iam_role" "dlm" {
  name = "${var.name_prefix}-dlm"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "dlm.amazonaws.com" }
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "dlm" {
  role       = aws_iam_role.dlm.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSDataLifecycleManagerServiceRole"
}

resource "aws_dlm_lifecycle_policy" "sqlite_data" {
  description        = "SQLite Data EBS snapshots"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]
    target_tags    = local.backup_tags

    # DLM 시각은 UTC다. 18:00 UTC는 다음 날 03:00 KST다.
    schedule {
      name = "daily-30-days"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["18:00"]
      }

      retain_rule {
        interval      = 30
        interval_unit = "DAYS"
      }

      copy_tags = false
      tags_to_add = {
        Name   = "${var.name_prefix}-sqlite-data"
        Backup = local.backup_tags.Backup
      }
    }

    # 매월 말일(L) 18:00 UTC, 즉 다음 달 1일 03:00 KST에 찍어 전월 말일 업무분까지 담는다.
    # DLM은 시간대를 지정할 수 없어 UTC 말일로 KST 1일을 맞춘다.
    schedule {
      name = "monthly-12-months"

      create_rule {
        cron_expression = "cron(0 18 L * ? *)"
      }

      retain_rule {
        interval      = 12
        interval_unit = "MONTHS"
      }

      copy_tags = false
      tags_to_add = {
        Name   = "${var.name_prefix}-sqlite-data"
        Backup = local.backup_tags.Backup
      }
    }
  }

  depends_on = [aws_iam_role_policy_attachment.dlm]
}

resource "aws_rbin_rule" "sqlite_data_snapshots" {
  description   = "Retain deleted SQLite Data EBS snapshots"
  resource_type = "EBS_SNAPSHOT"

  resource_tags {
    resource_tag_key   = "Backup"
    resource_tag_value = local.backup_tags.Backup
  }

  retention_period {
    retention_period_value = 28
    retention_period_unit  = "DAYS"
  }
}
