from __future__ import annotations

from dataclasses import dataclass

from app.detections.contracts import NormalizedTelemetryEvent, RuleEvaluation, RuleHit
from app.detections.rules.base import DetectionRule


@dataclass(frozen=True)
class _ToolSpec:
    slug: str
    display_name: str
    vendor: str
    domains: tuple[str, ...]
    display_markers: tuple[str, ...]


# Curated for Shadow AI: consumer + enterprise surfaces commonly seen in M365 logs.
_AI_TOOLS: tuple[_ToolSpec, ...] = (
    _ToolSpec(
        "chatgpt",
        "ChatGPT",
        "OpenAI",
        ("chat.openai.com", "chatgpt.com", "openai.com/chat", "api.openai.com"),
        ("chatgpt", "gpt-4", "gpt-3.5", "openai"),
    ),
    _ToolSpec(
        "claude",
        "Claude",
        "Anthropic",
        ("claude.ai", "anthropic.com", "console.anthropic.com"),
        ("claude", "anthropic"),
    ),
    _ToolSpec(
        "gemini",
        "Gemini",
        "Google",
        ("gemini.google.com", "bard.google.com", "generativelanguage.googleapis.com", "ai.google.dev"),
        ("gemini", "google bard", "palm api"),
    ),
    _ToolSpec(
        "perplexity",
        "Perplexity",
        "Perplexity AI",
        ("perplexity.ai", "www.perplexity.ai"),
        ("perplexity",),
    ),
    _ToolSpec(
        "copilot",
        "Microsoft Copilot",
        "Microsoft",
        (
            "copilot.microsoft.com",
            "edgeservices.bing.com",
            "bing.com/chat",
            "microsoft365.com/copilot",
            "m365.cloud.microsoft/copilot",
        ),
        ("microsoft copilot", "windows copilot", "github copilot", "copilot chat"),
    ),
    _ToolSpec(
        "grok",
        "Grok",
        "xAI",
        ("grok.com", "grok.x.ai", "x.ai"),
        ("grok", "grok-"),
    ),
)


class AIToolDomainRule(DetectionRule):
    """Match known AI surfaces via URL/domain fragments and display markers."""

    rule_id = "ai_tool_domain_v1"

    def evaluate(self, event: NormalizedTelemetryEvent) -> RuleEvaluation | None:
        hits: list[RuleHit] = []
        seen: set[str] = set()
        corpus = event.corpus
        for spec in _AI_TOOLS:
            if spec.slug in seen:
                continue
            matched: str | None = None
            weight = 0.0
            for d in spec.domains:
                if d in corpus:
                    matched = f"domain:{d}"
                    weight = 40.0
                    break
            if matched is None:
                for m in spec.display_markers:
                    token = m.strip().lower()
                    if token and token in corpus:
                        matched = f"marker:{m}"
                        weight = 36.0
                        break
            if matched:
                seen.add(spec.slug)
                hits.append(
                    RuleHit(
                        rule_id=self.rule_id,
                        sub_type=spec.slug,
                        weight=weight,
                        details={
                            "tool": spec.display_name,
                            "vendor": spec.vendor,
                            "match": matched,
                        },
                    ),
                )
        return RuleEvaluation(rule_id=self.rule_id, hits=hits) if hits else None


TOOL_BY_SLUG: dict[str, _ToolSpec] = {t.slug: t for t in _AI_TOOLS}
