#!/usr/bin/env python3
import argparse
import json
import os

from config import JSON_FILE, SQL_FILE
from generator import Generator

CYCLING_ACTIVITY_TYPES = {"cycling"}


def run_strava_sync(client_id, client_secret, refresh_token):
    generator = Generator(SQL_FILE)
    generator.set_strava_config(client_id, client_secret, refresh_token)
    generator.activity_types = CYCLING_ACTIVITY_TYPES
    generator.sync(False)

    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", nargs="?", help="strava client id")
    parser.add_argument("client_secret", nargs="?", help="strava client secret")
    parser.add_argument("refresh_token", nargs="?", help="strava refresh token")
    options = parser.parse_args(argv)

    options.client_id = options.client_id or os.getenv("STRAVA_CLIENT_ID")
    options.client_secret = options.client_secret or os.getenv("STRAVA_CLIENT_SECRET")
    options.refresh_token = options.refresh_token or os.getenv(
        "STRAVA_CLIENT_REFRESH_TOKEN"
    )
    missing = [
        name
        for name in ("client_id", "client_secret", "refresh_token")
        if not getattr(options, name)
    ]
    if missing:
        parser.error(
            "missing Strava credentials: "
            + ", ".join(missing)
            + " (pass positional arguments or set STRAVA_* environment variables)"
        )
    return options


if __name__ == "__main__":
    options = parse_args()
    run_strava_sync(
        options.client_id,
        options.client_secret,
        options.refresh_token,
    )
