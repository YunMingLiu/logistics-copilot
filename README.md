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
```mermaid
graph LR
A[User] --> B(Orchestrator)
B -->|Low Conf/Sensitive| C[Return Human Handoff]
B -->|Query| D[Query Handler]
B -->|Action| E[Action Handler]
B -->|Incident| F[Incident Handler]
D --> G[Return Answer]
E --> H[Return Deep Link]
F --> I[Create Ticket + Notify]