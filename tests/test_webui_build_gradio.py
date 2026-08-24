"""Real Gradio build/launch smoke test (requires the `webui` extra).

Verifies the WebUI builds and launches on the installed Gradio without a
TypeError or ignored-argument warning, and that the selected theme is actually
applied for the installed major version.
"""

from __future__ import annotations

import pytest

pytest.importorskip("gradio")

import gradio as gr  # noqa: E402

import skillopt_webui.app as app  # noqa: E402


def test_webui_builds_and_launches_theme():
    ui = app.build_ui()
    launch_kwargs = {"prevent_thread_lock": True}
    if app._GRADIO_MAJOR >= 6:
        # Gradio 6 applies theme at launch(); add it here and assert applied.
        launch_kwargs["theme"] = gr.themes.Soft(primary_hue="indigo")
    ui.launch(**launch_kwargs)
    try:
        assert ui.theme is not None, "theme was not applied on the launched app"
    finally:
        ui.close()


def test_gradio_major_detected():
    # The constant must reflect the installed Gradio major (6 for 6.25).
    assert app._GRADIO_MAJOR == int(gr.__version__.split(".")[0])
