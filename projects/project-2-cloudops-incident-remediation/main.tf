# ==============================================================================
# CLOUDOPS AUTOMATED INCIDENT REMEDIATION PIPELINE
# Technologies: AWS CloudWatch, Amazon SNS, AWS Lambda (Python), AWS Systems Manager
# Engineer: Cassiano Moura
# ==============================================================================

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "cloudops-incident-remediation"
}

# 1. Amazon SNS Topic for Incident Dispatch
resource "aws_sns_topic" "incident_topic" {
  name = "${var.project_name}-topic"

  tags = {
    Project   = var.project_name
    Owner     = "Cassiano Moura"
    ManagedBy = "Terraform"
  }
}

# 2. CloudWatch Metric Alarm: High CPU Utilization (> 85%)
resource "aws_cloudwatch_metric_alarm" "high_cpu_alarm" {
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Triggers when instance CPU exceeds 85% for 2 consecutive minutes."

  alarm_actions = [aws_sns_topic.incident_topic.arn]

  tags = {
    Project = var.project_name
    Tier    = "CloudOps"
  }
}

# 3. Archive Python script for Lambda Deployment
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_remediation.py"
  output_path = "${path.module}/lambda_remediation.zip"
}

# 4. IAM Role for Lambda Remediation Runner
resource "aws_iam_role" "lambda_remediation_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_remediation_policy" {
  name = "${var.project_name}-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.incident_topic.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation",
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_remediation_policy" {
  role       = aws_iam_role.lambda_remediation_role.name
  policy_arn = aws_iam_policy.lambda_remediation_policy.arn
}

# 5. AWS Lambda Function for Auto-Remediation
resource "aws_lambda_function" "remediation_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-handler"
  role             = aws_iam_role.lambda_remediation_role.arn
  handler          = "lambda_remediation.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      OPS_NOTIFICATION_TOPIC = aws_sns_topic.incident_topic.arn
    }
  }

  tags = {
    Project = var.project_name
  }
}

# 6. Allow SNS to Invoke Lambda
resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remediation_handler.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.incident_topic.arn
}

# 7. Subscribe Lambda to SNS Topic
resource "aws_sns_topic_subscription" "lambda_subscription" {
  topic_arn = aws_sns_topic.incident_topic.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.remediation_handler.arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.incident_topic.arn
}

output "cloudwatch_alarm_id" {
  value = aws_cloudwatch_metric_alarm.high_cpu_alarm.id
}

output "lambda_arn" {
  value = aws_lambda_function.remediation_handler.arn
}
