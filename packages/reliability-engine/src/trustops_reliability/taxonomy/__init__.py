"""Canonical failure taxonomy v1 and its strict loader/validator."""

from trustops_reliability.taxonomy.loader import load_taxonomy
from trustops_reliability.taxonomy.validation import TaxonomyValidationError, validate_taxonomy

__all__ = ["TaxonomyValidationError", "load_taxonomy", "validate_taxonomy"]
