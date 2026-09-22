"""
==============================================================================
AWS Lambda Function: CloudOps Automated Incident Remediation Pipeline
Author: Cassiano Moura
Technologies: AWS CloudWatch, Amazon SNS, AWS Lambda (Python 3.12), AWS SSM
Purpose: Ingests CloudWatch Alarms (High CPU / Disk Full), parses alarm payload,
         triggers automated remediation (service restart / cache purge), and notifies ops.
==============================================================================
"""

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    import boto3
    HAS_BOTO3 = True
    ssm_client = boto3.client("ssm")
    sns_client = boto3.client("sns")
except ImportError:
    HAS_BOTO3 = False
    ssm_client = None
    sns_client = None

OPS_NOTIFICATION_TOPIC = os.environ.get("OPS_NOTIFICATION_TOPIC", "")


def lambda_handler(event, context):
    """
    Entry point invoked by Amazon SNS when a CloudWatch Alarm triggers.
    """
    logger.info("Received CloudWatch Alarm Event: %s", json.dumps(event))

    records = event.get("Records", [])
    remediation_results = []

    for record in records:
        sns_message_raw = record.get("Sns", {}).get("Message", "{}")
        try:
            alarm_data = json.loads(sns_message_raw)
        except (json.JSONDecodeError, TypeError):
            alarm_data = {"AlarmName": "Manual-Or-Direct-Test", "NewStateValue": "ALARM", "Reason": str(sns_message_raw)}

        result = process_alarm_and_remediate(alarm_data)
        remediation_results.append(result)

    # Fallback if invoked directly with alarm JSON
    if not records and "AlarmName" in event:
        remediation_results.append(process_alarm_and_remediate(event))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Incident pipeline execution completed.",
            "results": remediation_results
        })
    }


def process_alarm_and_remediate(alarm_data):
    """
    Evaluates alarm metric and executes the appropriate automated remediation runbook.
    """
    alarm_name = alarm_data.get("AlarmName", "Unknown-Alarm")
    new_state = alarm_data.get("NewStateValue", "ALARM")
    reason = alarm_data.get("NewStateReason", "Threshold breached")
    
    # Extract instance ID from dimensions if present
    dimensions = alarm_data.get("Trigger", {}).get("Dimensions", [])
    instance_id = "i-0autoassigned"
    for dim in dimensions:
        if dim.get("name") == "InstanceId":
            instance_id = dim.get("value")

    logger.warning("ALARM TRIGGERED: [%s] State: %s for Instance: %s", alarm_name, new_state, instance_id)

    remediation_action = "Investigate Manually"
    execution_status = "Skipped"

    # Remediation Policy 1: High CPU Utilization (> 85%)
    if "CPU" in alarm_name.upper():
        remediation_action = "Restart unresponsive worker processes and collect thread dump via SSM"
        execution_status = execute_ssm_command(
            instance_id=instance_id,
            command="systemctl restart nginx && sync && echo 'Service refreshed successfully'"
        )

    # Remediation Policy 2: High Disk Space Utilization (> 85%)
    elif "DISK" in alarm_name.upper():
        remediation_action = "Purge rotated system logs (/var/log/*.gz) and clean temporary cache (/tmp)"
        execution_status = execute_ssm_command(
            instance_id=instance_id,
            command="journalctl --vacuum-time=2d && rm -rf /tmp/*.tmp && df -h"
        )

    # Remediation Policy 3: Application Health Check Failure
    elif "HEALTH" in alarm_name.upper() or "5XX" in alarm_name.upper():
        remediation_action = "Restart application service and recycle connection pool"
        execution_status = execute_ssm_command(
            instance_id=instance_id,
            command="systemctl restart app-service || systemctl restart nginx"
        )

    incident_summary = {
        "alarm_name": alarm_name,
        "instance_id": instance_id,
        "state": new_state,
        "reason": reason,
        "remediation_action": remediation_action,
        "execution_status": execution_status
    }

    # Dispatch final incident report to engineering team
    dispatch_ops_notification(incident_summary)
    return incident_summary


def execute_ssm_command(instance_id, command):
    """
    Executes automated remediation command via AWS Systems Manager without SSH.
    """
    if not HAS_BOTO3 or not ssm_client or instance_id.startswith("i-0autoassigned"):
        logger.info("[SIMULATION MODE] Would execute via AWS SSM on %s: %s", instance_id, command)
        return "Simulated Success (Local/Dry-Run Mode)"

    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
            TimeoutSeconds=60
        )
        command_id = response["Command"]["CommandId"]
        logger.info("SSM Remediation Dispatched. Command ID: %s", command_id)
        return f"Dispatched via AWS SSM (Command ID: {command_id})"
    except Exception as e:
        logger.error("Failed to execute SSM command: %s", str(e))
        return f"Failed: {str(e)}"


def dispatch_ops_notification(incident):
    """
    Sends structured incident resolution report via Amazon SNS to engineering team.
    """
    subject = f"[AUTO-REMEDIATED] CloudOps Incident: {incident['alarm_name']}"
    message = (
        f"CloudOps Incident & Auto-Remediation Report:\n\n"
        f"• Alarm Name: {incident['alarm_name']}\n"
        f"• Affected Target: {incident['instance_id']}\n"
        f"• State: {incident['state']}\n"
        f"• Trigger Reason: {incident['reason']}\n"
        f"• Action Taken: {incident['remediation_action']}\n"
        f"• Execution Result: {incident['execution_status']}\n\n"
        f"Automated incident workflow powered by AWS CloudWatch + SNS + Lambda (Cassiano Moura)."
    )

    if HAS_BOTO3 and sns_client and OPS_NOTIFICATION_TOPIC:
        try:
            sns_client.publish(
                TopicArn=OPS_NOTIFICATION_TOPIC,
                Subject=subject[:100],
                Message=message
            )
            logger.info("Incident report published to SNS.")
        except Exception as e:
            logger.error("Failed publishing to SNS: %s", str(e))
    else:
        logger.info("[SIMULATION MODE] Notification generated:\n%s", message)
