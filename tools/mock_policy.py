POLICY_DB = {
    "生鲜破损": "请在 App【我的-售后】上传照片申请补货",
    "台风停运": "极端天气以区域通知为准",
    "佣金结算": "每日 18:00 结算前日佣金"
}

def lookup_policy(keyword: str) -> str:
    return POLICY_DB.get(keyword, "暂无相关政策")