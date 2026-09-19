"""Bot card tests."""

from botscope.botcard import library_index, load_library


def test_library_loads():
    lib = load_library()
    assert lib.count if hasattr(lib, "count") else len(lib.cards) >= 1
    idx = library_index()
    assert idx
    assert "name" in idx[0]
