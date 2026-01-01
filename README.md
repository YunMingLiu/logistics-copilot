# Logistics Copilot

Enterprise Multi-Agent Assistant for Logistics.

## Features
✅ 意图识别  
 • 支持15+物流相关意图（如补货申请、破损赔付、路线变更等）  
 • 每次识别输出置信度评分（0.0–1.0），用于路由决策  

✅ 安全优先  
 • 实时敏感词检测（如“赔偿”“起诉”“隐私泄露”），触发即拦截并转人工  
 • 当置信度 < 0.85 或意图为“其他”时，自动进入低置信度兜底流程  

✅ 三种响应模式  
 • **查询类**：仅返回预审批知识库答案或只读API数据（如订单状态、政策条款），禁止LLM自由生成  
 • **操作类**：生成带深层链接（deep link）的引导语（如“点击上传照片”），用户需在App前端确认后才触发后端执行  
 • **事件类**：聚合订单、GPS、聊天记录等上下文，生成结构化工单，提交至高优人工队列，并告知用户“专员10分钟内联系”  

✅ 隐私与合规  
 • **无长期记忆**：对话结束后不存储任何用户身份或历史交互数据  
 • **完整审计追踪**：所有被拦截、转人工、工单创建等事件均记录时间戳、上下文快照与处理路径，支持事后回溯

## Architecture

本项目采用LangGraph + LangChain，为物流运营打造了一个企业级、安全至上的多智能体系统。与黑盒式自主智能体不同，我们的设计遵循集中编排+专业化处理程序的模式，以确保可审计性、合规性和人机协同控制——这对B2B场景至关重要。

🔁 System Workflow
```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'fontSize': '14px'}}}%%
graph TD
    A["用户输入<br/>（司机 / 小组组长）"] --> B{"协调器智能体<br/>意图识别 + 安全审查"}

    %% 立即转人工路径
    B -->|"检测到敏感词<br/>（例如：赔偿、隐私、起诉）"| C["拦截并返回人工提示"]
    B -->|"置信度 < 0.85<br/>或意图为“其他”"| D["低置信度兜底处理"]

    C --> Z["返回用户响应"]
    D --> Z

    %% 高置信度路由
    B -->|"置信度 ≥ 0.85"| F{"意图分类"}

    F -->|"查询类"| G{"查询子类型？"}
    F -->|"操作建议类"| H["操作处理器"]
    F -->|"高风险 / 复合类"| I["事件处理器"]

    %% 查询分支细化
    G -->|"政策查询<br/>（例如：破损赔付规则）"| G1["从政策知识库检索<br/>（向量数据库 / 规则引擎）"]
    G -->|"API 数据查询<br/>（例如：订单状态）"| G2["调用只读 API<br/>（TMS / WMS）"]

    G1 --> G3["返回预审批答案<br/>（不使用 LLM 生成）"]
    G2 --> G4["通过 LLM 格式化结构化数据<br/>（基于模板）"]

    G3 --> Z
    G4 --> Z

    %% 操作处理器：强调前端二次确认
    H --> H1["生成引导操作 + 深层链接"]
    H1 --> H2["发送响应：<br/>“请【点击上传照片】申请补货”<br/>+ app://after-sales?..."]
    H2 --> H3["用户在 App 前端确认<br/>（上传 / 提交 / 取消）"]
    H3 -->|"已确认"| H4["通过后端 API 执行"]
    H3 -->|"已取消"| H5["不执行任何操作"]
    H4 --> H6["通知：“申请已提交”"]
    H5 --> H6
    H6 --> Z

    %% 事件处理器：快照 + 工单
    I --> I1["聚合多源上下文：<br/>订单 + GPS + 聊天记录"]
    I1 --> I2["创建结构化事件快照"]
    I2 --> I3["提交高优先级工单<br/>至人工团队"]
    I3 --> I4["发送响应：<br/>“已提交专员处理，10 分钟内联系您”"]
    I4 --> Z

    %% 统一输出

    %% 样式定义
    classDef agent fill:#e6f3ff,stroke:#0066cc;
    classDef handler fill:#e6ffe6,stroke:#009933;
    classDef safety fill:#fff2e6,stroke:#ff6600;
    classDef output fill:#f9f9f9,stroke:#666;
    classDef frontend fill:#fff0f5,stroke:#cc0066,stroke-dasharray: 5 5;

    class B,F,G,H,I agent
    class G1,G2,G3,G4,H1,H2,I1,I2,I3 handler
    class C,D safety
    class Z output
    class H3,H4,H5,H6 frontend


graph LR
    A[Java Spring Boot App] -->|gRPC| B[Python Smart Agent]
    B --> C[FAISS Policy Index]
    B --> D[SFT Intent Model]
    B --> E[Prometheus Metrics]
    C --> F[data/policy_docs.jsonl]
    D --> G[models/sft/intent_model]
