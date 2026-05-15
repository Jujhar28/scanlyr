from __future__ import annotations

from enum import StrEnum


class OrganizationStatus(StrEnum):
    active = "active"
    suspended = "suspended"
    trial = "trial"


class MembershipStatus(StrEnum):
    invited = "invited"
    active = "active"
    revoked = "revoked"


class ScanSessionStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class DetectionSeverity(StrEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskScoreKind(StrEnum):
    detection = "detection"
    session = "session"
    organization = "organization"


class ReportStatus(StrEnum):
    draft = "draft"
    queued = "queued"
    rendering = "rendering"
    ready = "ready"
    failed = "failed"


class ReportType(StrEnum):
    compliance = "compliance"
    executive = "executive"
    incident = "incident"
    custom = "custom"


class AuditActorType(StrEnum):
    user = "user"
    system = "system"
    api_key = "api_key"


class IntegrationStatus(StrEnum):
    active = "active"
    disabled = "disabled"
    error = "error"


class MicrosoftGraphConnectionStatus(StrEnum):
    disconnected = "disconnected"
    pending = "pending"
    connected = "connected"
    error = "error"
