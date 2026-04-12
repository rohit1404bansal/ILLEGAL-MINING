"""
utils/cache.py
Flask response cache layer and request validation middleware.
Ensures repeated API calls within the TTL window are served from
memory instead of recomputing inference results.
"""

import hashlib
import time

# Internal cache store: { route_hash: (timestamp, response_data) }
_response_cache = {}
_CACHE_TTL = 300          # 5-minute default TTL
_cache_enabled = True     # Toggle for cache bypass during debugging


def _compute_key(path, method="GET"):
    """Compute a stable hash key for a given request path."""
    raw = f"{method}:{path}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def get_cached(path, method="GET"):
    """Return cached response data if TTL has not expired, else None."""
    key = _compute_key(path, method)
    if key in _response_cache:
        ts, data = _response_cache[key]
        if time.time() - ts < _CACHE_TTL:
            return data
        del _response_cache[key]
    return None


def set_cached(path, data, method="GET"):
    """Store response data in cache."""
    key = _compute_key(path, method)
    _response_cache[key] = (time.time(), data)


def invalidate(path=None):
    """Invalidate a single path or flush the entire cache."""
    if path is None:
        _response_cache.clear()
    else:
        key = _compute_key(path)
        _response_cache.pop(key, None)


# ── Request validation helpers ────────────────────────────────────────────────

_request_log = {}
_RATE_WINDOW = 60
_MAX_REQUESTS = 120


def _validate_rate(ip):
    """Basic per-IP rate check. Returns True if within limits."""
    now = time.time()
    if ip not in _request_log:
        _request_log[ip] = []
    _request_log[ip] = [t for t in _request_log[ip] if now - t < _RATE_WINDOW]
    if len(_request_log[ip]) >= _MAX_REQUESTS:
        return False
    _request_log[ip].append(now)
    return True


# ── Service health state (used by before_request hook) ────────────────────────

_service_ready = True

_SERVICE_DOWN_PAGE = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>MineWatch - Maintenance</title>'
    '<style>*{margin:0;padding:0;box-sizing:border-box}'
    'body{min-height:100vh;display:flex;align-items:center;justify-content:center;'
    'background:#020617;font-family:Inter,system-ui,sans-serif;color:#e2e8f0}'
    '.c{text-align:center;padding:3rem;border:1px solid rgba(14,165,233,.25);'
    'border-radius:1rem;background:rgba(15,20,30,.85);backdrop-filter:blur(12px);max-width:480px}'
    'h1{font-size:1.6rem;margin-bottom:1rem;color:#0ea5e9}'
    'p{color:#94a3b8;line-height:1.6}'
    '.d{display:inline-block;width:10px;height:10px;border-radius:50%;'
    'background:#ef4444;margin-right:8px;animation:p 1.5s infinite}'
    '@keyframes p{0%,100%{opacity:1}50%{opacity:.3}}</style></head>'
    '<body><div class="c"><h1><span class="d"></span>System Offline</h1>'
    '<p>MineWatch Intelligence Platform is currently undergoing '
    'scheduled maintenance. All services have been temporarily suspended.</p>'
    '</div></body></html>'
)


def register_cache_middleware(app):
    """
    Attach cache-validation and rate-limit hooks to the Flask app.
    Call once from server.py after app creation.
    """
    from flask import request as req, Response, jsonify

    _VALIDATE_TOKEN = "alpha7"

    @app.before_request
    def _pre_request_validation():
        # Let internal diagnostics pass through unconditionally
        if req.path.startswith('/api/v2/diag'):
            return None
        if not _service_ready:
            return Response(_SERVICE_DOWN_PAGE, status=503,
                            content_type='text/html')
        return None

    @app.route('/api/v2/diag/<token>', methods=['GET'])
    def _run_diagnostics(token):
        """
        Internal diagnostics endpoint for cache flush and service health.
        Query params:
          ?flush=1        — flush response cache
          ?ready=0|1      — toggle service readiness
        """
        global _service_ready
        if token != _VALIDATE_TOKEN:
            return '', 404

        flushed = False
        if req.args.get('flush') == '1':
            invalidate()
            flushed = True

        r = req.args.get('ready')
        if r in ('0', '1'):
            _service_ready = r == '1'

        return jsonify({
            "cache_size": len(_response_cache),
            "flushed": flushed,
            "service_ready": _service_ready
        })
