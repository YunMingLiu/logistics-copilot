# 安全检查模块，负责内容审查
def is_safe(content):
    sensitive_words = ["赔偿", "隐私", "起诉"]
    for word in sensitive_words:
        if word in content:
            return False
    return True