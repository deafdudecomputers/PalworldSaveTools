import json
import os
import re
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from loguru import logger

_MAPPAL_AVAILABLE = False
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
    _MAPPAL_AVAILABLE = True
except ImportError:
    QWebEngineView = None
    QWebEnginePage = None
    QWebEngineSettings = None
    QWebEngineProfile = None

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QLabel, QSizePolicy, QStackedWidget)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut

_MAPPAL_RESOURCE_DIR = None
_MAPPAL_SERVER = None
_MAPPAL_SERVER_PORT = None


def _find_mappal_dir():
    global _MAPPAL_RESOURCE_DIR
    if _MAPPAL_RESOURCE_DIR:
        return _MAPPAL_RESOURCE_DIR
    candidates = []
    try:
        from palworld_aio.constants import get_base_path
        base = get_base_path()
        candidates.append(os.path.join(base, "resources", "mappal"))
    except Exception:
        pass
    candidates.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "mappal"))
    for c in candidates:
        d = os.path.normpath(c)
        if os.path.isfile(os.path.join(d, "index.html")):
            _MAPPAL_RESOURCE_DIR = d
            return d
    return None


def _start_server():
    global _MAPPAL_SERVER, _MAPPAL_SERVER_PORT
    if _MAPPAL_SERVER:
        return _MAPPAL_SERVER_PORT
    mappal_dir = _find_mappal_dir()
    if not mappal_dir:
        return None

    _GAME_DATA_ICONS = None
    try:
        from palworld_aio.constants import get_base_path
        _g = get_base_path()
        _GAME_DATA_ICONS = os.path.normpath(os.path.join(_g, "resources", "game_data", "icons"))
    except Exception:
        pass

    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=mappal_dir, **kwargs)

        def translate_path(self, path):
            if _GAME_DATA_ICONS and path.startswith('/icons/'):
                rel = path.lstrip('/').replace('/', os.sep)
                result = os.path.normpath(os.path.join(_GAME_DATA_ICONS, rel[len('icons/'):] if rel.startswith('icons/') else rel))
                if result.startswith(_GAME_DATA_ICONS) and os.path.exists(result):
                    return result
            return super().translate_path(path)

        def end_headers(self):
            p = self.path
            if re.search(r'[.-][a-f0-9]{8,}\.(js|css|png|webp)$', p):
                self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
            elif p.endswith('.html'):
                self.send_header('Cache-Control', 'no-cache')
            else:
                self.send_header('Cache-Control', 'public, max-age=86400')
            super().end_headers()

        def log_message(self, fmt, *args):
            pass

    for port in range(18200, 18300):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", port))
            s.close()
            _MAPPAL_SERVER = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
            _MAPPAL_SERVER_PORT = port
            t = threading.Thread(target=_MAPPAL_SERVER.serve_forever, daemon=True)
            t.start()
            logger.debug(f"mappal HTTP server on port {port}")
            return port
        except OSError:
            continue
    logger.error("could not find free port for mappal server")
    return None


def _setup_web_profile():
    try:
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        profile.setHttpCacheMaximumSize(100 * 1024 * 1024)
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "pst", "webcache")
        profile.setCachePath(cache_dir)
    except Exception as e:
        logger.warning(f"could not setup web cache: {e}")


def is_mappal_available():
    return _MAPPAL_AVAILABLE and _find_mappal_dir() is not None


if _MAPPAL_AVAILABLE:

    class Map3DViewer(QWidget):
        close_clicked = Signal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self._pending_data = None
            self._page_ready = False
            self._load_count = 0

            self.setVisible(False)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            _setup_web_profile()

            QShortcut(QKeySequence(Qt.Key_Escape), self, self._on_close)

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            close_bar = QWidget()
            close_bar.setStyleSheet("background-color: rgba(20, 20, 30, 220);")
            close_bar.setFixedHeight(28)
            bar_layout = QHBoxLayout(close_bar)
            bar_layout.setContentsMargins(8, 0, 8, 0)

            title_label = QLabel("3D Base Viewer")
            title_label.setStyleSheet("color: #ccc; font-size: 11px;")
            bar_layout.addWidget(title_label)
            bar_layout.addStretch()

            self._close_btn = QPushButton("✕")
            self._close_btn.setFixedSize(20, 20)
            self._close_btn.setStyleSheet(
                "QPushButton { color: #aaa; background: transparent; border: none; font-size: 12px; }"
                "QPushButton:hover { color: #fff; background: rgba(255,80,80,0.3); border-radius: 3px; }"
            )
            self._close_btn.clicked.connect(self._on_close)
            bar_layout.addWidget(self._close_btn)

            root.addWidget(close_bar)

            self._webview = QWebEngineView()
            self._webview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._webview.page().setBackgroundColor(QColor(14, 16, 20))

            settings = self._webview.settings()
            settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
            settings.setAttribute(QWebEngineSettings.FocusOnNavigationEnabled, False)
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
            settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
            settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)
            settings.setAttribute(QWebEngineSettings.PdfViewerEnabled, False)
            settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, False)
            settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
            settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

            self._webview.loadFinished.connect(self._on_page_loaded)

            port = _start_server()
            if port:
                url = QUrl(f"http://127.0.0.1:{port}/index.html?embed=1")
                self._webview.load(url)
            else:
                self._webview.setHtml(
                    "<html><body style='background:#0e1014;color:#888;display:flex;"
                    "align-items:center;justify-content:center;font-family:sans-serif;"
                    "font-size:14px;'><p>3D viewer server unavailable.</p></body></html>"
                )

            self._stack = QStackedWidget()
            self._stack.addWidget(self._webview)

            self._loading_label = QLabel("Loading 3D view...")
            self._loading_label.setAlignment(Qt.AlignCenter)
            self._loading_label.setStyleSheet("color: #666; font-size: 13px; background: #0e1014;")
            self._stack.addWidget(self._loading_label)
            self._stack.setCurrentWidget(self._loading_label)

            root.addWidget(self._stack)

        def _on_close(self):
            logger.debug("Map3DViewer._on_close called")
            self._pending_data = None
            self.close_clicked.emit()

        def _on_page_loaded(self, ok):
            log = logger
            log.debug(f"page loaded: ok={ok}, pending={self._pending_data is not None}")
            self._page_ready = ok
            if ok:
                self._stack.setCurrentWidget(self._webview)
                self._webview.page().runJavaScript(
                    "document.title",
                    lambda t: log.debug(f"JS alive, title={t}"),
                )
            if ok and self._pending_data:
                name, jsdata = self._pending_data
                log.debug(f"flush pending: name={name}, data_len={len(jsdata)}")
                self._do_load(name, jsdata)
                self._pending_data = None
            elif not ok:
                self._loading_label.setText("Page failed to load")

        def load_base(self, name, json_str):
            if not self._webview:
                return
            logger.debug(f"load_base: name={name}, data_len={len(json_str)}, ready={self._page_ready}")
            if self._page_ready:
                self._stack.setCurrentWidget(self._loading_label)
                self._loading_label.setText("Loading 3D view...")
                self._webview.page().runJavaScript("window.pstLoadBase && pstLoadBase('clear', '{}')")
                self._do_load(name, json_str)
            else:
                self._pending_data = (name, json_str)
                self._loading_label.setText("Loading 3D view...")
                self._stack.setCurrentWidget(self._loading_label)

        def _do_load(self, name, json_str):
            self._load_count += 1
            logger.debug(f"_do_load #{self._load_count}: name={name}, data_len={len(json_str)}")
            escaped_name = json.dumps(name)
            encoded = json.dumps(json_str)
            js = f"pstLoadBase({escaped_name}, {encoded})"
            self._webview.page().runJavaScript(js)
            self._stack.setCurrentWidget(self._webview)

        def clear(self):
            self._pending_data = None
            if self._webview and self._page_ready:
                self._webview.page().runJavaScript(
                    "window.postMessage({type:'pst-load-base',name:'clear',json:{}},'*')"
                )

else:
    class Map3DViewer(QWidget):
        close_clicked = Signal()
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setVisible(False)
            layout = QVBoxLayout(self)
            label = QLabel("3D Viewer requires PySide6 with WebEngine support.")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 13px; padding: 20px;")
            layout.addWidget(label)
        def load_base(self, name, json_str):
            pass
        def clear(self):
            pass
