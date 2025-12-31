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

This project implements an enterprise-grade, safety-first multi-agent system for logistics operations using LangGraph + LangChain. Unlike black-box autonomous agents, our design follows a centralized orchestration + specialized handlers pattern to ensure auditability, compliance, and human-in-the-loop control — critical for B2B scenarios like Meituan Youxuan.

🔁 System Workflow
```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'fontSize': '14px'}}}%%
graph TD
    A[User Input<br/>(Driver / Group Leader)] --> B{Orchestrator Agent<br/>Intent Recognition + Safety Screening}

    %% Immediate Human Handoff Paths
    B -->|Sensitive Words Detected<br/>(e.g., 赔偿, 隐私, 起诉)| C[Block & Return Human Prompt]
    B -->|Confidence < 0.85<br/>or Intent = "other"| D[Low-Confidence Fallback]

    C --> E[Response: “该问题涉及敏感内容，请联系人工客服”]
    D --> E

    %% High-Confidence Routing
    B -->|Confidence ≥ 0.85| F{Intent Classification}
    
    F -->|Query-Type<br/>(order_status, policy_query)| G[Query Handler]
    F -->|Action-Suggestion<br/>(damage_report, missing_task)| H[Action Handler]
    F -->|High-Risk / Composite<br/>(compensation_claim, user_complaint)| I[Incident Handler]

    %% Query Handler: Read-Only + Safety Review
    G --> G1[Invoke Read-Only Tools:<br/>TMS / WMS / Policy Center]
    G1 --> G2{Safety Review:<br/>No Hallucination?<br/>(Block words: 可能, 建议, 大概)}
    G2 -->|Unsafe| E
    G2 -->|Safe| J[Return Structured Answer]

    %% Action Handler: Deep Link Only (No Auto-Execution)
    H --> H1[Generate Guided Action + Deep Link]
    H1 --> K[Response: “请【点击上传照片】申请补货”<br/>+ app://after-sales?...]

    %% Incident Handler: Snapshot + Ticket
    I --> I1[Aggregate Multi-Source Context:<br/>Order + GPS + Chat Log]
    I1 --> I2[Create Structured Incident Snapshot]
    I2 --> I3[Submit High-Priority Ticket<br/>to Human Team]
    I3 --> L[Response: “已提交专员处理，10分钟内联系您”]

    %% Final Output
    J --> M[User Receives Response]
    K --> M
    L --> M
    E --> M

    %% Styling
    classDef agent fill:#e6f3ff,stroke:#0066cc;
    classDef handler fill:#e6ffe6,stroke:#009933;
    classDef safety fill:#fff2e6,stroke:#ff6600;
    classDef output fill:#f9f9f9,stroke:#666;

    class B,F,G,H,I agent
    class G1,H1,I1,I2,I3 handler
    class C,D,G2 safety
    class E,J,K,L,M output