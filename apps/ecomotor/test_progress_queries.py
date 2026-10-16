"""S4-A: proyecciones y snapshots persistidos, sin efectos secundarios."""

from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as IsolatedTestCase
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold,
    Specialization, UserSpecializationProgress, XPEvent,
)
from .progress_queries import (
    GoalState, InconsistentQueryStateError, InvalidHistoryParametersError,
    InvalidQueryProfileError, ProgressQueryDatabaseError,
    get_progress_overview, list_progress_history,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class ProgressQueryTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile()
        self.stats = CharacterStats.objects.get(profile=self.profile)
        UserProfileBank.objects.create(user_id=self.profile.user_id)
        patcher = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        patcher.start()
        self.addCleanup(patcher.stop)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in
                [get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
                 XPEvent, EvolutionEvent, UserSpecializationProgress, Specialization,
                 LevelThreshold, EvolutionStage]]

    def test_initial_overview_returns_exact_persisted_fields(self):
        overview = get_progress_overview(self.profile)
        self.assertEqual((overview.profile_id, overview.historical_xp_total,
                          overview.current_level, overview.current_stage_code),
                         (self.profile.pk, 0, 1, "s3-test-stage-1"))
        self.assertEqual(tuple(getattr(overview, name) for name in
                              ["atk", "def_stat", "log_stat", "spe", "vel", "int_stat"]),
                         (2, 3, 4, 6, 7, 8))
        self.assertEqual(overview.available_points, 7)

    def test_next_level_is_calculable_from_catalog(self):
        target = get_progress_overview(self.profile).next_level
        self.assertEqual(target.state, GoalState.CALCULABLE)
        self.assertEqual((target.level, target.minimum_xp, target.remaining_xp), (2, 11, 11))
        self.assertIsNone(target.stage_code)

    def test_next_stage_is_calculable_with_codes_only(self):
        self.assertIsNone(XP_CONFIGURATION.atk)  # No requiere atributos S2-A válidos.
        target = get_progress_overview(self.profile).next_stage
        self.assertEqual(target.state, GoalState.CALCULABLE)
        self.assertEqual((target.stage_code, target.minimum_xp, target.remaining_xp),
                         ("s3-test-stage-2", 17, 17))
        self.assertIsNone(target.level)

    def test_overview_after_s3_reloads_stale_instance(self):
        grant_historical_xp(self.profile, 51, "query-test-evolved")
        self.assertEqual(self.profile.historical_xp_total, 0)
        overview = get_progress_overview(self.profile)
        self.assertEqual((overview.historical_xp_total, overview.current_level,
                          overview.current_stage_code, overview.available_points),
                         (51, 4, "s3-test-stage-4", 14))
        self.assertEqual(overview.next_level.state, GoalState.COMPLETED)
        self.assertEqual((overview.next_stage.stage_code, overview.next_stage.remaining_xp),
                         ("s3-test-stage-5", 17))

    def test_exact_level_threshold_moves_to_following_level(self):
        grant_historical_xp(self.profile, 11, "query-test-level-threshold")
        overview = get_progress_overview(self.profile)
        self.assertEqual(overview.current_level, 2)
        self.assertEqual((overview.next_level.level, overview.next_level.remaining_xp), (3, 12))

    def test_exact_stage_threshold_moves_to_following_stage(self):
        grant_historical_xp(self.profile, 17, "query-test-stage-threshold")
        overview = get_progress_overview(self.profile)
        self.assertEqual(overview.current_stage_code, "s3-test-stage-2")
        self.assertEqual((overview.next_stage.stage_code, overview.next_stage.remaining_xp),
                         ("s3-test-stage-3", 17))

    def test_last_level_and_stage_are_completed_without_fabricated_target(self):
        grant_historical_xp(self.profile, 102, "query-test-last")
        overview = get_progress_overview(self.profile)
        for target in [overview.next_level, overview.next_stage]:
            self.assertEqual(target.state, GoalState.COMPLETED)
            for name in ["level", "stage_code", "minimum_xp", "remaining_xp"]:
                self.assertIsNone(getattr(target, name))

    def test_basic_overview_and_level_work_without_initial_configuration(self):
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            overview = get_progress_overview(self.profile)
        self.assertEqual(overview.historical_xp_total, 0)
        self.assertEqual(overview.atk, 2)
        self.assertEqual(overview.next_level.state, GoalState.CALCULABLE)
        self.assertEqual(overview.next_stage.state, GoalState.UNAVAILABLE)
        self.assertEqual(overview.next_stage.reason, "STAGE_CONFIGURATION_UNAVAILABLE")
        self.assertIsNone(overview.next_stage.minimum_xp)

    def test_invalid_stage_configuration_does_not_hide_level_or_basic_data(self):
        for config in [object(), replace(XP_CONFIGURATION, ordered_stage_codes=()),
                       replace(XP_CONFIGURATION, ordered_stage_codes=("x",)*7),
                       replace(XP_CONFIGURATION, ordered_stage_codes=tuple(range(7)))]:
            with self.subTest(config=config), patch.object(
                initialization_config, "INITIAL_CONFIGURATION", config,
            ):
                overview = get_progress_overview(self.profile)
                self.assertEqual(overview.next_stage.state, GoalState.UNAVAILABLE)
                self.assertEqual(overview.next_stage.reason, "INVALID_STAGE_CONFIGURATION")
                self.assertEqual(overview.next_level.state, GoalState.CALCULABLE)
                self.assertEqual(overview.available_points, 7)

    def test_empty_level_catalog_is_unavailable_not_completed(self):
        LevelThreshold.objects.all().delete()
        overview = get_progress_overview(self.profile)
        self.assertEqual(overview.next_level.state, GoalState.UNAVAILABLE)
        self.assertEqual(overview.next_level.reason, "INVALID_LEVEL_CATALOG")
        self.assertEqual(overview.next_stage.state, GoalState.CALCULABLE)

    def test_gapped_level_catalog_is_unavailable(self):
        LevelThreshold.objects.filter(level=2).delete()
        target = get_progress_overview(self.profile).next_level
        self.assertEqual(target.state, GoalState.UNAVAILABLE)
        self.assertIsNone(target.minimum_xp)

    def test_nonincreasing_level_thresholds_are_unavailable(self):
        LevelThreshold.objects.filter(level=2).update(minimum_xp=0)
        self.assertEqual(get_progress_overview(self.profile).next_level.state, GoalState.UNAVAILABLE)

    def test_incomplete_and_empty_stage_catalogs_are_unavailable(self):
        EvolutionStage.objects.filter(ordinal=7).delete()
        self.assertEqual(get_progress_overview(self.profile).next_stage.state, GoalState.UNAVAILABLE)
        EvolutionStage.objects.all().delete()
        overview = get_progress_overview(self.profile)
        self.assertEqual(overview.next_stage.state, GoalState.UNAVAILABLE)
        self.assertEqual(overview.next_level.state, GoalState.CALCULABLE)

    def test_nonincreasing_stage_thresholds_are_unavailable(self):
        EvolutionStage.objects.filter(ordinal=2).update(minimum_xp=0)
        self.assertEqual(get_progress_overview(self.profile).next_stage.reason, "INVALID_STAGE_CATALOG")

    def test_wrong_stage_mapping_is_not_inferred_from_rows(self):
        EvolutionStage.objects.filter(ordinal=1).update(code="query-test-unknown")
        self.assertEqual(get_progress_overview(self.profile).next_stage.state, GoalState.UNAVAILABLE)

    def test_structurally_valid_misaligned_progress_is_returned_without_repair(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            current_level=12, current_stage_code="query-test-old-code",
        )
        before = self.snapshot()
        overview = get_progress_overview(self.profile)
        self.assertEqual((overview.current_level, overview.current_stage_code),
                         (12, "query-test-old-code"))
        self.assertEqual(overview.next_level.reason, "LEVEL_STATE_MISMATCH")
        self.assertEqual(overview.next_stage.reason, "STAGE_STATE_MISMATCH")
        self.assertEqual(self.snapshot(), before)

    def test_invalid_or_unsaved_profiles_are_rejected_by_both_services(self):
        for profile in [None, object(), self.profile.pk, UserProfileEcomotor(),
                        UserProfileEcomotor(pk=self.profile.pk)]:
            for query in [get_progress_overview, list_progress_history]:
                with self.subTest(profile=type(profile), query=query), \
                        self.assertRaises(InvalidQueryProfileError):
                    query(profile)

    def test_deleted_profile_is_rejected(self):
        stale = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        self.profile.delete()
        for query in [get_progress_overview, list_progress_history]:
            with self.assertRaises(InvalidQueryProfileError):
                query(stale)

    def test_missing_stats_are_rejected_without_initialization(self):
        self.stats.delete()
        before = self.snapshot()
        for query in [get_progress_overview, list_progress_history]:
            with self.assertRaises(InconsistentQueryStateError):
                query(self.profile)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_profile_code_is_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="x"*33)
        for query in [get_progress_overview, list_progress_history]:
            with self.assertRaises(InconsistentQueryStateError):
                query(self.profile)

    def test_fractional_legacy_fields_are_rejected_without_normalization(self):
        for table, name, pk in [
            ("users_userprofileecomotor", "historical_xp_total", self.profile.pk),
            ("ecomotor_characterstats", "atk", self.stats.pk),
        ]:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {table} SET {name}=%s WHERE id=%s", [1.5, pk])
            before = self.snapshot()
            for query in [get_progress_overview, list_progress_history]:
                with self.subTest(field=name, query=query), \
                        self.assertRaises(InconsistentQueryStateError):
                    query(self.profile)
            self.assertEqual(self.snapshot(), before)
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {table} SET {name}=%s WHERE id=%s", [0, pk])

    def test_fractional_catalog_threshold_is_unavailable_without_normalization(self):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_levelthreshold SET minimum_xp=11.5 WHERE level=2")
        before = self.snapshot()
        self.assertEqual(get_progress_overview(self.profile).next_level.state, GoalState.UNAVAILABLE)
        self.assertEqual(self.snapshot(), before)

    def test_empty_history_has_no_cursor(self):
        page = list_progress_history(self.profile)
        self.assertEqual(page.entries, ())
        self.assertFalse(page.has_more)
        self.assertIsNone(page.next_before_id)

    def test_one_xp_event_without_evolution_returns_only_persisted_fields(self):
        result = grant_historical_xp(self.profile, 3, "query-test-single")
        event = XPEvent.objects.get(pk=result.xp_event_id)
        entry = list_progress_history(self.profile).entries[0]
        self.assertEqual((entry.id, entry.profile_id, entry.operation_key, entry.amount,
                          entry.xp_before, entry.xp_after, entry.created_at, entry.evolutions),
                         (event.pk, self.profile.pk, "query-test-single", 3, 0, 3,
                          event.created_at, ()))
        self.assertEqual({field.name for field in fields(entry)},
                         {"id", "profile_id", "operation_key", "amount", "xp_before",
                          "xp_after", "created_at", "evolutions"})

    def test_multiple_evolutions_preserve_causality_and_order(self):
        result = grant_historical_xp(self.profile, 102, "query-test-jump")
        entry = list_progress_history(self.profile).entries[0]
        stored = list(EvolutionEvent.objects.order_by("pk"))
        self.assertEqual(tuple(row.id for row in entry.evolutions), result.evolution_event_ids)
        self.assertEqual(tuple(row.stage_id for row in entry.evolutions), result.evolved_stage_ids)
        for actual, expected in zip(entry.evolutions, stored):
            self.assertEqual(actual.xp_event_id, entry.id)
            self.assertEqual(actual.created_at, expected.created_at)
            self.assertEqual({field.name for field in fields(actual)},
                             {"id", "xp_event_id", "stage_id", "created_at"})

    def create_history(self, count=5):
        return [grant_historical_xp(self.profile, 1, f"query-test-page-{i}").xp_event_id
                for i in range(count)]

    def test_descending_id_order_is_stable_even_if_timestamps_change(self):
        ids = self.create_history()
        timestamp = XPEvent.objects.first().created_at
        XPEvent.objects.all().update(created_at=timestamp)
        self.assertEqual(tuple(row.id for row in list_progress_history(self.profile).entries),
                         tuple(reversed(ids)))

    def test_cursor_pages_have_no_duplicates_and_report_has_more(self):
        ids = self.create_history()
        first = list_progress_history(self.profile, limit=2)
        self.assertEqual(tuple(row.id for row in first.entries), tuple(reversed(ids[-2:])))
        self.assertTrue(first.has_more)
        self.assertEqual(first.next_before_id, ids[-2])
        second = list_progress_history(self.profile, limit=2, before_id=first.next_before_id)
        self.assertEqual(tuple(row.id for row in second.entries), (ids[2], ids[1]))
        self.assertTrue(second.has_more)
        third = list_progress_history(self.profile, limit=2, before_id=second.next_before_id)
        self.assertEqual(tuple(row.id for row in third.entries), (ids[0],))
        self.assertFalse(third.has_more)
        self.assertIsNone(third.next_before_id)

    def test_exact_limit_has_no_more_or_cursor(self):
        self.create_history(2)
        page = list_progress_history(self.profile, limit=2)
        self.assertEqual(len(page.entries), 2)
        self.assertFalse(page.has_more)
        self.assertIsNone(page.next_before_id)

    def test_cursor_is_exclusive_and_can_produce_empty_page(self):
        ids = self.create_history(3)
        self.assertEqual(tuple(row.id for row in list_progress_history(
            self.profile, before_id=ids[1]).entries), (ids[0],))
        self.assertEqual(list_progress_history(self.profile, before_id=ids[0]).entries, ())
        self.assertEqual(len(list_progress_history(self.profile, before_id=2**80).entries), 3)

    def test_default_and_maximum_limits_are_technical_bounds(self):
        # Fixtures de historial ya persistido; no constituyen concesiones del servicio.
        XPEvent.objects.bulk_create([
            XPEvent(profile=self.profile, amount=1, xp_before=i, xp_after=i+1,
                    operation_key=f"query-test-limit-{i}") for i in range(101)
        ])
        page = list_progress_history(self.profile)
        self.assertEqual(len(page.entries), 50)
        self.assertTrue(page.has_more)
        page = list_progress_history(self.profile, limit=100)
        self.assertEqual(len(page.entries), 100)
        self.assertTrue(page.has_more)

    def test_invalid_limits_are_rejected_before_database_reads(self):
        for value in [0, -1, 101, True, False, 1.0, "2", None]:
            with self.subTest(limit=value), self.assertNumQueries(0), \
                    self.assertRaises(InvalidHistoryParametersError):
                list_progress_history(self.profile, limit=value)

    def test_invalid_cursors_are_rejected_before_database_reads(self):
        for value in [0, -1, True, False, 1.0, "2"]:
            with self.subTest(before_id=value), self.assertNumQueries(0), \
                    self.assertRaises(InvalidHistoryParametersError):
                list_progress_history(self.profile, before_id=value)

    def test_old_snapshots_remain_original_after_new_grants(self):
        first = grant_historical_xp(self.profile, 17, "query-test-old")
        grant_historical_xp(self.profile, 85, "query-test-new")
        entries = list_progress_history(self.profile).entries
        self.assertEqual([(row.xp_before, row.xp_after) for row in entries], [(17, 102), (0, 17)])
        self.assertEqual(entries[-1].id, first.xp_event_id)

    def test_history_ignores_missing_configuration_and_level_catalog(self):
        grant_historical_xp(self.profile, 3, "query-test-no-config")
        LevelThreshold.objects.all().delete()
        EvolutionStage.objects.all().delete()  # Sin evoluciones referenciadas en esta fixture.
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            page = list_progress_history(self.profile)
        self.assertEqual(page.entries[0].xp_after, 3)

    def test_stage_renaming_does_not_fabricate_historical_snapshots(self):
        result = grant_historical_xp(self.profile, 51, "query-test-renamed")
        EvolutionStage.objects.filter(ordinal=2).update(code="query-test-renamed-code", name="Nuevo nombre")
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), \
                CaptureQueriesContext(connection) as queries:
            entry = list_progress_history(self.profile).entries[0]
        self.assertEqual(tuple(row.stage_id for row in entry.evolutions), result.evolved_stage_ids)
        self.assertFalse(hasattr(entry.evolutions[0], "stage_code"))
        sql = " ".join(row["sql"].lower() for row in queries)
        self.assertNotIn('"ecomotor_evolutionstage"', sql)
        self.assertNotIn('"ecomotor_levelthreshold"', sql)

    def test_other_profile_events_are_not_returned(self):
        mine = grant_historical_xp(self.profile, 3, "query-test-mine")
        other = create_xp_profile(username="query-test-other")
        grant_historical_xp(other, 51, "query-test-other-key")
        page = list_progress_history(self.profile)
        self.assertEqual(tuple(row.id for row in page.entries), (mine.xp_event_id,))
        self.assertTrue(all(row.profile_id == self.profile.pk for row in page.entries))

    def test_evolution_with_other_profile_and_own_cause_is_rejected(self):
        result = grant_historical_xp(self.profile, 17, "query-test-bad-cause")
        other = create_xp_profile(username="query-test-other-cause")
        EvolutionEvent.objects.filter(xp_event_id=result.xp_event_id).update(profile=other)
        before = self.snapshot()
        with self.assertRaises(InconsistentQueryStateError):
            list_progress_history(self.profile)
        self.assertEqual(self.snapshot(), before)

    def test_own_evolution_with_foreign_cause_is_rejected_without_leaking_history(self):
        other = create_xp_profile(username="query-test-foreign-cause")
        result = grant_historical_xp(other, 17, "query-test-foreign")
        EvolutionEvent.objects.filter(xp_event_id=result.xp_event_id).update(profile=self.profile)
        with self.assertRaises(InconsistentQueryStateError):
            list_progress_history(self.profile)

    def test_fractional_historical_snapshots_are_rejected_without_normalization(self):
        result = grant_historical_xp(self.profile, 3, "query-test-legacy-event")
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_xpevent SET amount=1, xp_before=1.5, xp_after=2.5 WHERE id=%s",
                           [result.xp_event_id])
        before = self.snapshot()
        with self.assertRaises(InconsistentQueryStateError):
            list_progress_history(self.profile)
        self.assertEqual(self.snapshot(), before)

    def test_evolution_loading_has_constant_query_count_not_n_plus_one(self):
        grant_historical_xp(self.profile, 17, "query-test-first-evolution")
        with self.assertNumQueries(5):
            first = list_progress_history(self.profile)
        grant_historical_xp(self.profile, 85, "query-test-more-evolutions")
        with self.assertNumQueries(5):
            second = list_progress_history(self.profile)
        self.assertEqual(len(first.entries), 1)
        self.assertEqual(sum(len(row.evolutions) for row in second.entries), 6)

    def test_queries_only_select_without_writes_locks_or_external_user_reads(self):
        grant_historical_xp(self.profile, 51, "query-test-read-only")
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            get_progress_overview(self.profile)
            list_progress_history(self.profile)
        self.assertTrue(queries.captured_queries)
        self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT ") for row in queries))
        sql = " ".join(row["sql"].lower() for row in queries)
        self.assertNotIn('"auth_user"', sql)
        self.assertNotIn('"users_userprofilebank"', sql)
        self.assertEqual(self.snapshot(), before)

    def test_database_failures_are_explicit_not_unavailable(self):
        def broken(execute, sql, params, many, context):
            if '"ecomotor_levelthreshold"' in sql:
                raise OperationalError("test database failure")
            return execute(sql, params, many, context)

        with connection.execute_wrapper(broken), self.assertRaises(ProgressQueryDatabaseError) as caught:
            get_progress_overview(self.profile)
        self.assertIsInstance(caught.exception.__cause__, OperationalError)
        with patch("apps.ecomotor.progress_queries.XPEvent.objects.using",
                   side_effect=OperationalError("test history failure")), \
                self.assertRaises(ProgressQueryDatabaseError):
            list_progress_history(self.profile)

    def test_programming_errors_are_not_hidden_as_unavailable(self):
        with patch("apps.ecomotor.progress_queries.validate_level_catalog", side_effect=RuntimeError("test bug")), \
                self.assertRaisesRegex(RuntimeError, "test bug"):
            get_progress_overview(self.profile)

    def test_all_returned_structures_are_immutable(self):
        grant_historical_xp(self.profile, 17, "query-test-immutable")
        overview = get_progress_overview(self.profile)
        page = list_progress_history(self.profile)
        for obj, name, value in [(overview, "current_level", 99),
                                 (overview.next_level, "remaining_xp", 99),
                                 (page, "has_more", True),
                                 (page.entries[0], "amount", 99),
                                 (page.entries[0].evolutions[0], "stage_id", 99)]:
            with self.subTest(obj=type(obj)), self.assertRaises(FrozenInstanceError):
                setattr(obj, name, value)
        self.assertIsInstance(page.entries, tuple)
        self.assertIsInstance(page.entries[0].evolutions, tuple)


class ProgressQueryAliasTests(IsolatedTestCase):
    """Alias temporal independiente: verifica routing sin alterar la BD habitual."""

    def test_services_use_profile_database_alias(self):
        with TemporaryDirectory(prefix="ducky-s4a-alias-") as directory:
            alias = "s4a_query_test"
            config = connections["default"].settings_dict.copy()
            config["NAME"] = str(Path(directory) / "test.sqlite3")
            config["OPTIONS"] = config["OPTIONS"].copy()
            connections.databases[alias] = config
            database = connections[alias]
            try:
                executor = MigrationExecutor(database)
                executor.migrate(executor.loader.graph.leaf_nodes())
                create_xp_catalogs(alias)
                profile = create_xp_profile(alias)
                with patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION):
                    granted = grant_historical_xp(profile, 51, "query-test-alias")

                    def no_default_queries(*args):
                        raise AssertionError("La consulta intentó usar default.")

                    with connections["default"].execute_wrapper(no_default_queries), \
                            CaptureQueriesContext(database) as queries:
                        overview = get_progress_overview(profile)
                        history = list_progress_history(profile)
                self.assertEqual(overview.historical_xp_total, 51)
                self.assertEqual(overview.next_stage.stage_code, "s3-test-stage-5")
                self.assertEqual(history.entries[0].id, granted.xp_event_id)
                self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT ") for row in queries))
            finally:
                database.close()
                del connections[alias]
                del connections.databases[alias]
