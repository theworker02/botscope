"""Annotation store tests."""

from botscope.annotations import AnnotationStore


def test_annotation_roundtrip(tmp_path):
    store = AnnotationStore(tmp_path / "sess.bscope")
    store.add("s1", "note A", event_id="e1", tags=["x"])
    store.add("s1", "note B")
    assert len(store.list_annotations("s1")) == 2
    store.close()
