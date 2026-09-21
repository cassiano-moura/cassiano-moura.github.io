# ==============================================================================
# AUTO SCALING GROUP & LAUNCH TEMPLATE
# Project: Multi-Tier Resilient AWS Architecture
# Engineer: Cassiano Moura
# ==============================================================================

# 1. Fetch Latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 2. Launch Template for App Tier EC2 Instances
resource "aws_launch_template" "app_lt" {
  name_prefix   = "${var.project_name}-lt-"
  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.instance_type

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.app_sg.id]
  }

  # User Data Script - Installs Nginx & Health Response
  user_data = base64encode(<<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y nginx

              TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
              INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
              AVAIL_ZONE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)

              cat <<HTML > /usr/share/nginx/html/index.html
              <!DOCTYPE html>
              <html>
              <head><title>Production App Instance - Healthy</title></head>
              <body style="font-family:sans-serif; background:#0B0F19; color:#F8FAFC; text-align:center; padding:50px;">
                <h1 style="color:#38BDF8;">AWS Multi-Tier Architecture Online</h1>
                <p><strong>Instance ID:</strong> $INSTANCE_ID</p>
                <p><strong>Availability Zone:</strong> $AVAIL_ZONE</p>
                <p style="color:#10B981;">Status: Healthy (HTTP 200 OK)</p>
                <p style="font-size:0.85em; color:#94A3B8;">Deployed via Terraform by Cassiano Moura</p>
              </body>
              </html>
              HTML

              systemctl enable nginx
              systemctl start nginx
              EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-ec2"
      Tier = "Application"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# 3. Auto Scaling Group spanning Private App Subnets
resource "aws_autoscaling_group" "app_asg" {
  name_prefix         = "${var.project_name}-asg-"
  vpc_zone_identifier = aws_subnet.private_app[*].id
  target_group_arns   = [aws_lb_target_group.app_tg.arn]

  min_size         = var.asg_min_size
  max_size         = var.asg_max_size
  desired_capacity = var.asg_desired_capacity

  health_check_type         = "ELB"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.app_lt.id
    version = "$Latest"
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-asg-instance"
    propagate_at_launch = true
  }
}

# 4. Target Tracking Scaling Policy (CPU Utilization at 70%)
resource "aws_autoscaling_policy" "cpu_policy" {
  name                   = "${var.project_name}-cpu-target-policy"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
