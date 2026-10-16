"""JSON temporal ficticio; nunca configura producción."""

from dataclasses import FrozenInstanceError, asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import SimpleTestCase, TestCase

from . import initialization_config as config
from .initialization import ensure_ecomotor_initialized
from .models import CharacterStats, EvolutionEvent, XPEvent
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs
from .xp_service import grant_historical_xp


def candidate_data():
    return {"atk": -2, "def_stat": 3, "log_stat": 4, "spe": 6, "vel": 7, "int_stat": 8,
            "ordered_stage_codes": list(XP_CONFIGURATION.ordered_stage_codes)}


class RuntimeConfigurationTests(SimpleTestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="s6a-json-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "candidate.json"
        self.original = config.INITIAL_CONFIGURATION

    def load(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return config.load_initialization_configuration(self.path)

    def test_valid_json_exact_frozen_dataclass_and_order(self):
        value = self.load(candidate_data())
        self.assertIsInstance(value, config.InitializationConfiguration)
        self.assertEqual(value.atk, -2)  # No rango funcional inventado.
        self.assertEqual(value.ordered_stage_codes, XP_CONFIGURATION.ordered_stage_codes)
        self.assertEqual(set(asdict(value)), set(candidate_data()))
        with self.assertRaises(FrozenInstanceError):
            value.atk = 99

    def test_defensive_copy_of_codes(self):
        data = candidate_data()
        value = config.InitializationConfiguration(**data)
        data["ordered_stage_codes"][0] = "changed"
        self.assertEqual(value.ordered_stage_codes[0], XP_CONFIGURATION.ordered_stage_codes[0])

    def test_loading_never_installs_configuration(self):
        self.load(candidate_data())
        self.assertIs(config.INITIAL_CONFIGURATION, self.original)

    def test_production_reference_has_no_default(self):
        self.assertIsNone(config.INITIAL_CONFIGURATION)

    def test_missing_file_differentiated(self):
        with self.assertRaises(config.ConfigurationFileMissingError):
            config.load_initialization_configuration(self.path)

    def test_file_read_failure_controlled(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("secret path")):
            with self.assertRaises(config.ConfigurationFileError) as raised:
                config.load_initialization_configuration(self.path)
        self.assertNotIn("secret", str(raised.exception))

    def test_syntax_error_differentiated(self):
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(config.ConfigurationSyntaxError):
            config.load_initialization_configuration(self.path)

    def test_excessive_json_integer_is_controlled(self):
        self.path.write_text('{"atk":' + "9" * 5000 + '}', encoding="utf-8")
        with self.assertRaises(config.ConfigurationSyntaxError):
            config.load_initialization_configuration(self.path)

    def test_invalid_utf8_controlled(self):
        self.path.write_bytes(b"\xff")
        with self.assertRaises(config.ConfigurationSyntaxError):
            config.load_initialization_configuration(self.path)

    def test_wrong_roots(self):
        for value in ([], None, 1, "string", True):
            with self.subTest(value=value), self.assertRaises(config.ConfigurationStructureError):
                self.load(value)

    def test_missing_and_unknown_fields(self):
        missing = candidate_data()
        del missing["atk"]
        unknown = candidate_data() | {"rank": 1}
        for value in (missing, unknown):
            with self.subTest(value=value), self.assertRaises(config.ConfigurationStructureError):
                self.load(value)

    def test_duplicate_json_fields_rejected(self):
        self.path.write_text('{"atk":1,"atk":2}', encoding="utf-8")
        with self.assertRaises(config.ConfigurationStructureError):
            config.load_initialization_configuration(self.path)

    def test_each_stat_rejects_bool_string_fraction_null(self):
        for name in ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat"):
            for value in (True, False, "3", 1.5, None):
                with self.subTest(name=name, value=value), self.assertRaises(config.ConfigurationStructureError):
                    self.load(candidate_data() | {name: value})

    def test_technical_integer_bounds(self):
        lower, upper = connection.ops.integer_field_range(CharacterStats._meta.get_field("atk").get_internal_type())
        for boundary in (lower, upper):
            self.assertEqual(self.load(candidate_data() | {"atk": boundary}).atk, boundary)
        for value in (lower - 1, upper + 1):
            with self.assertRaises(config.ConfigurationStructureError):
                self.load(candidate_data() | {"atk": value})

    def test_invalid_stage_sequences(self):
        codes = candidate_data()["ordered_stage_codes"]
        for value in ([], codes[:6], codes + ["extra"], ["same"] * 7,
                      "text", None, [1] * 7, [True] * 7,
                      [""] + codes[1:], ["x" * 33] + codes[1:]):
            with self.subTest(value=value), self.assertRaises(config.ConfigurationStructureError):
                self.load(candidate_data() | {"ordered_stage_codes": value})

    def test_invalid_json_preserves_existing_reference(self):
        existing = config.InitializationConfiguration(**candidate_data())
        with patch.object(config, "INITIAL_CONFIGURATION", existing):
            with self.assertRaises(config.ConfigurationStructureError):
                self.load(candidate_data() | {"atk": True})
            self.assertIs(config.INITIAL_CONFIGURATION, existing)

    def test_network_sources_not_read(self):
        with patch.object(Path, "read_text") as read:
            for source in ("https://example.invalid/config.json", r"\\server\share\config.json"):
                with self.assertRaises(config.ConfigurationFileError):
                    config.load_initialization_configuration(source)
            read.assert_not_called()


class LoadedConfigurationCompatibilityTests(TestCase):
    def test_candidate_explicitly_supplied_to_unchanged_s2_and_s3(self):
        create_xp_catalogs()
        with TemporaryDirectory(prefix="s6a-compat-") as directory:
            source = Path(directory) / "candidate.json"
            source.write_text(json.dumps(candidate_data()), encoding="utf-8")
            value = config.load_initialization_configuration(source)
        self.assertIsNone(config.INITIAL_CONFIGURATION)
        user = get_user_model().objects.create(username="s6a-test-only")
        with patch.object(config, "INITIAL_CONFIGURATION", value):
            first = ensure_ecomotor_initialized(user)
            self.assertTrue(first.created)
            self.assertFalse(XPEvent.objects.exists())
            self.assertFalse(EvolutionEvent.objects.exists())
            from apps.users.models import UserProfileEcomotor
            profile = UserProfileEcomotor.objects.get(pk=first.profile_id)
            result = grant_historical_xp(profile, 51, "s6a-test-key")
            self.assertEqual(result.xp_after, 51)
            self.assertTrue(grant_historical_xp(profile, 51, "s6a-test-key").replayed)
        self.assertIsNone(config.INITIAL_CONFIGURATION)
        self.assertFalse(ensure_ecomotor_initialized(user).created)
