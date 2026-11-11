# Model Card: Corroboration Agent (`corroboration_agent`)

**Version:** 0.2.0  
**Owner:** Jaish  
**Role:** AI/ML Intelligence & Generation Agents  
**Date:** November 2026  
**Stage:** 2 (Mid)

---

## 1. Overview & Purpose

The **Corroboration Agent** monitors cross-source narrative convergence and divergence by identifying `CORROBORATED_BY` and `CONTRADICTS` relationships across news items.

---

## 2. Capabilities

1. **Cross-Source Corroboration (`CORROBORATED_BY`):**
   - Links independent sources confirming identical events, weapon trials, or diplomatic dialogues.
2. **Conflict & Contradiction Detection (`CONTRADICTS`):**
   - Flags narrative clashes between Indian official releases (Ring 1) and foreign adversary media (Ring 2).
   - Identifies casualty discrepancies and denied incidents.
3. **Disinformation Indicator:**
   - Computes a ratio of contradictory reports over an event cluster to highlight narrative warfare operations.

