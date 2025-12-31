**技术架构**

logistics-copilot/
├── README.md
├── requirements.txt
├── main.py
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py      # 意图识别 + 路由
│   ├── query_handler.py     # 查询类处理
│   ├── action_handler.py    # 操作建议类处理
│   └── incident_handler.py  # 高风险/复合异常处理
├── tools/
│   ├── __init__.py
│   ├── mock_tms.py          # Mock TMS（订单）
│   ├── mock_wms.py          # Mock WMS（仓储）
│   ├── mock_policy.py       # Mock 规则中心
│   └── mock_gps.py          # Mock GPS 轨迹
├── core/
│   ├── state.py             # AgentState 定义
│   ├── workflow.py          # LangGraph 编排
│   └── safety.py            # 安全审查模块
├── utils/
│   └── logger.py            # 审计日志
└── tests/
    └── test_intents.py      # 意图测试用例
