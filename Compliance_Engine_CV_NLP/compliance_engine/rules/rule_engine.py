"""
Phase 7 - Rule engine (core compliance evaluation).

Drives the data-driven checks: loads rules/lmpc_rules_database.json once,
matches Phase 6 declarations against mandatory rules, and evaluates Phase 5
font/legibility metrics against the Rule 7 sections. Emits Violation rows +
ComplianceStats, which the final report (Phase 8) consumes.

Design rule: no rule thresholds are hardcoded here -- everything comes from
the JSON rule DB, so enforcement updates are a data change. Validators
(rules/validators.py) implement each validation_logic.type; the engine only
dispatches rule-by-rule. A Rule object (rules/rule_loader.py) carries
rule_id, rule_reference, field_name, requirement, validation_logic.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from compliance_engine.rules.rule_loader import Rule, load_all
from compliance_engine.rules.validators import REGISTRY, font_height_general_check, referral_violation
from compliance_engine.schema import ComplianceStats, DeclarationInfo, FontMetricInfo, Violation


@dataclass
class RuleContext:
    """Extra context passed to validators for cross-checks."""
    calibration_mm_per_px: float = 0.0
    font_metrics: List[FontMetricInfo] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class RuleEngine:
    """Stateless per-scan evaluator (rules DB loaded once at construction)."""

    def __init__(self, rules_bundle: Optional[dict] = None):
        bundle = rules_bundle or load_all()
        self.mandatory_rules: List[Rule] = bundle["mandatory"]
        self.font_rules = bundle["font"]
        self.placement_rules: List[Rule] = bundle["placement"]

    def _make_rule(self, rule_id: str, rule_reference: str, field_name: str,
                   validation_logic: Optional[dict] = None) -> Rule:
        return Rule(rule_id=rule_id, rule_reference=rule_reference,
                    field_name=field_name, validation_logic=validation_logic or {})

    # ------------------------------------------------------------------
    # Mandatory-declaration evaluation
    # ------------------------------------------------------------------
    def evaluate_mandatory(
        self, declarations: List[DeclarationInfo], ctx: RuleContext,
    ) -> List[Violation]:
        """Check each active mandatory rule against the extracted declarations."""
        by_field: Dict[str, DeclarationInfo] = {}
        for decl in declarations:
            if decl.field_name not in by_field:
                by_field[decl.field_name] = decl

        violations: List[Violation] = []
        for rule in self.mandatory_rules:
            decl = by_field.get(rule.field_name)
            logic = rule.validation_logic or {}
            validator = REGISTRY.get(logic.get("type"), REGISTRY["presence_check"])

            # Rules that only apply to e-commerce listings are N/A for an
            # image/label scan of a physical package.
            if "ecommerce" in rule.field_name and not ctx.metadata.get("is_ecommerce_listing"):
                violations.append(Violation(
                    rule_id=rule.rule_id, rule_reference=rule.rule_reference,
                    field_name=rule.field_name, status="not_applicable",
                    severity="low",
                    reason="N/A for physical package scan (e-commerce listing rule)",
                    evidence={},
                ))
                continue

            # Consumer-care rule: also honor separately-extracted phone/email
            # declaration rows (often found in full-image OCR even when the
            # care block itself OCR'd poorly).
            if rule.field_name == "consumer_care_details":
                decl = _resolve_consumer_care(decl, by_field)

            # Unit-sale-price (MD-10) is effective-date sensitive (LMPC 2021-
            # 2023 amendment, repeatedly deferred). When the declaration is not
            # detected AND the operator hasn't asserted the duty applies, flag
            # for verification rather than a hard 'missing' violation.
            if (rule.field_name == "unit_sale_price"
                    and (decl is None or not decl.value)
                    and not ctx.metadata.get("enforce_unit_sale_price")):
                violations.append(Violation(
                    rule_id=rule.rule_id, rule_reference=rule.rule_reference,
                    field_name=rule.field_name, status="not_applicable",
                    severity="low",
                    reason="Unit sale price not detected; requirement is "
                           "effective-date sensitive (LMPC 2021-2023 amendments, "
                           "repeatedly deferred) and is not being enforced for "
                           "this scan - pass metadata "
                           "enforce_unit_sale_price=true to enforce it",
                    evidence={},
                ))
                continue

            violation = validator(decl, rule, ctx)
            if violation is not None:
                violations.append(violation)
        return violations

    # ------------------------------------------------------------------
    # Font-size / legibility evaluation (Phase 5 metrics)
    # ------------------------------------------------------------------
    def evaluate_font(
        self, font_metrics: List[FontMetricInfo], ctx: RuleContext,
    ) -> List[Violation]:
        """Evaluate Rule 7(3) general letter-height against measured fonts."""
        violations: List[Violation] = []
        general = self.font_rules.get("general_letter_height", {})
        min_height_mm = (general.get("validation_logic", {})
                         .get("min_height_mm", {}).get("normal", 1.0))
        rule = self._make_rule(
            rule_id="FS-01",
            rule_reference=general.get("rule_reference", "Rule 7(3)"),
            field_name="font_size_and_legibility_rules.general_letter_height",
            validation_logic=general.get("validation_logic", {}),
        )
        for metric in font_metrics:
            v = font_height_general_check(metric, rule, float(min_height_mm))
            if v is not None:
                violations.append(v)
        return violations

    # ------------------------------------------------------------------
    # Placement rules: reference flags for human/rule review
    # ------------------------------------------------------------------
    def evaluate_placement(self, ctx: RuleContext) -> List[Violation]:
        """Reference flags for human/rule review; no auto thresholds here."""
        violations: List[Violation] = []
        by_id = {r.rule_id: r for r in self.placement_rules}
        for pid in ("PL-02", "PL-03", "PL-04"):
            rule = by_id.get(pid)
            if not rule:
                continue
            violations.append(referral_violation(
                rule,
                reason=f"Placement check requires manual/visual review ({rule.title})",
                severity="low",
                evidence={"kind": "referral"},
            ))
        return violations

    # ------------------------------------------------------------------
    # Entry-point
    # ------------------------------------------------------------------
    def evaluate(
        self,
        declarations: List[DeclarationInfo],
        font_metrics: List[FontMetricInfo],
        calibration_mm_per_px: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> tuple:
        """Run all checks; return (violations, stats)."""
        ctx = RuleContext(
            calibration_mm_per_px=calibration_mm_per_px,
            font_metrics=font_metrics,
            metadata=metadata or {},
        )
        violations = self.evaluate_mandatory(declarations, ctx)
        violations += self.evaluate_font(font_metrics, ctx)
        violations += self.evaluate_placement(ctx)
        return violations, _summarize(violations)


def _resolve_consumer_care(
    decl: Optional[DeclarationInfo],
    by_field: Dict[str, DeclarationInfo],
) -> Optional[DeclarationInfo]:
    """Merge consumer_phone/consumer_email rows into the care-details check.

    The consumer-care rule should pass when a phone/email was extracted from
    any source (zone or full-image OCR), even if the care block itself didn't
    OCR a complete contact.
    """
    phone = by_field.get("consumer_phone")
    email = by_field.get("consumer_email")
    contact = (phone.value if phone and phone.value else
               email.value if email and email.value else "")
    if not contact:
        return decl
    return DeclarationInfo(
        field_name="consumer_care_details",
        value=email.value if email and email.value else phone.value,
        raw_text=decl.raw_text if decl else "",
        confidence=max([d.confidence for d in (decl, phone, email) if d], default=0.5),
        method="merged",
        source_zone=(phone.source_zone if phone and phone.value else
                     email.source_zone if email else ""),
    )


def _summarize(violations: List[Violation]) -> ComplianceStats:
    stats = ComplianceStats(total_checks=len(violations))
    for v in violations:
        if v.status == "compliant":
            stats.compliant += 1
        elif v.status == "non_compliant":
            stats.non_compliant += 1
        elif v.status == "missing":
            stats.missing += 1
        elif v.status == "needs_review":
            stats.needs_review += 1
        elif v.status == "not_applicable":
            stats.not_applicable += 1
    return stats


def overall_status(stats: ComplianceStats,
                   violations: Optional[List[Violation]] = None) -> str:
    """Derive the headline compliance status from the violations.

    Placement/manual-review referrals (PL-02/03/04) are *informational*
    checkpoints: their validation_logic types (spacing / manual_flag / visual)
    need a human to eyeball the physical package, and the engine emits them on
    every scan by design. They stay visible in the report, but do not block a
    clean 'compliant' verdict - otherwise a compliant verdict would be
    unreachable for any scan. Pass `violations` so referrals can be told apart
    from substantive needs_review items (an unverified MRP qualifier, an
    uncalibrated font check, ...). When `violations` is omitted the legacy
    behaviour (every needs_review row blocks) is preserved for direct callers.
    """
    if violations is not None:
        blocking_review = sum(
            1 for v in violations
            if v.status == "needs_review" and v.evidence.get("kind") != "referral"
        )
    else:
        blocking_review = stats.needs_review
    if stats.non_compliant == 0 and stats.missing == 0:
        if blocking_review > 0:
            return "needs_review"
        return "compliant"
    if stats.non_compliant > 0 or stats.missing > 0:
        return "non_compliant"
    return "needs_review"