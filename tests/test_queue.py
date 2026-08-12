"""Unit tests for QueueManager with strict duplicate prevention and persistence."""

import pytest
from termtune.models.track import Track
from termtune.queue.manager import QueueManager


@pytest.fixture
def sample_tracks():
    return [
        Track(id="1", title="Song A", artist="Artist A", duration=180, webpage_url="http://a.com"),
        Track(id="2", title="Song B", artist="Artist B", duration=200, webpage_url="http://b.com"),
        Track(id="3", title="Song C", artist="Artist C", duration=220, webpage_url="http://c.com"),
    ]


def test_queue_add_and_count(sample_tracks):
    qm = QueueManager()
    assert qm.is_empty()
    assert qm.count() == 0

    qm.add(sample_tracks[0])
    qm.add(sample_tracks[1])
    assert qm.count() == 2
    assert qm.items[0].title == "Song A"


def test_queue_duration_and_duplicates(sample_tracks):
    qm = QueueManager()
    qm.add(sample_tracks[0])  # 180s (idx 0)
    qm.add(sample_tracks[1])  # 200s (idx 1)
    assert qm.total_duration == 380

    # Strict duplicate prevention blocks addition and returns existing index 0
    idx, is_dup = qm.add(sample_tracks[0])
    assert is_dup is True
    assert idx == 0
    assert qm.count() == 2


def test_queue_add_next(sample_tracks):
    qm = QueueManager()
    qm.add(sample_tracks[0])  # idx 0
    qm.add(sample_tracks[2])  # idx 1
    qm.set_current_index(0)

    idx, is_dup = qm.add_next(sample_tracks[1])
    assert idx == 1
    assert qm.items[1].title == "Song B"


def test_queue_persistence(tmp_path, sample_tracks):
    file_path = tmp_path / "test_queue.json"
    qm1 = QueueManager()
    for t in sample_tracks:
        qm1.add(t)
    qm1.set_current_index(1)
    qm1.save_state(file_path)

    qm2 = QueueManager()
    qm2.load_state(file_path)
    assert qm2.count() == 3
    assert qm2.current_index == 1
    assert qm2.get_current_track().title == "Song B"


def test_queue_next_and_previous(sample_tracks):
    qm = QueueManager()
    for t in sample_tracks:
        qm.add(t)

    # Initial state
    assert qm.get_current_track() is None

    # Next track -> Song A
    t1 = qm.next()
    assert t1.title == "Song A"
    assert qm.current_index == 0

    # Next track -> Song B
    t2 = qm.next()
    assert t2.title == "Song B"
    assert qm.current_index == 1

    # Previous track -> Song A
    t_prev = qm.previous()
    assert t_prev.title == "Song A"


def test_queue_repeat_modes(sample_tracks):
    qm = QueueManager()
    for t in sample_tracks:
        qm.add(t)

    qm.next()  # Song A
    qm.next()  # Song B
    qm.next()  # Song C

    # Off mode -> Next returns None
    qm.repeat = "off"
    assert qm.next() is None

    # Repeat ALL mode -> Next wraps to Song A
    qm.repeat = "all"
    qm.set_current_index(2)  # Song C
    t_wrap = qm.next()
    assert t_wrap.title == "Song A"

    # Repeat TRACK mode -> Next returns same track Song A
    qm.repeat = "track"
    t_same = qm.next()
    assert t_same.title == "Song A"


def test_queue_shuffle(sample_tracks):
    qm = QueueManager()
    for t in sample_tracks:
        qm.add(t)

    qm.shuffle = True
    qm.set_current_index(0)
    nxt = qm.next()
    assert nxt is not None
    assert nxt.id in ["2", "3"]


def test_queue_reordering(sample_tracks):
    qm = QueueManager()
    for t in sample_tracks:
        qm.add(t)

    # Move Song B (index 1) up -> becomes index 0
    assert qm.move_up(1) is True
    assert qm.items[0].title == "Song B"
    assert qm.items[1].title == "Song A"

    # Move Song B (index 0) down -> becomes index 1
    assert qm.move_down(0) is True
    assert qm.items[0].title == "Song A"
    assert qm.items[1].title == "Song B"


def test_queue_remove_and_clear(sample_tracks):
    qm = QueueManager()
    for t in sample_tracks:
        qm.add(t)

    removed = qm.remove(1)
    assert removed.title == "Song B"
    assert qm.count() == 2

    qm.clear()
    assert qm.is_empty()
    assert qm.get_current_track() is None
