#!/usr/bin/env python3
"""
Run the tick manager
"""

import os
import sys

# Setup Django before importing anything else
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameserver.config.settings")

import django

django.setup()

# Now import and run
from gameserver.controller.tick_manager import TickManager

if __name__ == "__main__":
    manager = TickManager()
    try:
        manager.start()
    except KeyboardInterrupt:
        manager.stop()
