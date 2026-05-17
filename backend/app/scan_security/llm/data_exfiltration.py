from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class DataExfiltrationDetector(PatternListDetector):
    """Detects prompts aimed at exporting data, files, or tenant content."""

    detector_id = "llm_data_exfiltration"
    default_finding_type = "data_exfiltration"
    default_category = "data_exfiltration"
    default_risk_category = "data_exfiltration"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)\b(export|exfiltrate|dump|download)\s+(all\s+)?(user|customer|tenant|database)\s+data",
                ),
                "critical",
                "Bulk data export request",
                "Bulk export of user or tenant data requested: «{matched}».",
                "Deny bulk export via agents; require audited admin APIs.",
                risk_category="data_exfiltration",
            ),
            PatternSpec(
                re.compile(r"(?i)\bsend\s+(me\s+)?(the\s+)?(full\s+)?(chat\s+)?history\b"),
                "high",
                "Chat history exfiltration",
                "Request to send full conversation history externally: «{matched}».",
                "Scope history retrieval to authenticated session owners only.",
                risk_category="data_exfiltration",
            ),
            PatternSpec(
                re.compile(r"(?i)\bencode\s+(all\s+)?(records|rows|data)\s+(in\s+)?base64"),
                "high",
                "Encoded bulk export",
                "Attempt to encode records for covert export: «{matched}».",
                "Monitor for base64 blobs in outbound tool responses.",
                risk_category="data_exfiltration",
            ),
            PatternSpec(
                re.compile(r"(?i)\bupload\s+(results|data)\s+to\s+(pastebin|gist|dropbox|drive)"),
                "high",
                "Third-party data upload",
                "Instruction to upload data to external file sharing: «{matched}».",
                "Block egress to unapproved storage domains.",
                risk_category="data_exfiltration",
            ),
        )
