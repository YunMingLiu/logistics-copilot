# utils/logger.py
import json
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)

def log_incident(snapshot: dict):
    incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    record = {
        "incident_id": incident_id,
        "timestamp": datetime.now().isoformat(),
        "snapshot": snapshot
    }
    # 实际写入 Kafka / 日志系统
    print(f"📝 工单已创建: {incident_id}")
    return incident_id