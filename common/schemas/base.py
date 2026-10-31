from pydantic import BaseModel
from typing import List, Optional

class ProvenanceFields(BaseModel):
    """Mixin for provenance information attached to derived records."""
    source_ids: Optional[List[int]] = None  # IDs of source articles
    method: Optional[str] = None            # rule | model name | human
    model_version: Optional[str] = None     # version string of the model used
    confidence: Optional[float] = None      # 0‑1 confidence where applicable
    created_at: Optional[str] = None        # ISO‑8601 timestamp
    reviewed_by: Optional[str] = None       # analyst identifier if reviewed
    claim_status: Optional[str] = None      # reported | official_designation | analyst_verified
    source_type: Optional[str] = None       # public | user_upload
