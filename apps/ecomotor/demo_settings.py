"""Opt-in local demo: bind runserver explicitly to 127.0.0.1."""

from config.settings import *  # noqa: F403


ROOT_URLCONF = "apps.ecomotor.demo_urls"
