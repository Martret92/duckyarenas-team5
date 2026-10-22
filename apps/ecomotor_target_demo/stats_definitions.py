"""Explicit synthetic exercise, never a configuration source for real players."""

from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES
from apps.ecomotor.target_stats_config_validation import validate_target_stats_definition

DEFINITION_VERSION = "persist-stats-demo-2026-10-22-v1"
DEMO_BUDGET = 45
ZERO_BASES = tuple((code, 0) for code in TARGET_STAT_CODES)


def synthetic_definition(option_code, context):
    return validate_target_stats_definition(option_code=option_code,
        catalog_id=context.catalog_id, catalog_version=context.catalog_version,
        definition_version=DEFINITION_VERSION, bases=ZERO_BASES, expected_catalog=context)
