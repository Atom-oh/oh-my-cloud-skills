"""Host identity shared by configuration, readiness probes, and lifecycle hooks."""
import os

HOSTS = ("claude", "codex")


def detect_host(explicit=None):
    """Prefer caller overrides, then runtime markers, then the legacy Claude default.

    Do not infer the host from installed CLIs or credentials: either host may have
    both. CLAUDECODE identifies a nested Claude process even when it inherits Codex
    session markers. Callers validate explicit values rather than hiding typos.
    """
    if explicit is not None:
        return explicit
    if os.environ.get("CO_AGENT_HOST"):
        return os.environ["CO_AGENT_HOST"]
    if os.environ.get("CLAUDECODE") == "1":
        return "claude"
    if (os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
            or (os.environ.get("PLUGIN_ROOT") and os.environ.get("PLUGIN_DATA"))):
        return "codex"
    return "claude"
