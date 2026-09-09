"""
Phase 7 - Rule database loader.

Loads rules/lmpc_rules_database.json and presents it as typed Rule objects so
the rule engine can iterate the mandatory declarations, font-size/legibility
rules, and placement/manner rules without knowing which validation_logic
type each entry carries. Rule updates simply edit the JSON (no code change).
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_RULES_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "rules", "lmpc_rules_database.json"
)


@dataclass
class Rule:
    rule_id: str
    rule_reference: str
    field_name: str
    title: str = ""
    requirement: str = ""
    validation_logic: dict = field(default_factory=dict)
    status: str = "active"            # "omitted" | "disabled" | "active"
    exemptions: list = field(default_factory=list)


def load_rules_db(path: Optional[str] = None) -> dict:
    """Load the raw rules JSON dictionary."""
    path = path or _RULES_DB_PATH
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_mandatory_rules(path: Optional[str] = None) -> List[Rule]:
    """Load mandatory declarations as Rule objects (active ones only)."""
    db = load_rules_db(path)
    rules = []
    for entry in db.get("mandatory_declarations", []):
        status = entry.get("status", "active")
        if status in ("omitted", "disabled"):
            continue
        rules.append(Rule(
            rule_id=entry["rule_id"],
            rule_reference=entry.get("rule_reference", ""),
            field_name=entry.get("field_name", ""),
            title=entry.get("title", ""),
            requirement=entry.get("requirement", ""),
            validation_logic=entry.get("validation_logic", {}),
            status=status,
            exemptions=entry.get("exemptions", []),
        ))
    return rules


def load_font_rules(path: Optional[str] = None) -> dict:
    """Return the font_size_and_legibility_rules section unchanged."""
    db = load_rules_db(path)
    return db.get("font_size_and_legibility_rules", {})


def load_placement_rules(path: Optional[str] = None) -> List[Rule]:
    """Load placement_and_manner_rules as Rule objects."""
    db = load_rules_db(path)
    rules = []
    for entry in db.get("placement_and_manner_rules", []):
        rules.append(Rule(
            rule_id=entry["rule_id"],
            rule_reference=entry.get("rule_reference", ""),
            field_name=entry.get("title", ""),   # placement rules have no field_name; use title
            title=entry.get("title", ""),
            requirement=entry.get("requirement", ""),
            validation_logic=entry.get("validation_logic", {}),
            status="active",
        ))
    return rules


def load_all() -> Dict[str, object]:
    """Convenience: everything the rule engine needs in one dict."""
    return {
        "mandatory": load_mandatory_rules(),
        "font": load_font_rules(),
        "placement": load_placement_rules(),
        "raw_db": load_rules_db(),
    }