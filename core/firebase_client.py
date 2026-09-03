"""
core/firebase_client.py

Initializes Firebase Admin SDK once at import time and exposes a
shared Firestore client for tools to use (e.g. tournament_tools.py).

CREDENTIALS - two ways this can find them, checked in order:

1. Local dev: a JSON key file on disk. Set FIREBASE_CREDENTIALS_PATH
   in your .env to point at it, e.g.:
       FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
   (relative paths are resolved from the Cortex project root)

2. Production (Render): no file on disk, so instead put the FULL
   JSON content of the key file into a Render environment variable
   named FIREBASE_CREDENTIALS_JSON (paste the whole file content as
   the value). This file reads that instead.

Never commit the JSON key file or paste its contents into chat/logs -
it's a master credential for your whole Firebase project.
"""

from __future__ import annotations

import json
import os

import firebase_admin
from firebase_admin import credentials, firestore

_app = None
_db = None


def _load_credentials():
    json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if json_env:
        info = json.loads(json_env)
        return credentials.Certificate(info)

    path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-service-account.json")
    if not os.path.isabs(path):
        # Resolve relative to the Cortex project root (two levels up
        # from this file: core/firebase_client.py -> project root).
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(project_root, path)

    if not os.path.exists(path):
        raise RuntimeError(
            "No Firebase credentials found. Set FIREBASE_CREDENTIALS_JSON "
            "(production) or make sure FIREBASE_CREDENTIALS_PATH points at "
            "a valid service account file (local dev)."
        )

    return credentials.Certificate(path)


def get_firestore_client():
    """Returns a shared Firestore client, initializing Firebase Admin
    on first call. Safe to call repeatedly - subsequent calls reuse
    the same app/client instead of re-initializing."""
    global _app, _db

    if _db is not None:
        return _db

    if not firebase_admin._apps:
        cred = _load_credentials()
        _app = firebase_admin.initialize_app(cred)
    else:
        _app = firebase_admin.get_app()

    _db = firestore.client()
    return _db