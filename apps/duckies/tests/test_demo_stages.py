from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from apps.ecomotor.models import EvolutionStage
from apps.duckies.models import EvolutionItem


@override_settings(DEBUG=True)
class DemoStagesCommandTests(TestCase):
    def test_create_idempotent_and_cleanup(self):
        call_command("prepare_duckies_demo_stages", verbosity=0)
        self.assertEqual(EvolutionStage.objects.count(), 7)
        call_command("prepare_duckies_demo_stages", verbosity=0)
        self.assertEqual(EvolutionStage.objects.count(), 7)
        call_command("prepare_duckies_demo_stages", "--cleanup", verbosity=0)
        self.assertEqual(EvolutionStage.objects.count(), 0)

    def test_dry_run_does_not_create(self):
        call_command("prepare_duckies_demo_stages", "--dry-run", verbosity=0)
        self.assertFalse(EvolutionStage.objects.exists())

    def test_does_not_modify_existing_official_stage(self):
        EvolutionStage.objects.create(code="OFFICIAL", name="Official", ordinal=1, minimum_xp=0)
        with self.assertRaises(CommandError):
            call_command("prepare_duckies_demo_stages", verbosity=0)
        self.assertEqual(EvolutionStage.objects.count(), 1)

    def test_cleanup_refuses_if_outfit_exists(self):
        call_command("prepare_duckies_demo_stages", verbosity=0)
        call_command("seed_duckies", verbosity=0)
        self.assertEqual(EvolutionItem.objects.count(), 7)
        with self.assertRaises(CommandError):
            call_command("prepare_duckies_demo_stages", "--cleanup", verbosity=0)
        self.assertEqual(EvolutionStage.objects.count(), 7)

    @override_settings(DEBUG=False)
    def test_disabled_outside_debug(self):
        with self.assertRaises(CommandError):
            call_command("prepare_duckies_demo_stages", verbosity=0)
