"""Page and widget numbers of QIDI's screen layout.

Taken from ``UI/xindi_800_480.HMI`` with ``tools/hmi_dump.py``. A page
number is the page's position in the project, as used by ``page <n>``.
Widget numbers are the numbers the widgets *report* in touch events,
which are not always their TJC object ids.
"""

GRAY = 38066     # pco of an inactive label, from the layout
WHITE = 65535

LOGO = 0
MAIN = 3
FILE_LIST = 4
PREVIEW = 5
PRINTING = 17
PRINT_KB = 18
PRINT_FINISH = 20
CONTROL = 35
CONTROL_KB = 36
PRE_LOAD = 37
PRE_HEAT = 39
UNLOAD = 40
LOAD = 41
SCREEN_SLEEP = 43
GCODE_ERROR = 45
PRINT_STOP = 53
CONTROL_SETFAN = 58
LOAD_2 = 71
LOAD_FINISH = 72

# Navigation bar at the bottom of most pages.
NAV_HOME = 33
NAV_HOME_ALT = 102      # the home button on MAIN and PRINTING reports 102
NAV_CONTROL = 34
NAV_FILES = 35
NAV_TOOLS = 36
NAV_SETTINGS = 37

# The left column shared by the control pages: temperatures and fans.
# n0-n2 current temperature, n3-n5 target, n6-n8 fan percentage.
CONTROL_FAMILY = (CONTROL, CONTROL_KB, PRE_LOAD, PRE_HEAT, UNLOAD, LOAD,
                  CONTROL_SETFAN, LOAD_2, LOAD_FINISH)
W_HEATER_TARGET = 3     # b3/b4/b5, the screen sets sys0 to 0/1/2 first
W_FANS = 22             # b22, opens CONTROL_SETFAN

# CONTROL (page 35)
W_STEP = {6: 1, 7: 10, 8: 50, 9: 100}   # widget -> mm
STEP_PICC = (114, 116)                    # picc (normal, selected)
W_HOME = 10
W_MOTORS_OFF = 11
W_FILAMENT = 13          # stock: QIDI Box page; here: single-spool flow
# Directions match xindi: 14 move_y_increase, 15 move_y_decrease,
# 16 move_x_decrease, 17 move_x_increase, 18 move_z_decrease (Z-),
# 19 move_z_increase (Z+), 20 start_retract, 21 start_extrude.
W_JOG = {14: ("Y", 1), 15: ("Y", -1), 16: ("X", -1), 17: ("X", 1),
         18: ("Z", -1), 19: ("Z", 1)}
W_EXTRUDER = {20: -1, 21: 1}   # up arrow retracts, down arrow extrudes

# CONTROL_KB (page 36). OK sends the typed value as a 0x71 frame
# (page 35, widget 0/1/2 by sys0); with an empty input it reports 25.
W_KB_OK = 25
HEATER_VALUE_WIDGETS = (0, 1, 2)    # extruder, bed, chamber

# 0x71 frames from the fan page and keypad carry page 35 and these widgets.
FAN_VALUE_WIDGETS = (22, 23, 24)
W_FAN_TOGGLE = {6: 0, 7: 1, 8: 2}

# PRE_HEAT (page 39): temperature choice and the two buttons below it.
W_TEMP = {6: 220, 7: 250, 8: 300}
TEMP_PICC = (123, 124)   # picc (normal, selected)
W_LEFT = 10              # stock "Next"
W_RIGHT = 9              # stock "Back"

# MAIN (page 3)
W_LIGHT = 0
W_WIFI = 1               # opens NETWORK
W_ESTOP = 2
W_LAST_PRINT = 3         # the picture of the last print (cp0 / b3)
LIGHT_PICC = ((11, 9), (12, 10))   # b0 (picc, picc2) off, on
RED = 63488              # pco of a temperature that is heating

# PRINTING (page 17) and PRINT_KB (page 18, keypad over the print page)
W_PRINT_STOP = 0
W_PRINT_PAUSE = 1
W_PRINT_FLOW = 2         # the screen sets sys0=0 first
W_PRINT_SPEED = 3        # the screen sets sys0=1 first
W_PRINT_LIGHT = 5
W_PRINT_KB_CLOSE = 12    # OK with empty input, or tapping the open tab
# PRINT_KB OK sends a 0x71 frame with page 17 and widget 2 (flow) or
# 3 (speed), value in percent.
TOGGLE_PICC = (67, 69)   # picc of b1 / b5 (normal, alternate)

# FILE_LIST (page 4)
FILES_PER_PAGE = 6
W_FILE_PREV = 9
W_FILE_NEXT = 10

# PREVIEW (page 5)
W_PREVIEW_BACK = 0
W_PREVIEW_PRINT = 1

# PRINT_STOP (page 53)
W_YES = 0
W_NO = 1

# SCREEN_SLEEP: every page's sleep timer sends "65 2B 01 FF FF FF".
SLEEP_EVENT = (SCREEN_SLEEP, 1)

# PRINT_ZOFFSET (page 19): Z offset during a print. Widgets 0-3 and 5
# work as on PRINTING.
PRINT_ZOFFSET = 19
W_PRINT_ZOFFSET = 4      # on PRINTING: open PRINT_ZOFFSET
W_ZOFFSET_STEP = {6: 0.01, 7: 0.05, 8: 0.1, 9: 0.5}
W_ZOFFSET_DOWN = 10      # SET_GCODE_OFFSET Z_ADJUST=-step
W_ZOFFSET_UP = 11        # SET_GCODE_OFFSET Z_ADJUST=+step
W_ZOFFSET_BACK = 12
ZOFFSET_STEP_PICC = ((70, 72), (71, 71))   # (picc, picc2) normal, selected

# Settings tab (navigation widget 37). The left column is the same on
# every settings page: 0 language, 1 network, 2 system, 4 versions, 5 more.
BOOT_SPLASH = 1          # full-screen picture shown while rebooting
POWER_OFF = 2            # full-screen picture shown while shutting down
LANGUAGE = 21            # language buttons work on the screen itself
SYSTEM_OK = 29
SYSTEM_ERR = 30          # Klipper in shutdown/error; t6 = its message
SLEEP_SET = 31           # sleep buttons work on the screen itself
UPDATE = 32              # used to show versions
MORE = 33
SERVICE = 34             # static QR code
NETWORK = 62
LANGUAGE_2 = 69
CONFIRM = 94             # t0 question, b0 yes, b1 no
SETTINGS_PAGES = (LANGUAGE, SYSTEM_OK, SYSTEM_ERR, SLEEP_SET, UPDATE, MORE,
                  SERVICE, NETWORK, LANGUAGE_2)
W_SET_COLUMN = {0: LANGUAGE, 1: NETWORK, 4: UPDATE, 5: MORE}
W_SET_SYSTEM = 2
W_MORE_SLEEP = 3
W_MORE_SERVICE = 6
W_MORE_REBOOT = 8        # stock: factory reset; here: restart the printer
W_SYS_SHUTDOWN = 6       # stock: export logs; here: shut the printer down
W_SYS_KLIPPER_RESTART = 7
W_SYS_FIRMWARE_RESTART = 8
W_CONFIRM_YES = 0
W_CONFIRM_NO = 1
NET_TAB_PICC = ((248, 245), (249, 249))   # (picc, picc2) inactive, active
NETWORK_HIDE = ("b8", "b9", "b10", "t8", "b20", "b21", "b22")

# Tools tab (navigation widget 36).
TOOL_SELECT = 95
SHAPER = 8
SHAPER_RUNNING = 9
SHAPER_DONE = 59
LEVEL = 14
LEVEL_RUNNING = 15
LEVEL_DONE = 61
LEVEL_WARNING = 73
W_TOOL_SCREWS = 0        # bed screws: not implemented
W_TOOL_LEVEL = 1
W_TOOL_SHAPER = 2
W_SHAPER_START = 3
W_SHAPER_BACK = 4
W_LEVEL_TEMP = 4         # 0x71 frame from the bed temperature keypad
W_LEVEL_BACK = 6
W_DONE_OK = 3            # SHAPER_DONE and LEVEL_DONE
W_WARNING_OK = 0
LEVEL_BED_MIN = 35
LEVEL_BED_MAX = 120
