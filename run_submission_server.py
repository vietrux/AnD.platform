#!/usr/bin/env python3
"""
Run the submission server
"""

import os
import sys

# Setup Django before importing anything else
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameserver.config.settings")

import django

django.setup()

# Now import and run
from gameserver.submission.submission_server import SubmissionServer

if __name__ == "__main__":
    server = SubmissionServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
