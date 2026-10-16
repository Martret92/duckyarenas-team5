from dataclasses import FrozenInstanceError
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as IsolatedTestCase
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config as config
from .configuration_checks import ReadinessDatabaseError, ReadinessStatus as S, check_ecomotor_readiness
from .models import CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent
from .test_runtime_configuration import candidate_data
from .test_xp_service import create_xp_catalogs, create_xp_profile


class ConfigurationCheckTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.config = config.InitializationConfiguration(**candidate_data())

    def check(self):
        return check_ecomotor_readiness(configuration=self.config)

    def test_missing_configuration(self):
        self.assertEqual(check_ecomotor_readiness(configuration=None).status, S.CONFIGURATION_MISSING)

    def test_process_reference_is_read_at_call_time(self):
        with patch.object(config, "INITIAL_CONFIGURATION", self.config):
            self.assertEqual(check_ecomotor_readiness().status, S.TECHNICALLY_READY)
        with patch.object(config, "INITIAL_CONFIGURATION", None):
            self.assertEqual(check_ecomotor_readiness().status, S.CONFIGURATION_MISSING)

    def test_invalid_configuration(self):
        for value in (object(), {}, config.InitializationConfiguration(**(candidate_data() | {"atk": True})),
                      config.InitializationConfiguration(**(candidate_data() | {"ordered_stage_codes": []}))):
            with self.subTest(value=value):
                self.assertEqual(check_ecomotor_readiness(configuration=value).status, S.INVALID_CONFIGURATION)

    def test_empty_level_catalog_incomplete(self):
        LevelThreshold.objects.all().delete()
        self.assertEqual(self.check().status, S.CATALOG_INCOMPLETE)

    def test_incomplete_stage_catalog(self):
        EvolutionStage.objects.filter(ordinal=4).delete()
        self.assertEqual(self.check().status, S.CATALOG_INCOMPLETE)

    def test_one_initial_level_is_complete(self):
        LevelThreshold.objects.exclude(level=1).delete()
        self.assertEqual(self.check().status, S.TECHNICALLY_READY)

    def test_gaps_in_levels_invalid(self):
        LevelThreshold.objects.filter(level=2).delete()
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_missing_first_level_invalid(self):
        LevelThreshold.objects.filter(level=1).delete()
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_nonzero_initial_threshold_invalid(self):
        LevelThreshold.objects.filter(level=1).update(minimum_xp=1)
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_nonincreasing_level_thresholds_invalid(self):
        LevelThreshold.objects.filter(level=2).update(minimum_xp=0)
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_nonincreasing_stage_thresholds_invalid(self):
        EvolutionStage.objects.filter(ordinal=2).update(minimum_xp=0)
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_incompatible_stage_codes(self):
        EvolutionStage.objects.filter(ordinal=2).update(code="different-fictitious-code")
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_invalid_partial_stages_not_just_incomplete(self):
        EvolutionStage.objects.filter(ordinal=7).delete()
        EvolutionStage.objects.filter(ordinal=1).update(minimum_xp=2)
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_invalid_row_rejected(self):
        EvolutionStage.objects.filter(ordinal=1).update(name="x" * 101)
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_fractional_persisted_numbers_not_normalized(self):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_levelthreshold SET minimum_xp = 1.5 WHERE level = 2")
        self.assertEqual(self.check().status, S.INVALID_CATALOG)

    def test_ready_is_technical_not_functional_and_frozen(self):
        result = self.check()
        self.assertEqual(result.status, S.TECHNICALLY_READY)
        self.assertTrue(result.technically_consistent)
        self.assertEqual(result.issues, ())
        self.assertFalse(hasattr(result, "approved"))
        with self.assertRaises(FrozenInstanceError):
            result.status = S.INVALID_CONFIGURATION

    def test_deterministic_precedence(self):
        LevelThreshold.objects.all().delete()
        EvolutionStage.objects.filter(ordinal=1).update(minimum_xp=1)
        self.assertEqual(self.check().status, S.INVALID_CATALOG)
        self.assertEqual([i.code for i in self.check().issues], ["LEVELS_MISSING", "INVALID_STAGES"])
        self.assertEqual(check_ecomotor_readiness(configuration={}).status, S.INVALID_CONFIGURATION)
        self.assertEqual(check_ecomotor_readiness(configuration=None).status, S.CONFIGURATION_MISSING)

    def test_invalid_configuration_does_not_query_catalogs(self):
        with self.assertNumQueries(0):
            check_ecomotor_readiness(configuration={})
            check_ecomotor_readiness(configuration=None)

    def test_database_failure_explicit_with_cause(self):
        with patch("apps.ecomotor.configuration_checks.LevelThreshold.objects.using",
                   side_effect=OperationalError("private failure")), self.assertRaises(ReadinessDatabaseError) as raised:
            self.check()
        self.assertIsInstance(raised.exception.__cause__, OperationalError)
        self.assertNotIn("private", str(raised.exception))

    def test_invalid_alias_is_operational_error(self):
        with self.assertRaises(ReadinessDatabaseError):
            check_ecomotor_readiness(configuration=None, using="not-configured")

    def test_programming_error_not_misclassified(self):
        with patch("apps.ecomotor.configuration_checks.validate_level_catalog", side_effect=RuntimeError("bug")):
            with self.assertRaisesRegex(RuntimeError, "bug"):
                self.check()

    def test_diagnostic_only_select_preserves_all_records(self):
        profile = create_xp_profile()
        UserProfileBank.objects.create(user=profile.user)
        models = (get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
                  XPEvent, EvolutionEvent, LevelThreshold, EvolutionStage)
        before = [list(m.objects.values()) for m in models]
        with CaptureQueriesContext(connection) as queries:
            self.check()
        self.assertEqual(len(queries), 2)
        self.assertTrue(all(q["sql"].upper().startswith("SELECT") for q in queries))
        self.assertEqual(before, [list(m.objects.values()) for m in models])

    def test_command_without_config_reports_missing_code_two(self):
        output = StringIO()
        with patch.object(config, "INITIAL_CONFIGURATION", None), self.assertRaises(CommandError) as raised:
            call_command("check_ecomotor_readiness", stdout=output)
        self.assertEqual(raised.exception.returncode, 2)
        self.assertIn("CONFIGURATION_MISSING", output.getvalue())
        self.assertIn("Aprobación funcional independiente", output.getvalue())

    def test_command_current_reference_ready(self):
        output = StringIO()
        with patch.object(config, "INITIAL_CONFIGURATION", self.config):
            call_command("check_ecomotor_readiness", stdout=output)
        self.assertIn("TECHNICALLY_READY", output.getvalue())
        self.assertIn("No se guarda ni activa", output.getvalue())

    def test_command_config_candidate_and_no_writes_or_activation(self):
        with TemporaryDirectory(prefix="s6a-command-") as directory:
            source = Path(directory) / "test.json"
            source.write_text(json.dumps(candidate_data()), encoding="utf-8")
            output = StringIO()
            with CaptureQueriesContext(connection) as queries:
                call_command("check_ecomotor_readiness", config=str(source), database="default", stdout=output)
        self.assertIn("TECHNICALLY_READY", output.getvalue())
        self.assertIsNone(config.INITIAL_CONFIGURATION)
        self.assertTrue(all(q["sql"].upper().startswith("SELECT") for q in queries))

    def test_command_invalid_and_missing_json_code_two(self):
        with TemporaryDirectory(prefix="s6a-command-") as directory:
            source = Path(directory) / "test.json"
            for content in (None, "{bad", "{}"):
                if content is not None:
                    source.write_text(content, encoding="utf-8")
                with self.assertRaises(CommandError) as raised:
                    call_command("check_ecomotor_readiness", config=str(source), stdout=StringIO())
                self.assertEqual(raised.exception.returncode, 2)
                self.assertNotIn(str(source), str(raised.exception))

    def test_command_incomplete_diagnostic_code_two(self):
        EvolutionStage.objects.all().delete()
        with patch.object(config, "INITIAL_CONFIGURATION", self.config), self.assertRaises(CommandError) as raised:
            call_command("check_ecomotor_readiness", stdout=StringIO())
        self.assertEqual(raised.exception.returncode, 2)

    def test_command_database_error_code_three(self):
        with self.assertRaises(CommandError) as raised:
            call_command("check_ecomotor_readiness", database="not-configured", stdout=StringIO())
        self.assertEqual(raised.exception.returncode, 3)

    def test_command_file_access_failure_code_three(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("secret")):
            with self.assertRaises(CommandError) as raised:
                call_command("check_ecomotor_readiness", config="unused", stdout=StringIO())
        self.assertEqual(raised.exception.returncode, 3)
        self.assertNotIn("secret", str(raised.exception))


class ReadinessAliasTests(IsolatedTestCase):
    def test_diagnostic_and_command_use_explicit_alias(self):
        with TemporaryDirectory(prefix="s6a-alias-") as directory:
            alias = "s6a_readiness_test"
            settings = connections["default"].settings_dict.copy()
            settings["NAME"] = str(Path(directory) / "test.sqlite3")
            connections.databases[alias] = settings
            database = connections[alias]
            try:
                executor = MigrationExecutor(database)
                executor.migrate(executor.loader.graph.leaf_nodes())
                create_xp_catalogs(alias)
                candidate = config.InitializationConfiguration(**candidate_data())

                def forbid_default(*args):
                    raise AssertionError("default no permitido")

                with connections["default"].execute_wrapper(forbid_default), CaptureQueriesContext(database) as queries:
                    result = check_ecomotor_readiness(configuration=candidate, using=alias)
                    output = StringIO()
                    with patch.object(config, "INITIAL_CONFIGURATION", candidate):
                        call_command("check_ecomotor_readiness", database=alias, stdout=output)
                self.assertEqual(result.status, S.TECHNICALLY_READY)
                self.assertIn("TECHNICALLY_READY", output.getvalue())
                self.assertTrue(all(q["sql"].upper().startswith("SELECT") for q in queries))
            finally:
                database.close()
                del connections[alias]
                del connections.databases[alias]
