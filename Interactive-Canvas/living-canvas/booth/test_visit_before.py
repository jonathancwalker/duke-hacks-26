#!/usr/bin/env python3
"""The first visit of the night also stores the canvas as it was before it, so the montage (issue #31) can start there.

    python3 booth/test_visit_before.py

Also collectable by pytest.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402

# A 1x1 JPEG is enough: the server only decodes base64 and writes the bytes.
JPEG = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="


def test_first_visit_keeps_its_before_canvas():
    with tempfile.TemporaryDirectory() as d:
        bs.VISITS, bs.TONIGHT = d, os.path.join(d, "current")
        bs.visit_save({"reading": "a calm Sunday", "strokes": [[{"x": 1, "y": 2, "t": 0}]], "canvas": JPEG, "before": JPEG})
        bs.visit_save({"reading": "nervous", "strokes": [], "canvas": JPEG})
        first, second = bs.visits_list()
        assert first["before"] == "/visits/0001-before.jpg", first.get("before")
        assert os.path.isfile(os.path.join(bs.TONIGHT, "0001-before.jpg"))
        assert second["before"] is None, second.get("before")
        assert first["canvas"] == "/visits/0001-canvas.jpg"


if __name__ == "__main__":
    test_first_visit_keeps_its_before_canvas()
    print("visit before canvas: ok")
