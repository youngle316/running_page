import datetime
import sys
from pathlib import Path
from types import SimpleNamespace

RUN_PAGE_DIR = Path(__file__).parent / "run_page"
sys.path.insert(0, str(RUN_PAGE_DIR))

import gen_svg
import generator as generator_module
import strava_sync
import strava_web_sync
from activity_filter import activity_matches_types
from generator import Generator
from generator.db import Activity


def test_cycling_filter_accepts_strava_ride_subtypes():
    for sport_type in (
        "Ride",
        "VirtualRide",
        "GravelRide",
        "MountainBikeRide",
        "EMountainBikeRide",
        "EBikeRide",
    ):
        activity = SimpleNamespace(type="Ride", sport_type=sport_type, subtype="Ride")
        assert activity_matches_types(activity, {"cycling"})

    assert not activity_matches_types(
        SimpleNamespace(type="Run", sport_type="TrailRun", subtype="Run"),
        {"cycling"},
    )
    assert not activity_matches_types(
        SimpleNamespace(type="Ride", sport_type="Walk", subtype="Walk"),
        {"cycling"},
    )
    assert not activity_matches_types(
        SimpleNamespace(type="Run", subtype="Run", sport_type=""),
        {"cycling"},
    )


def test_strava_sync_only_saves_selected_activity_types(tmp_path, monkeypatch):
    generator = Generator(tmp_path / "activities.db")
    ride = SimpleNamespace(
        id=1,
        type="Ride",
        sport_type="GravelRide",
        map=None,
        total_elevation_gain=100,
    )
    run = SimpleNamespace(id=2, type="Run", sport_type="Run", subtype="Run")
    requested_filters = []
    generator.client = SimpleNamespace(
        get_activities=lambda **filters: requested_filters.append(filters)
        or [ride, run]
    )
    generator.activity_types = {"cycling"}
    generator.session.add(
        Activity(run_id=99, type="Run", start_date="2025-01-01 00:00:00")
    )
    generator.session.commit()

    saved = []
    monkeypatch.setattr(generator, "check_access", lambda: None)
    monkeypatch.setattr(
        generator_module,
        "update_or_create_activity",
        lambda session, activity: saved.append(activity.id) or True,
    )

    generator.sync(False)

    assert saved == [1]
    assert "before" in requested_filters[0]


def test_database_export_excludes_historical_non_cycling_rows(tmp_path, monkeypatch):
    generator = Generator(tmp_path / "activities.db")
    common = {
        "distance": 10_000,
        "moving_time": datetime.timedelta(hours=1),
        "elapsed_time": datetime.timedelta(hours=1),
        "start_date": "2024-01-01 00:00:00",
        "location_country": "",
        "summary_polyline": "",
        "average_heartrate": 120,
        "average_speed": 3,
        "elevation_gain": 50,
    }
    generator.session.add_all(
        [
            Activity(
                run_id=1,
                name="Historical run",
                type="Run",
                subtype="Run",
                start_date_local="2024-01-01 08:00:00",
                **common,
            ),
            Activity(
                run_id=2,
                name="Historical ride",
                type="Ride",
                subtype="MountainBikeRide",
                start_date_local="2024-01-02 08:00:00",
                **common,
            ),
        ]
    )
    generator.session.commit()
    generator.activity_types = {"cycling"}
    monkeypatch.setattr(generator_module, "filter_out", lambda polyline: polyline)

    exported = generator.load()

    assert [activity["run_id"] for activity in exported] == [2]
    assert exported[0]["sport_type"] == "MountainBikeRide"


def test_strava_sync_is_locked_to_cycling(tmp_path, monkeypatch):
    captured_types = []

    class FakeGenerator:
        def __init__(self, db_path):
            self.activity_types = set()

        def set_strava_config(self, client_id, client_secret, refresh_token):
            pass

        def sync(self, force):
            captured_types.append(self.activity_types)

        def load(self):
            return []

    monkeypatch.setattr(strava_sync, "Generator", FakeGenerator)
    monkeypatch.setattr(strava_sync, "JSON_FILE", tmp_path / "activities.json")

    strava_sync.run_strava_sync("id", "secret", "refresh")

    assert captured_types == [{"cycling"}]

    try:
        strava_sync.parse_args(["id", "secret", "refresh", "--only-run"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("running-only CLI options must be rejected")


def test_sync_watermark_uses_filtered_scalar_query_and_skips_bad_dates(tmp_path):
    generator = Generator(tmp_path / "activities.db")
    generator.session.add_all(
        [
            Activity(
                run_id=1,
                type="Run",
                subtype="Run",
                start_date="2099-01-01 00:00:00",
            ),
            Activity(
                run_id=2,
                type="Ride",
                subtype="Ride",
                start_date="not-a-date",
            ),
            Activity(
                run_id=3,
                type="Ride",
                subtype="GravelRide",
                start_date="2025-03-04 05:06:07",
            ),
            Activity(run_id=4, type="Ride", subtype="Ride", start_date=""),
        ]
    )
    generator.session.commit()
    generator.activity_types = {"cycling"}

    watermark = generator._latest_activity_date()

    assert watermark.format("YYYY-MM-DD HH:mm:ss") == "2025-03-04 05:06:07"


def test_export_tolerates_invalid_local_date(tmp_path, monkeypatch):
    generator = Generator(tmp_path / "activities.db")
    generator.activity_types = {"cycling"}
    generator.session.add(
        Activity(
            run_id=1,
            name="Legacy ride",
            distance=1000,
            moving_time=datetime.timedelta(minutes=5),
            elapsed_time=datetime.timedelta(minutes=5),
            type="Ride",
            subtype="Ride",
            start_date="bad",
            start_date_local="bad",
            location_country="",
            summary_polyline="",
            average_speed=3,
            elevation_gain=0,
        )
    )
    generator.session.commit()
    monkeypatch.setattr(generator_module, "filter_out", lambda value: value)

    assert [activity["run_id"] for activity in generator.load()] == [1]


def test_strava_web_sync_and_export_only_cycling(tmp_path, monkeypatch):
    original_finalize = strava_web_sync._finalize
    synced = []
    finalized = []
    models = [
        {"id": 1, "sport_type": "Run", "start_date_local_raw": 0},
        {"id": 2, "sport_type": "GravelRide", "start_date_local_raw": 0},
    ]
    monkeypatch.setattr(strava_web_sync, "WebClient", lambda jwt: object())
    monkeypatch.setattr(strava_web_sync, "init_db", lambda path: object())
    monkeypatch.setattr(
        strava_web_sync,
        "_fetch_json",
        lambda client, url: {"models": models, "total": 1},
    )
    monkeypatch.setattr(
        strava_web_sync,
        "_sync_one",
        lambda client, session, raw: synced.append(raw["id"]),
    )
    monkeypatch.setattr(
        strava_web_sync,
        "_finalize",
        lambda session, count: finalized.append(count) or count,
    )

    count = strava_web_sync.run_strava_web_sync("jwt")

    assert count == 1
    assert synced == [2]
    assert finalized == [1]

    db_path = tmp_path / "web.db"
    output_path = tmp_path / "activities.json"
    generator = Generator(db_path)
    generator.session.add_all(
        [
            Activity(run_id=10, type="Run", subtype="Run", distance=1000),
            Activity(run_id=11, type="Ride", subtype="Ride", distance=1000),
        ]
    )
    generator.session.commit()
    monkeypatch.setattr(strava_web_sync, "SQL_FILE", db_path)
    monkeypatch.setattr(strava_web_sync, "JSON_FILE", output_path)
    monkeypatch.setattr(generator_module, "filter_out", lambda value: value)
    original_finalize(object(), 1)

    assert '"run_id": 11' in output_path.read_text()
    assert '"run_id": 10' not in output_path.read_text()


def test_svg_filter_is_locked_to_consistent_cycling_tracks():
    tracks = [
        SimpleNamespace(type="Run", subtype="Run"),
        SimpleNamespace(type="Ride", subtype="Ride"),
        SimpleNamespace(type="Workout", sport_type="MountainBikeRide", subtype=""),
        SimpleNamespace(type="Run", sport_type="Ride", subtype="Ride"),
    ]

    assert gen_svg.filter_tracks_by_sport(tracks) == tracks[1:3]

    try:
        gen_svg.filter_tracks_by_sport(tracks, "all")
    except gen_svg.ParameterError as error:
        assert "only supports cycling" in str(error)
    else:
        raise AssertionError("non-cycling poster filters must fail")


def test_workflow_db_svg_commands_are_cycling_only():
    workflow = (
        Path(__file__).parent / ".github/workflows/run_data_sync.yml"
    ).read_text()
    commands = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith("python run_page/gen_svg.py --from-db")
        and not line.lstrip().startswith("#")
    ]

    assert commands
    assert all("--sport-type cycling" in command for command in commands)
