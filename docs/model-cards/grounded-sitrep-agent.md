# Model Card: Grounded Daily SitRep Agent (`grounded_sitrep_agent`)

**Version:** 0.2.0  
**Owner:** Jaish  
**Role:** AI/ML Intelligence & Generation Agents  
**Date:** November 2026  
**Stage:** 2 (Mid)

---

## 1. Overview & Purpose

The **Grounded Daily SitRep Agent** generates daily morning strategic intelligence reports (06:00 AM) summarizing the 24-hour national security landscape. Every assertion in the report is strictly grounded in cited public sources.

---

## 2. Core Safeguards Against Hallucination

1. **Sentence-Level Grounding:**
   - Every factual assertion must include explicit citations in format `[Source #ID]`.
2. **Citation Verification Engine:**
   - Automatically parses all sentences and verifies that each cited ID exists in the ingested dataset.
   - Any statement lacking a valid citation is flagged with `is_supported=False`.
3. **Grounding Rate Metric:**
   - Emits `grounding_rate` = $\frac{\text{supported sentences}}{\text{total sentences}}$.
4. **Dual Engine Execution:**
   - Primary: Groq Llama 3 (`llama-3.3-70b-versatile` configured via `settings.GROQ_MODEL`).
   - Fallback: Deterministic intelligence synthesis ensuring 100% operational availability during network outages or API exhaustion.

