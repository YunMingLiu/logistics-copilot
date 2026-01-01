# utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Intent Classification
INTENT_REQUESTS = Counter("intent_requests_total", "Total intent classification requests")
INTENT_CONFIDENCE = Gauge("intent_confidence", "Latest intent confidence score")

# RAG Policy
RAG_POLICY_HIT = Counter("rag_policy_hit_total", "RAG policy hit")
RAG_POLICY_MISS = Counter("rag_policy_miss_total", "RAG policy miss")
RAG_DURATION = Histogram("rag_policy_duration_seconds", "RAG response time")

# Fallback
FALLBACK_TO_HUMAN = Counter("fallback_to_human_total", "Total fallback to human")