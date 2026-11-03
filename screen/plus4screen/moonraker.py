"""Minimal Moonraker HTTP client (standard library only)."""

import json
import urllib.error
import urllib.parse
import urllib.request

MAX_DOWNLOAD = 2 * 1024 * 1024   # bytes; thumbnails are tens of KB


class MoonrakerError(Exception):
    def __init__(self, message, reachable=False):
        super().__init__(message)
        self.reachable = reachable      # Moonraker answered with an error


class Moonraker:
    def __init__(self, url="http://127.0.0.1:7125", timeout=5.0):
        self.url = url.rstrip("/")
        self.timeout = timeout
        # Moonraker runs on the printer itself: never use a proxy.
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}))

    def _request(self, method, path, params=None, body=None, timeout=None):
        url = self.url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method,
                                     headers=headers)
        try:
            with self.opener.open(
                    req, timeout=timeout or self.timeout) as resp:
                payload = json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            raise MoonrakerError(self._error_text(exc), True) from None
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise MoonrakerError(str(exc)) from None
        return payload.get("result")

    @staticmethod
    def _error_text(exc):
        try:
            return json.loads(exc.read().decode())["error"]["message"]
        except Exception:
            return "HTTP %d" % exc.code

    # Printer status -----------------------------------------------------

    def query(self, objects):
        result = self._request("POST", "/printer/objects/query",
                               body={"objects": objects})
        return result["status"]

    # Commands -----------------------------------------------------------

    def gcode(self, script, timeout=3600.0):
        """Run G-code. Blocks until Klipper has finished it."""
        self._request("POST", "/printer/gcode/script",
                      params={"script": script}, timeout=timeout)

    def emergency_stop(self):
        self._request("POST", "/printer/emergency_stop")

    def pause(self):
        self._request("POST", "/printer/print/pause")

    def resume(self):
        self._request("POST", "/printer/print/resume")

    def cancel(self):
        self._request("POST", "/printer/print/cancel")

    def start_print(self, filename):
        self._request("POST", "/printer/print/start",
                      params={"filename": filename})

    def restart(self):
        """Klipper host restart (G-code RESTART)."""
        self._request("POST", "/printer/restart")

    def firmware_restart(self):
        self._request("POST", "/printer/firmware_restart")

    def machine_reboot(self):
        self._request("POST", "/machine/reboot")

    def machine_shutdown(self):
        self._request("POST", "/machine/shutdown")

    # Information --------------------------------------------------------

    def printer_info(self):
        return self._request("GET", "/printer/info") or {}

    def server_info(self):
        return self._request("GET", "/server/info") or {}

    def system_info(self):
        result = self._request("GET", "/machine/system_info") or {}
        return result.get("system_info", {})

    def last_job(self):
        """Most recent job from the print history, or None."""
        result = self._request("GET", "/server/history/list",
                               params={"limit": 1, "order": "desc"}) or {}
        jobs = result.get("jobs") or []
        return jobs[0] if jobs else None

    def download(self, root, path, limit=MAX_DOWNLOAD):
        """Raw bytes of a file in a Moonraker root, e.g. a thumbnail; a file
        larger than ``limit`` bytes is refused."""
        url = "%s/server/files/%s/%s" % (
            self.url, root, urllib.parse.quote(path))
        try:
            with self.opener.open(url, timeout=self.timeout) as resp:
                data = resp.read(limit + 1)
        except urllib.error.HTTPError as exc:
            raise MoonrakerError("HTTP %d for %s" % (exc.code, path),
                                 True) from None
        except (urllib.error.URLError, OSError) as exc:
            raise MoonrakerError(str(exc)) from None
        if len(data) > limit:
            raise MoonrakerError("%s is larger than %d bytes" % (path, limit),
                                 True)
        return data

    def gcode_store(self, count=100):
        """Recent console lines: [{"message", "time", "type"}, ...]."""
        result = self._request("GET", "/server/gcode_store",
                               params={"count": count}) or {}
        return result.get("gcode_store", [])

    # Files --------------------------------------------------------------

    def list_files(self):
        files = self._request("GET", "/server/files/list",
                              params={"root": "gcodes"}) or []
        files = [f for f in files
                 if f.get("path", "").lower().endswith((".gcode", ".g"))
                 and not is_hidden(f["path"])]
        files.sort(key=lambda f: f.get("modified", 0), reverse=True)
        return files

    def metadata(self, filename):
        try:
            return self._request("GET", "/server/files/metadata",
                                 params={"filename": filename}) or {}
        except MoonrakerError:
            return {}


def is_hidden(path):
    """True for files inside hidden folders such as QIDI's ``.cache``
    and ``.plr`` (power-loss recovery copies)."""
    return any(part.startswith(".") for part in path.split("/")[:-1])
