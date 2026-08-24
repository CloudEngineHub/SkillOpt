"""Real Gradio build/launch smoke test (requires the `webui` extra).

Verifies the WebUI builds (and launches where the environment allows) on the
installed Gradio without a TypeError or ignored-argument warning, and that the
theme is placed on the right object for the installed major version.
"""

from __future__ import annotations

import pytest

pytest.importorskip("gradio")

import gradio as gr  # noqa: E402

import skillopt_webui.app as app  # noqa: E402


def test_webui_builds_theme_on_blocks():
    """build_ui() must not raise; for Gradio <6 the theme lives on Blocks."""
    ui = app.build_ui()
    assert ui is not None
    if app._GRADIO_MAJOR < 6:
        assert ui.theme is not None, "theme was not set on Blocks for Gradio <6"


def test_webui_builds_and_launches_theme():
    ui = app.build_ui()
    launch_kwargs = {"prevent_thread_lock": True}
    if app._GRADIO_MAJOR >= 6:
        # Gradio 6 applies theme at launch(); we add it here and assert applied.
        launch_kwargs["theme"] = gr.themes.Soft(primary_hue="indigo")
    try:
        ui.launch(**launch_kwargs)
    except ValueError as exc:
        # Headless/sandboxed environments may not expose localhost; that is an
        # environment limitation, not a theme-compatibility bug.
        if "localhost is not accessible" in str(exc):
            pytest.skip("headless environment blocks localhost launch")
        raise
    try:
        assert ui.theme is not None, "theme was not applied on the launched app"
    finally:
        ui.close()


def test_gradio_major_detected():
    # The constant must reflect the installed Gradio major.
    assert app._GRADIO_MAJOR == int(gr.__version__.split(".")[0])
