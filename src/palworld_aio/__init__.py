def run_aio(*args, **kwargs):
    """Launch the GUI without importing the full application at package import time."""
    from .main import run_aio as _run_aio

    return _run_aio(*args, **kwargs)
