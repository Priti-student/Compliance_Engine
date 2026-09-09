"""
NLP declaration-extraction package (Phase 6).

The phone/email/dates/units/FSSAI/MRP regex patterns live in
`regex_patterns.py`; `declaration_extractor.py` runs them against the
Phase 4 zone text and produces DeclarationInfo rows that Phase 7's rule
engine validates.
"""