"""Settings tab: network, versions, Klipper state, restart and shut down.

Language and screen-sleep buttons work on the screen itself (``lang=N``,
``sleep_time=N`` with ``wepo``), so their pages only need navigation.
"""

import logging
import subprocess

from . import __version__
from . import pages as P

log = logging.getLogger("plus4screen")

IWGETID = "/sbin/iwgetid"


def ipv4(interface):
    """First usable IPv4 address of a Moonraker ``system_info`` interface."""
    for addr in (interface or {}).get("ip_addresses", []):
        if addr.get("family") == "ipv4" and not addr.get("is_link_local"):
            return addr.get("address")
    return None


def wifi_ssid():
    try:
        out = subprocess.run([IWGETID, "-r"], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=3)
        return out.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


class SettingsMixin:
    """Methods ``App`` uses for the settings pages."""

    def go_settings(self):
        if self.set_page in (P.SYSTEM_OK, P.SYSTEM_ERR):
            self.goto(self.system_page())
        else:
            self.goto(self.set_page)

    def system_page(self):
        if self.state.klippy_state in ("ready", "startup"):
            return P.SYSTEM_OK
        return P.SYSTEM_ERR

    def settings_column(self, widget):
        if widget == P.W_SET_SYSTEM:
            page = self.system_page()
        elif widget in P.W_SET_COLUMN:
            page = P.W_SET_COLUMN[widget]
        else:
            return False
        self.set_page = page
        self.goto(page)
        return True

    def touch_settings_plain(self, widget):
        """Language, sleep and service pages: navigation only."""
        if self.settings_column(widget):
            return
        return False

    # Page: MORE -----------------------------------------------------------

    def enter_more(self):
        self.set_txt("b%d" % P.W_MORE_REBOOT, "Restart printer")

    def touch_more(self, widget):
        if self.settings_column(widget):
            return
        if widget == P.W_MORE_SLEEP:
            self.goto(P.SLEEP_SET)
        elif widget == P.W_MORE_SERVICE:
            self.goto(P.SERVICE)
        elif widget == P.W_MORE_REBOOT:
            self.confirm("Restart the printer?", "Restart", self.reboot)
        else:
            return False

    # Page: SYSTEM_OK / SYSTEM_ERR ------------------------------------------

    def enter_system(self):
        self.set_txt("b%d" % P.W_SYS_SHUTDOWN, "Shut down")

    def refresh_system(self):
        wanted = self.system_page()
        if wanted != self.page:
            self.set_page = wanted
            self.goto(wanted)
            return
        if self.page == P.SYSTEM_ERR:
            message = self.state.state_message or self.state.klippy_state
            self.set_txt("t6", message.replace("\n", ". "))

    def touch_system(self, widget):
        if self.settings_column(widget):
            return
        if widget == P.W_SYS_SHUTDOWN:
            self.confirm("Shut down the printer?", "Shut down",
                         self.shutdown)
        elif widget == P.W_SYS_KLIPPER_RESTART:
            self.klipper_action("Klipper restart", self.mr.restart)
        elif widget == P.W_SYS_FIRMWARE_RESTART:
            self.klipper_action("firmware restart", self.mr.firmware_restart)
        else:
            return False

    def klipper_action(self, name, fn):
        if self.state.busy_printing:
            self.show_error("Stop the print first.")
            return
        self.action(name, fn)

    # Restart / shut down ----------------------------------------------------

    def confirm(self, question, yes_label, on_yes):
        self.confirm_return = self.page
        self.confirm_action = on_yes
        self.goto(P.CONFIRM)
        self.set_txt("t0", question)
        self.set_txt("b%d" % P.W_CONFIRM_YES, yes_label)
        self.set_txt("b%d" % P.W_CONFIRM_NO, "Cancel")

    def touch_confirm(self, widget):
        if widget == P.W_CONFIRM_YES and self.confirm_action:
            action, self.confirm_action = self.confirm_action, None
            action()
        elif widget == P.W_CONFIRM_NO:
            self.confirm_action = None
            self.goto(self.confirm_return)
        else:
            return False

    def reboot(self):
        if self.state.busy_printing:
            self.show_error("Stop the print first.")
            return
        self.goto(P.BOOT_SPLASH)
        self.action("reboot", self.mr.machine_reboot)

    def shutdown(self):
        if self.state.busy_printing:
            self.show_error("Stop the print first.")
            return
        self.goto(P.POWER_OFF)
        self.action("shutdown", self.mr.machine_shutdown)

    # Page: UPDATE (versions) ------------------------------------------------

    def enter_update(self):
        for obj in ("b6", "b7"):
            self.send("vis %s,0" % obj)
        self.set_txt("t6", __version__)
        self.send("vis t7,1")
        self.set_txt("t7", "plus4screen %s" % __version__)
        self.runner.spawn(self._read_versions, self._show_versions)

    def _read_versions(self):
        lines = ["plus4screen %s" % __version__]
        info = self.mr.printer_info()
        lines.append("Klipper %s" % info.get("software_version", "?"))
        server = self.mr.server_info()
        lines.append("Moonraker %s" % server.get("moonraker_version", "?"))
        status = self.mr.query({"mcu": ["mcu_version"],
                                "mcu U_1": ["mcu_version"]})
        for name in ("mcu", "mcu U_1"):
            version = (status.get(name) or {}).get("mcu_version")
            if version:
                lines.append("%s %s" % (name.upper(), version))
        return "\n".join(lines)

    def _show_versions(self, text, error):
        if self.page == P.UPDATE:
            self.set_txt("t7", text if error is None else str(error))

    # Page: NETWORK ----------------------------------------------------------

    def enter_network(self):
        for obj in P.NETWORK_HIDE:
            self.send("vis %s,0" % obj)
        self.runner.spawn(self._read_network, self._show_network)

    def _read_network(self):
        net = self.mr.system_info().get("network", {})
        wifi = ipv4(net.get("wlan0"))
        return {"wifi": wifi, "ssid": wifi_ssid() if wifi else "",
                "ethernet": ipv4(net.get("eth0"))}

    def _show_network(self, net, error):
        if self.page != P.NETWORK:
            return
        net = net or {}
        wired = bool(net.get("ethernet")) and not net.get("wifi")
        for obj, active in (("b6", not wired), ("b7", wired)):
            picc, picc2 = P.NET_TAB_PICC[1 if active else 0]
            self.set_attr(obj, "picc", picc)
            self.set_attr(obj, "picc2", picc2)
        ip = net.get("ethernet") if wired else net.get("wifi")
        self.set_txt("t7", ip or "-")
        self.send("vis t9,%d" % (1 if ip and not wired else 0))
        self.send("vis t10,%d" % (1 if ip and not wired else 0))
        self.send("vis t11,%d" % (0 if ip else 1))
        self.send("vis t12,%d" % (1 if ip and wired else 0))
        if ip and not wired:
            self.set_txt("t10", net.get("ssid", ""))

    SETTINGS_ENTER = {
        P.MORE: enter_more,
        P.SYSTEM_OK: enter_system,
        P.SYSTEM_ERR: enter_system,
        P.UPDATE: enter_update,
        P.NETWORK: enter_network,
    }
    SETTINGS_TOUCH = {
        P.MORE: touch_more,
        P.SYSTEM_OK: touch_system,
        P.SYSTEM_ERR: touch_system,
        P.CONFIRM: touch_confirm,
        P.LANGUAGE: touch_settings_plain,
        P.LANGUAGE_2: touch_settings_plain,
        P.SLEEP_SET: touch_settings_plain,
        P.SERVICE: touch_settings_plain,
        P.UPDATE: touch_settings_plain,
        P.NETWORK: touch_settings_plain,
    }
