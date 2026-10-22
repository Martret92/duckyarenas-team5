"""Fictitious values for this demonstration, not official configuration."""

CATALOG_ID = "synthetic-persistent-target-demo"
VERSION = "persist-demo-2026-10-22-v1"
THRESHOLDS = (0, 100, 200, 300, 400, 500, 600, 700, 900)
NAMES = ("Prehistórico", "Griego", "Romano", "Medieval", "Renacentista",
         "Revolución Industrial", "Siglo XX")
CODES = tuple(f"persist-demo-epoch-{n}" for n in range(1, 8))
OPTIONS = NAMES + ("Developer", "Ciber", "Sistemas", "Data IA", "Gamer")
MAX_XP = 2**63 - 1  # SQLite signed INTEGER storage bound, not a game rule.
