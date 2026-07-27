__all__ = ['MainWindow']


def __getattr__(name):
    """Load the main window only when callers request it."""
    if name == 'MainWindow':
        from .main_window import MainWindow

        return MainWindow
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
