# Model Card: Anomaly Detection Agent (`anomaly_agent`)

**Version:** 0.2.0  
**Owner:** Jaish  
**Role:** AI/ML Intelligence & Generation Agents  
**Date:** November 2026  
**Stage:** 2 (Mid)

---

## 1. Overview & Purpose

The **Anomaly Detection Agent** flags statistical volume surges, severe threat escalations, and sentiment alarm spikes by comparing recent 24-hour activity against a 30-day rolling regional baseline.

---

## 2. Detection Criteria & Severity

- **Critical Alert (`SEVERITY_CRITICAL`):**
  - $\ge 3$ high-threat articles or deviation factor $\ge 3.5$ in sensitive border zones.
- **High Alert (`SEVERITY_HIGH`):**
  - Volume surge $\ge 2.5\times$ baseline with $\ge 4$ articles.
- **Medium Alert (`SEVERITY_MEDIUM`):**
  - Hostile sentiment surge ($\ge 60\%$ alarming ratio with $\ge 3$ articles).

---

## 3. Provenance & Audit

Alerts feed directly into the `alerts` database table and carry:
- `method`: `statistical_baseline_deviation_v2`
- `deviation_factor`: Numeric multiplier relative to daily average.
- `provenance`: Complete source article IDs and timestamp.

