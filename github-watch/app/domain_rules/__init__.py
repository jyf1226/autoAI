from __future__ import annotations

from importlib import import_module


def get_domain_rule(domain: str) -> dict[str, str | list[str]]:
    module_name = domain.replace("-", "_")
    module = import_module(f"app.domain_rules.{module_name}")
    return {
        "keywords": getattr(module, "KEYWORDS", []),
        "research_angle": getattr(module, "RESEARCH_ANGLE", ""),
        "inspiration_angle": getattr(module, "INSPIRATION_ANGLE", ""),
    }
