#!/usr/bin/env python
"""Ponto de entrada do Django. Criado com auxílio de IA; ver AI_USAGE.md."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)
