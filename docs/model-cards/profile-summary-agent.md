# Model Card: Profile Summary Agent (`profile_summary_agent`)

**Version:** 0.2.0  
**Owner:** Jaish  
**Role:** AI/ML Intelligence & Generation Agents  
**Date:** November 2026  
**Stage:** 2 (Mid)

---

## 1. Overview & Purpose

The **Profile Summary Agent** compiles attributed intelligence dossiers for named entities (Person, Organisation, Location, Equipment) observed across multi-ring news feeds.

---

## 2. Responsible Use & Safeguards

1. **Candidate-to-Profile Rule:**
   - Entities remain unpromoted candidates until they accumulate $\ge 3$ mentions across $\ge 2$ unique public sources, or until an analyst manually reviews and promotes them.
2. **Sensitive-Attribute Filter (India DPDP Act Compliance):**
   - Hard safety rule: the system **never infers, stores, or summarizes** religion, caste, sub-caste, faith, sect, ethnicity, or medical/health conditions.
   - Any raw text mentioning protected attributes is permanently rejected prior to database persistence.
3. **Attribution & Claim Status:**
   - Statements are explicitly tagged with `claim_status`: `official_designation`, `analyst_verified`, or `reported`.
   - No subjective labels (such as "terrorist" or "criminal") are generated autonomously.

