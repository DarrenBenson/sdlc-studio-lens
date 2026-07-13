"""Application logs must actually reach stdout (BG-01KXDGA1).

For the entire life of this project, `logging.basicConfig` was never called. Uvicorn
configures only its own loggers, so the root logger had no handler and EVERY
`logger.info`/`warning`/`exception` in `sdlc_lens.*` was silently discarded in production.

**819 tests passed while this was true**, because every logging assertion in the suite uses
`caplog` - and `caplog` installs its own handler. The fixture supplied the very thing that
was missing, so it was testing itself.

So these tests deliberately do NOT use caplog. They capture real stdout and assert a real
log record comes out of the real configured root logger. A test that cannot fail against
the broken code is not a test.
"""

import io
import logging
import sys

from sdlc_lens.main import configure_logging, create_app


def _capture_stdout_of(fn) -> str:
    """Run `fn` with a fresh root logger and capture what it actually writes to stdout.

    The root logger is cleared HERE rather than in a fixture: pytest's logging plugin
    re-attaches its own handler after fixture setup, which is precisely the kind of
    fixture-supplies-the-missing-thing effect that let this bug live for the life of the
    project. Clear it in the test body, where nothing can put it back behind our back.
    """
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    root.handlers = []

    buffer = io.StringIO()
    real_stdout = sys.stdout
    sys.stdout = buffer
    try:
        fn()
    finally:
        for h in root.handlers:
            h.flush()
        sys.stdout = real_stdout
        root.handlers, root.level = saved_handlers, saved_level
    return buffer.getvalue()


def test_an_application_log_line_actually_reaches_stdout() -> None:
    """The whole bug, in one assertion.

    Without configure_logging() the root logger has no handler and this produces nothing
    at all - which is exactly what production did.
    """

    def _emit() -> None:
        configure_logging()
        logging.getLogger("sdlc_lens.services.poller").info("Freshness poller started")

    out = _capture_stdout_of(_emit)

    assert "Freshness poller started" in out, (
        "an application log line did not reach stdout - the root logger has no handler, "
        "so everything the app logs is silently discarded (BG-01KXDGA1)"
    )


def test_the_poller_failure_warning_reaches_stdout() -> None:
    """The poller's only observability. If this is dropped, it dies in silence."""

    def _emit() -> None:
        configure_logging()
        logging.getLogger("sdlc_lens.services.poller").warning("Poll failed for 'x': boom")

    out = _capture_stdout_of(_emit)
    assert "Poll failed" in out


def test_creating_the_app_configures_logging() -> None:
    """It must be wired in, not merely available."""

    def _emit() -> None:
        create_app()
        logging.getLogger("sdlc_lens.services.sync_engine").info("sync engine says hello")

    out = _capture_stdout_of(_emit)
    assert "sync engine says hello" in out, "create_app() did not configure logging"


def test_the_configured_level_is_honoured() -> None:
    """SDLC_LENS_LOG_LEVEL sat in config.py doing nothing at all."""
    from sdlc_lens.config import settings

    original = settings.log_level
    settings.log_level = "WARNING"
    try:

        def _emit() -> None:
            configure_logging()
            log = logging.getLogger("sdlc_lens.services.poller")
            log.info("this INFO line must be suppressed at WARNING")
            log.warning("this WARNING line must appear")

        out = _capture_stdout_of(_emit)
    finally:
        settings.log_level = original

    assert "must be suppressed" not in out, "log_level is not being honoured"
    assert "must appear" in out


def test_it_is_idempotent_and_survives_a_foreign_handler() -> None:
    """Calling it twice must not double-log - and a foreign handler must not silence us.

    The first version of the fix said `if not root.handlers`. That is the wrong question:
    anything else attaching a root handler (pytest's caplog, an APM agent, a library) would
    make us skip, and the app would go silent again - which is the whole bug.
    """
    from sdlc_lens.main import _LOG_HANDLER_NAME

    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers = [logging.NullHandler()]  # a foreign handler is already present
    try:
        configure_logging()
        configure_logging()
        configure_logging()
        ours = [h for h in root.handlers if h.get_name() == _LOG_HANDLER_NAME]
    finally:
        root.handlers = saved

    assert len(ours) == 1, f"expected exactly one of our handlers, got {len(ours)}"
