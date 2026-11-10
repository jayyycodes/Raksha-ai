"""
Anomaly Detection Agent.
Owner: Jaish
Stage: 2 (Mid)

Detects statistical anomalies, volume surges, and threat escalations by comparing
recent activity (24-hour window) against a historical baseline (30 days).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from common.constants import (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
)
from common.logger import get_logger
from common.schemas.provenance import ClaimStatus, Provenance, SourceType
from common.schemas.intelligence import AnomalyCheckIn, AnomalyCheckOut
from agents.base import BaseAgent

logger = get_logger(__name__)


class AnomalyAgent(BaseAgent[AnomalyCheckIn, AnomalyCheckOut]):
    name = "anomaly_agent"
    version = "0.2.0"

    def detect_region_anomaly(
        self,
        region: str,
        current_articles: List[Dict[str, Any]],
        baseline_daily_average: float = 2.0,
    ) -> AnomalyCheckOut:
        """
        Analyzes a single region for volume, severity, or sentiment anomalies.
        """
        current_count = len(current_articles)
        effective_baseline = max(0.5, baseline_daily_average)
        deviation_factor = round(current_count / effective_baseline, 2)

        high_threat_count = sum(
            1 for a in current_articles
            if a.get("threat_level", 1) >= 8 or a.get("threat_category") == "high"
        )
        alarming_count = sum(
            1 for a in current_articles
            if str(a.get("sentiment", "")).lower() in ("alarming", "aggressive")
        )
        alarming_ratio = (alarming_count / current_count) if current_count > 0 else 0.0

        is_anomaly = False
        alert_severity: Optional[str] = None
        alert_type: Optional[str] = None
        description: Optional[str] = None

        # Rule 1: Critical volume or threat surge
        if (deviation_factor >= 3.5 and current_count >= 5) or high_threat_count >= 3:
            is_anomaly = True
            alert_type = "THREAT_ESCALATION" if high_threat_count >= 3 else "VOLUME_SPIKE"
            alert_severity = SEVERITY_CRITICAL if high_threat_count >= 3 else SEVERITY_HIGH
            description = (
                f"Critical activity surge in {region}: {current_count} articles ({deviation_factor}x baseline of {baseline_daily_average:.1f}/day) "
                f"with {high_threat_count} high-severity alerts."
            )
        # Rule 2: High volume surge
        elif deviation_factor >= 2.5 and current_count >= 4:
            is_anomaly = True
            alert_type = "VOLUME_SPIKE"
            alert_severity = SEVERITY_HIGH if high_threat_count >= 1 else SEVERITY_MEDIUM
            description = (
                f"Significant volume anomaly in {region}: {current_count} articles detected in 24h, "
                f"exceeding 30-day baseline by {deviation_factor}x."
            )
        # Rule 3: Sentiment alarm spike
        elif current_count >= 3 and alarming_ratio >= 0.6:
            is_anomaly = True
            alert_type = "SENTIMENT_ANOMALY"
            alert_severity = SEVERITY_MEDIUM
            description = (
                f"Alarming sentiment spike in {region}: {alarming_count}/{current_count} articles ({alarming_ratio*100:.0f}%) "
                f"exhibit hostile or alarming framing."
            )
        else:
            description = f"Normal operational baseline in {region} ({current_count} articles, {deviation_factor}x baseline)."

        prov = Provenance(
            source_ids=[a.get("id") for a in current_articles if a.get("id") is not None],
            method="statistical_baseline_deviation_v2",
            model_version=f"{self.name}:{self.version}",
            confidence=0.90 if is_anomaly else 0.75,
            claim_status=ClaimStatus.REPORTED,
            source_type=SourceType.PUBLIC,
        )

        return AnomalyCheckOut(
            region=region,
            is_anomaly=is_anomaly,
            current_count=current_count,
            baseline_average=baseline_daily_average,
            deviation_factor=deviation_factor,
            alert_severity=alert_severity,
            description=description,
            provenance=prov,
        )

    def scan_all_regions(
        self,
        region_articles: Dict[str, List[Dict[str, Any]]],
        baselines: Optional[Dict[str, float]] = None,
    ) -> List[AnomalyCheckOut]:
        """Scans all monitored regions for anomalies."""
        baselines = baselines or {}
        results = []
        for region, articles in region_articles.items():
            base_avg = baselines.get(region, 2.0)
            res = self.detect_region_anomaly(region, articles, baseline_daily_average=base_avg)
            results.append(res)
        return results

    def run(self, input_data: AnomalyCheckIn) -> AnomalyCheckOut:
        # Standalone invocation for a single region
        return self.detect_region_anomaly(
            region=input_data.region,
            current_articles=[],
            baseline_daily_average=2.0,
        )
