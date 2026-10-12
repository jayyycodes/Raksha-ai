"""
Anomaly Detector — detects unusual spikes in article volume or threat levels.
Owner: Jay
Stage: 3

Monitors for:
    - Volume spikes: 3x normal article count from a source/region in a window
    - Sentiment shifts: sudden increase in "alarming" articles
    - New event types: first-time event type from a specific source

Stores alerts in the alerts table.

Usage:
    from report.anomaly import detect_anomalies
    alerts = detect_anomalies()
"""
from common.constants import SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL
from common.logger import get_logger

logger = get_logger(__name__)


def detect_anomalies(window_hours: int = 24) -> list[dict]:
    """
    Scan recent data for anomalies and generate alerts.

    Args:
        window_hours: Time window to analyze

    Returns:
        List of {"alert_type": str, "region": str, "description": str, "severity": str}

    TODO (Jay):
        1. Query article counts per source/region for current vs historical window
        2. Flag volume spikes (current > 3x historical average)
        3. Flag sentiment anomalies (alarming ratio spike)
        4. Insert into alerts table
        5. Log summary
    """
    raise NotImplementedError("Anomaly detection not yet implemented — Stage 3")
