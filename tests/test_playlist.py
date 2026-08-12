"""Unit tests for PlaylistManager."""

import pytest
from termtune.models.track import Track
from termtune.playlist.manager import PlaylistManager


@pytest.fixture
def sample_track():
    return Track(
        id="t1",
        title="Test Song",
        artist="Test Artist",
        duration=180,
        webpage_url="http://test.com",
    )


def test_playlist_creation_and_add_track(tmp_path, sample_track):
    pm = PlaylistManager(storage_dir=tmp_path)
    assert pm.list_playlists() == []

    # Create playlist
    assert pm.create_playlist("Favorites") is True
    assert pm.list_playlists() == ["favorites"]

    # Add track
    ok, msg = pm.add_track("Favorites", sample_track)
    assert ok is True

    # Duplicate track addition should fail
    ok_dup, msg_dup = pm.add_track("Favorites", sample_track)
    assert ok_dup is False

    # Load playlist
    tracks = pm.load_playlist("Favorites")
    assert len(tracks) == 1
    assert tracks[0].title == "Test Song"


def test_playlist_remove_and_delete(tmp_path, sample_track):
    pm = PlaylistManager(storage_dir=tmp_path)
    pm.create_playlist("Workout")
    pm.add_track("Workout", sample_track)

    assert len(pm.load_playlist("Workout")) == 1

    # Remove track
    assert pm.remove_track("Workout", sample_track.id) is True
    assert len(pm.load_playlist("Workout")) == 0

    # Delete playlist
    assert pm.delete_playlist("Workout") is True
    assert pm.list_playlists() == []
