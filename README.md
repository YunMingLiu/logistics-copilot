# Logistics Copilot

Enterprise Multi-Agent Assistant for Meituan Youxuan Logistics.

## Features
- ✅ **Intent Recognition**: 15+ logistics intents with confidence scoring
- ✅ **Safety First**: Sensitive word blocking, low-confidence fallback
- ✅ **Three Response Modes**:
  - **Query**: Return factual answers (read-only)
  - **Action**: Provide Deep Link for user confirmation
  - **Incident**: Create structured ticket for human review
- ✅ **Zero Long-term Memory**: No user history stored
- ✅ **Audit Trail**: All incidents logged

## Architecture
%%{init: {'theme': 'default', 'themeVariables': { 'fontSize': '14px'}}}%%
graph TD
    A[用户提问<br/>(司机/团长)] --> B{Orchestrator Agent<br/>意图识别 + 安全初筛}

    %% 敏感词或低置信度 → 直接转人工
    B -->|命中敏感词<br/>（赔偿/隐私/起诉等）| C[立即拦截]
    B -->|置信度 < 0.85<br/>或意图不明] D[低置信度兜底]

    C --> E[返回话术：<br/>“该问题涉及敏感内容，请联系人工客服”]
    D --> E

    %% 高置信度 → 路由到三类处理器
    B -->|高置信度 ≥ 0.85| F{意图分类}
    
    F -->|查询类<br/>（订单状态/政策/佣金）| G[Query Handler]
    F -->|操作建议类<br/>（破损上报/漏派补单）| H[Action Handler]
    F -->|高风险/复合异常类<br/>（赔偿诉求/用户投诉/多问题交织）| I[Incident Handler]

    %% Query Handler：只读工具 + 安全审查
    G --> G1[调用只读工具：<br/>TMS / WMS / Policy Center]
    G1 --> G2{安全审查：<br/>是否含模糊词？<br/>（可能/大概/建议）}
    G2 -->|是| E
    G2 -->|否| J[返回结构化答案]

    %% Action Handler：提供 Deep Link，不自动执行
    H --> H1[生成操作引导 + Deep Link]
    H1 --> K[返回话术：<br/>“请【点击上传照片】申请补货”<br/>+ App 深度链接]

    %% Incident Handler：生成快照 + 创建工单
    I --> I1[并行拉取多源数据：<br/>订单 + GPS + 聊天记录 + 规则]
    I1 --> I2[生成“异常快照”<br/>（JSON 结构化上下文）]
    I2 --> I3[调用工单系统 API<br/>创建高优审批工单]
    I3 --> L[返回话术：<br/>“已提交专员处理，10分钟内联系您”]

    %% 所有输出汇总
    J --> M[用户收到响应]
    K --> M
    L --> M
    E --> M

    %% 样式美化
    classDef agent fill:#e6f3ff,stroke:#0066cc,stroke-width:2px;
    classDef handler fill:#e6ffe6,stroke:#009933;
    classDef safety fill:#fff2e6,stroke:#ff6600;
    classDef output fill:#f0f0f0,stroke:#666;

    class B,F,G,H,I agent
    class G1,H1,I1,I2,I3 handler
    class C,D,G2 safety
    class E,J,K,L,M output





