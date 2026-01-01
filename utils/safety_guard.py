# utils/safety_guard.py
from config.settings import settings

def contains_sensitive_content(text: str) -> bool:
    return any(kw in text for kw in settings.SENSITIVE_KEYWORDS)

def mask_pii(text: str) -> str:
    import re
    text = re.sub(r'1[3-9]\d{9}', '1XXXXXXXXX', text)
    text = re.sub(r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]\d{5,6}', 'XX地址', text)
    return text