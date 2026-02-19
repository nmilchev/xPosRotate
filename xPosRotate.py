from phBot import *
from threading import Timer
from datetime import datetime
import QtBind
import phBotChat
import urllib.request
import re
import os
import shutil
import time

pName = 'PosRotate'
pVersion = '2.0.6'
pUrl = 'https://raw.githubusercontent.com/nmilchev/xPosRotate/refs/heads/main/xPosRotate.py'

gui = QtBind.init(__name__, pName)

# -------------------------
# Globals
# -------------------------
TIMER_DURATION = 60  # 3600 = 1 hour

ENABLED = False
timer_start_time = 0
timer_running = False
paused = False
# Rotation System
active_location = None
rotation_order = []
current_rotation_index = 0
locations = ["","Location 1","Location 2","Location 3"]

SPECIAL_ITEMS = [
    "BearBoo",
    "CuteBunny",
    "Fire-Bred",
    "Immortal",
    "Craft The Min",
    "Double Dragon",
    "Acid",
    "God of Fight"
]

drop_counts = {name: 0 for name in SPECIAL_ITEMS}
seen_drop_uids = set()
total_special_drops = 0
_cbParty = False
_cbPlayer = False

# ===== HEADER BAR =====
QtBind.createLabel(gui, "══════════════════════════════", 5, 5)
QtBind.createLabel(gui, "  ⚡ FGW/HoW ROTATION MANAGER ⚡", 15, 18)
QtBind.createLabel(gui, "══════════════════════════════", 5, 32)
# ===== POSITION CONTROL PANEL =====

QtBind.createLabel(gui, "📍 Position control", 5, 50)
QtBind.createLabel(gui, "Training Slot:", 10, 75)
cmb_location = QtBind.createCombobox(gui, 80, 71, 100, 22)
btn = QtBind.createButton(gui, "save_selected", "💾 SAVE POSITION", 20, 105)
btn1 = QtBind.createButton(gui, "copy_selected", "🔙 BACK TO CENTER", 150, 105)
QtBind.createLabel(gui, "──────────────────────────────", 5, 135)

# ===== ROTATION ENGINE PANEL =====
QtBind.createLabel(gui, "🎯 Training Rotation", 10, 150)
spot1 = QtBind.createCheckBox(gui, "cb_1_clicked", "🔴 Inactive", 25, 175)
spot2 = QtBind.createCheckBox(gui, "cb_2_clicked", "🔴 Inactive", 25, 195)
spot3 = QtBind.createCheckBox(gui, "cb_3_clicked", "🔴 Inactive", 25, 215)
QtBind.createCheckBox(gui, "cbEnable_clicked", "Enabled", 325, 245)
QtBind.createLabel(gui, "──────────────────────────────", 5, 240)
# Checkbox map
checkbox_map = {
    "cb_1": (spot1, "Location 1"),
    "cb_2": (spot2, "Location 2"),
    "cb_3": (spot3, "Location 3"),
}
# ===== LIVE STATUS DASHBOARD =====
QtBind.createLabel(gui, "📊 Status Panel", 10, 255)
lblStatus = QtBind.createLabel(gui, "Mode: Idle", 25, 280)
lblTime = QtBind.createLabel(gui, "Remaining: 00:00:00", 25, 300)
btnStart = QtBind.createButton(gui, "btn_start_rotation", "✅ START", 150, 150)
btnStop = QtBind.createButton(gui, "btn_stop_rotation", "⛔ STOP", 150, 180)
btnRes = QtBind.createButton(gui, "btn_force_reset", "⏳ RESET ⏳", 150, 280)
btnPause = QtBind.createButton(gui, "btn_pause_rotation", "⏸ PAUSE", 150, 210)
QtBind.createLabel(gui, "══════════════════════════════", 5, 310)

# ===== Log =====
QtBind.createLabel(gui, "Plugin Log:", 280, 3)
lstLog = QtBind.createList(gui, 280, 25, 350, 260) 

# ===== RIGHT SIDE =====
vr = f"Version:{pVersion}"
QtBind.createLabel(gui, vr, 565, 5)
btnUpdate = QtBind.createButton(gui, "btn_update", "🔄 UPDATE 🔄", 630, 1)
QtBind.createLabel(gui, "<b>💼 Drops 💼</b>", 640, 28)
lstDrops = QtBind.createList(gui,632,45,88,140)
lblTotal = QtBind.createLabel(gui, 'Total Drops: 0', 635, 190)
QtBind.createLabel(gui, '<b>Notify:📞<b>', 635, 210)
cbParty = QtBind.createCheckBox(gui, "cbParty_clicked", "🟢 Party", 635, 225)
QtBind.setChecked(gui, cbParty, True)
cbPlayer = QtBind.createCheckBox(gui, "cbPlayer_clicked", "🔴 Player", 635, 240)
player_not = QtBind.createLineEdit(gui,"",632,260,88,20)

def cb_1_clicked(checked): handle_checkbox("cb_1", checked)
def cb_2_clicked(checked): handle_checkbox("cb_2", checked)
def cb_3_clicked(checked): handle_checkbox("cb_3", checked)

def cbParty_clicked(checked):
    global _cbParty
    _cbParty = checked
    if _cbParty:
        QtBind.setText(gui, cbParty, "🟢 Party")
    else:
        QtBind.setText(gui, cbParty, "🔴 Party")

def cbPlayer_clicked(checked):
    global _cbPlayer
    player_name = QtBind.text(gui, player_not).strip()
    
    if checked and not player_name:
        add_log("⚠ Enter player name first.")
        QtBind.setChecked(gui, cbPlayer, False)
        QtBind.setText(gui, cbPlayer, "🔴 Player")
        _cbPlayer = False
        return
    _cbPlayer = checked
    if _cbPlayer:
        QtBind.setText(gui, cbPlayer, f"🟢 {player_name}")
        QtBind.move(gui, player_not, 1000, 0)
    else:
        QtBind.setText(gui, cbPlayer, "🔴 Player")
        QtBind.move(gui, player_not, 632, 260)

def cbEnable_clicked(checked):
    global ENABLED
    ENABLED = True

start = "walk,6428,1108,0"
SCRIPT = """use,FGW - Hall of Warship
fgw,teleport
get_hole
walk,19483,6393,856
walk,19493,6379,856
walk,19508,6357,856
AttackArea2,40
walk,19519,6339,856
walk,19525,6321,856
AttackArea2,40
walk,19521,6303,856
walk,19501,6292,856
AttackArea2,40
walk,19481,6284,856
walk,19463,6288,856
AttackArea2,40
walk,19446,6306,856
walk,19439,6321,856
AttackArea2,40
walk,19442,6341,856
walk,19452,6353,856
AttackArea2,40
walk,19470,6364,856
walk,19478,6365,856
AttackArea2,40
walk,19464,6361,856
walk,19443,6359,856
walk,19427,6359,856
walk,19415,6364,895
walk,19397,6373,856
walk,19389,6385,856
walk,19386,6409,856
AttackArea2,40
walk,19379,6398,856
AttackArea2,40
walk,19369,6381,856
walk,19347,6367,856
AttackArea2,40
walk,19330,6366,856
walk,19314,6364,856
AttackArea2,40
walk,19297,6360,856
AttackArea2,40
walk,19278,6351,856
AttackArea2,40
walk,19265,6337,856
AttackArea2,40
walk,19265,6321,856
AttackArea2,40
walk,19265,6305,856
walk,19264,6287,856
AttackArea2,40
walk,19264,6270,856
AttackArea2,40
walk,19263,6251,856
AttackArea2,40
walk,19263,6234,856
AttackArea2,40
walk,19264,6214,856
walk,19263,6197,856
AttackArea2,40
walk,19264,6178,856
AttackArea2,40
walk,19261,6162,856
AttackArea2,40
walk,19265,6145,856
walk,19263,6122,856
AttackArea2,40
walk,19265,6101,856
walk,19265,6080,856
walk,19263,6064,856
AttackArea2,40
walk,19260,6050,856
walk,19268,6035,856
AttackArea2,40
walk,19269,6026,856
walk,19271,6010,856
AttackArea2,40
walk,19286,6016,856
walk,19304,6018,856
AttackArea2,40
walk,19324,6023,856
walk,19333,6041,856
AttackArea2,40
walk,19326,6065,856
walk,19324,6087,856
AttackArea2,40
walk,19322,6110,856
walk,19323,6128,856
AttackArea2,40
walk,19325,6145,856
walk,19326,6163,856
AttackArea2,40
walk,19327,6180,856
walk,19327,6196,895
walk,19328,6219,858
walk,19328,6233,858
walk,19345,6235,858
walk,19364,6235,858
walk,19384,6236,877
walk,19399,6235,883
AttackArea2,40
walk,19399,6235,883
AttackArea2,40
wait,10000
walk,19386,6237,877
walk,19362,6236,858
walk,19346,6236,858
walk,19329,6236,858
walk,19327,6253,858
walk,19328,6276,883
walk,19340,6282,877
walk,19359,6283,858
walk,19377,6281,858
walk,19393,6284,858
walk,19409,6292,895
walk,19426,6302,856
walk,19442,6311,856 
AttackArea2,40
walk,19438,6331,856
walk,19446,6347,856  
AttackArea2,40
walk,19456,6359,856
walk,19473,6363,856 
AttackArea2,40
walk,19486,6364,856
walk,19502,6356,856
AttackArea2,40
walk,19456,6359,856
walk,19473,6363,856 
AttackArea2,40
walk,19438,6331,856
walk,19446,6347,856 
AttackArea2,40
walk,19426,6302,856
walk,19442,6311,856  
AttackArea2,40
walk,19452,6297,856
AttackArea2,40
walk,19466,6287,856
AttackArea2,40
walk,19486,6289,856
AttackArea2,40
walk,19503,6297,856
AttackArea2,40
walk,19515,6311,856
walk,19517,6329,856
walk,19520,6343,856
walk,19530,6351,856
AttackArea2,40
walk,19578,6389,856
walk,19579,6426,856
AttackArea2,40
walk,19584,6375,856
walk,19593,6365,856
walk,19615,6362,856
AttackArea2,40
walk,19630,6361,856
walk,19647,6362,856
walk,19664,6360,856
AttackArea2,40
walk,19680,6355,856
walk,19691,6346,856
walk,19698,6329,855
AttackArea2,40
walk,19697,6314,855
walk,19696,6300,856
walk,19698,6286,856
AttackArea2,40
walk,19697,6268,856
walk,19697,6254,856
walk,19698,6237,856
AttackArea2,40
walk,19697,6217,856
walk,19698,6203,856
walk,19697,6189,856
AttackArea2,40
walk,19697,6173,856
walk,19698,6155,856
walk,19698,6135,856
AttackArea2,40
walk,19697,6119,856
walk,19697,6102,856
walk,19698,6085,856
AttackArea2,40
walk,19698,6065,856
walk,19698,6048,856
walk,19695,6031,856
AttackArea2,40
walk,19680,6021,856
AttackArea2,40
walk,19663,6015,856
walk,19650,6016,856
AttackArea2,40
walk,19637,6028,856
walk,19630,6043,856
AttackArea2,50
walk,19647,6053,856
walk,19647,6068,856
walk,19647,6080,856
AttackArea2,40
walk,19646,6098,856
walk,19647,6116,856
walk,19646,6128,856
AttackArea2,40
walk,19645,6146,856
walk,19641,6164,856
AttackArea2,40
walk,19638,6179,856
AttackArea2,40
walk,19638,6194,894
walk,19638,6206,895
walk,19637,6230,858
walk,19624,6235,858
walk,19610,6235,858
walk,19592,6236,858
walk,19581,6236,877
walk,19566,6236,883
AttackArea2,50
walk,19566,6236,883
AttackArea2,50
wait,10000
walk,19577,6236,877
walk,19594,6236,858
walk,19611,6236,858
walk,19624,6236,858
walk,19637,6237,858
walk,19639,6248,858
walk,19638,6267,877
walk,19638,6282,883
walk,19625,6282,877
walk,19609,6282,858
walk,19595,6282,858
walk,19579,6283,858
walk,19569,6285,858
walk,19556,6292,895
walk,19539,6301,856
walk,19525,6308,856
AttackArea2,40
walk,19522,6321,856
walk,19519,6334,856
AttackArea2,40
walk,19516,6348,856
walk,19507,6361,856
AttackArea2,40
walk,19484,6367,856
walk,19465,6363,856
AttackArea2,40
walk,19450,6353,856
walk,19443,6345,856
AttackArea2,40
walk,19434,6333,856
walk,19435,6322,856
AttackArea2,40
walk,19443,6306,856
walk,19456,6296,856
AttackArea2,40
walk,19464,6289,856
walk,19478,6286,856
AttackArea2,40
walk,19490,6284,856
walk,19508,6292,856
AttackArea2,40
walk,19515,6300,856
walk,19519,6313,856
AttackArea2,40
walk,19509,6306,855
walk,19493,6291,856
walk,19484,6279,856
walk,19483,6266,856
walk,19483,6252,856
walk,19483,6230,904
walk,19483,6221,967
walk,19482,6210,1036
walk,19482,6201,1095
walk,19483,6187,1115
AttackArea2,50
walk,19483,6187,1115
AttackArea2,50
wait,20000
walk,19483,6178,1115
walk,19497,6181,1115
walk,19475,6183,1115
use,returnscroll
report
stop
"""

# =========================
# GAME STATE
# =========================
def is_ingame():
    return get_character_data() is not None
def getPath():
    return get_config_dir()+pName+"\\"
# -------------------------
# Helpers
# -------------------------
log_buffer = []
MAX_LOGS = 15

def add_log(text):
    global log_buffer
    timestamp = datetime.now().strftime('%H:%M:%S')
    entry = f"[{timestamp}] {text}"

    log_buffer.append(entry)
    if len(log_buffer) > MAX_LOGS:
        log_buffer.pop(0)
        
    QtBind.clear(gui, lstLog)
    for line in log_buffer:
        QtBind.append(gui, lstLog, line)

def get_latest_version(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': "Mozilla/5.0"})
        with urllib.request.urlopen(req) as w:
            pyCode = str(w.read().decode("utf-8"))
            if re.search("\npVersion = [0-9.'\"]*", pyCode):
                return re.search("\npVersion = ([0-9a-zA-Z.'\"]*)", pyCode).group(0)[13:-1], pyCode
    except:
        pass
    return None, None

def compare_version(a, b):
    a = tuple(map(int, a.split(".")))
    b = tuple(map(int, b.split(".")))
    return a < b

def btn_update():
    global pVersion, pUrl
    if not pUrl:
        add_log("❌ No update URL defined.")
        return
    add_log("🔎 Checking for updates...")
    latest_version, new_code = get_latest_version(pUrl)
    if not latest_version:
        add_log("❌ Could not check version.")
        return
    if not compare_version(pVersion, latest_version):
        add_log("✔ Plugin already up to date.")
        return
    try:
        current_file = os.path.realpath(__file__)
        backup_file = current_file + ".bkp"
        # Create backup
        shutil.copyfile(current_file, backup_file)
        # Overwrite current plugin
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(new_code)
        add_log(f"✅ Updated successfully to v{latest_version}")
        add_log("♻ Please reload the plugin.")
    except Exception as e:
        add_log("❌ Update failed:")
        add_log(str(e))

def dropps():
    global total_special_drops
    drops = get_drops()
    if not drops:
        return
    for uid, drop in drops.items():
        if uid in seen_drop_uids:
            continue
        seen_drop_uids.add(uid)
        item_name = drop.get('name', '')
        quantity = drop.get('quantity', 1)
        for name in SPECIAL_ITEMS:
            if name.lower() in item_name.lower():
                drop_counts[name] += quantity
                total_special_drops += quantity

                text = f"{name} x{quantity}"
                QtBind.append(gui, lstDrops, text)
                QtBind.setText(gui, lblTotal, f"Total Drops: {total_special_drops}")
                break

def send_report():
    global _cbParty, _cbPlayer, total_special_drops
    player_name = QtBind.text(gui, player_not).strip()
    report_parts = []
    for name, count in drop_counts.items():
        if count > 0:
            report_parts.append(f"{name} x{count}")
    report_text = " | ".join(report_parts)
    
    if total_special_drops == 0:
        message = "Run Finished with 0 drops 😭"
        add_log("🏃🏃🏃 Run Finished with 0 drops 😭")
    else:
        message = f"Run finished! Drops:-> {report_text}"
        add_log("🏃🏃🏃 Run finished!🏃🏃🏃")
        add_log(f"🏷️🏷️🏷️: -> {report_text}")
    # Send to Party if enabled
    if _cbParty:
        phBotChat.Party(message)
    # Send to Player if enabled
    if _cbPlayer:
        if player_name:
            phBotChat.Private(player_name, message)

def btn_pause_rotation():
    global paused
    if not timer_running:
        add_log("⚠ We didn't even started ...  🤔 Nothing is running.")
        return
    paused = not paused
    if paused:
        stop_bot()
        QtBind.setText(gui, lblStatus, "Mode: Paused")
        add_log("⏸ Rotation paused.")
    else:
        QtBind.setText(gui, lblStatus, "Mode: Idle")
        add_log("▶ Rotation resumed.")
        if get_remaining() <= 0:
            add_log("⏳ Time was over during pause.")
            add_log("⏳ Continuing rotation...")

def format_time(seconds):
    seconds = int(seconds); hours = seconds // 3600; minutes = (seconds % 3600) // 60;  secs = seconds % 60
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, secs)

def get_elapsed():
    return time.time() - timer_start_time

def get_remaining():
    remaining = TIMER_DURATION - get_elapsed()
    return max(0, remaining)

def handle_checkbox(name, checked):
    global timer_running
    element, label = checkbox_map[name]
    if checked:
        QtBind.setText(gui, element, "🟢 Active")
    else:
        QtBind.setText(gui, element, "🔴 Inactive")
    #rebuild_rotation_list()

def rebuild_rotation_list():
    global rotation_order, current_rotation_index
    
    rotation_order = []
    for key in checkbox_map:
        element, label = checkbox_map[key]
        if QtBind.isChecked(gui, element):
            rotation_order.append(label)

    if current_rotation_index >= len(rotation_order):
        current_rotation_index = 0
    add_log(f"🔁 Refreshing scripts")


def btn_start_rotation():
    global timer_running, timer_start_time, current_rotation_index, ENABLED

    ENABLED = True
    rebuild_rotation_list()

    if not rotation_order:
        add_log("❌ No active locations selected.")
        QtBind.setText(gui, lblStatus, "Mode: Idle")
        return

    if timer_running:
        add_log("⚠ Rotation already running.")
        return

    current_rotation_index = 0
    start_training(rotation_order[current_rotation_index])
    
    QtBind.setText(gui, lblStatus, "Mode: Active")
    add_log("▶ Rotation started.")

def btn_stop_rotation():
    global timer_running, timer_start_time, current_rotation_index, ENABLED, paused
    stop_bot()
    paused = False
    ENABLED = False
    timer_running = False
    timer_start_time = 0
    current_rotation_index = 0
    QtBind.setText(gui, lblStatus, "Mode: Stopped")
    QtBind.setText(gui, lblTime, "Remaining: 00:00:00")
    add_log("⛔ FULL STOP executed. All timers and rotations stopped.")

def btn_force_reset():
    global timer_running, timer_start_time, current_rotation_index
    
    rebuild_rotation_list()
    
    if not rotation_order: 
        add_log("❌ No active locations selected.")
        QtBind.setText(gui, lblStatus, "Mode: Idle (No Locations)")
        return
    if timer_running: 
        timer_start_time = 0
        timer_running = False
        add_log("⚠ Timer has been force reseted !!! ⚠")
        return
    add_log("⚠ Timer isnt started / nothing to reset !!! ⚠")

def start_training(location_name):
    global timer_start_time, timer_running
    if not load_training_script(location_name):
        add_log(f"🟢 Bot started. Using {location_name}")
        return
    add_log(f"🔴🔴🔴 Opps, Seems we cant can't start.")

def load_training_script(location_name):
    data = get_character_data()
    if not data:
        add_log("❌ Not in game.")
        return False
    name = data['name']
    filename = f"{name}_{location_name.replace(' ', '_')}.txt"
    filepath = os.path.join(getPath(), filename)

    if not os.path.exists(filepath):
        add_log(f"❌ Script not found for {location_name}")
        return False
    stop_bot()
    set_training_script(filepath)
    Timer(1.0,start_bot).start()
    return 

def _rebuild_combos():
    try:
        QtBind.clear(gui, cmb_location)
        for u in locations:
            QtBind.append(gui, cmb_location, u)
        if locations:
            QtBind.setText(gui, cmb_location, locations[0])
    except:
        pass

def btn_start_clicked():
    global timer_start_time, timer_running, seen_drop_uids, drop_counts, total_special_drops

    if timer_running:
        add_log("⏱Going back. Maybe we missed some mobs !?")
        return
        
    timer_start_time = time.time()
    timer_running = True
    
    seen_drop_uids = set()
    drop_counts = {name: 0 for name in SPECIAL_ITEMS}
    total_special_drops = 0

    QtBind.clear(gui, lstDrops)
    QtBind.setText(gui, lblTotal, 'Total Drops: 0')
    QtBind.setText(gui, lblStatus, "Status: Running")
    add_log("⏱ Entered through the portal. ⏱")

def copy_selected():
    line = "path,25000,6428,1108,0"
    add_log("📍 GOING BACK TO Jangan CENTER:")
    start_script(line)

def save_selected():
    data = get_character_data()
    name = data['name']
    selected = QtBind.text(gui, cmb_location)

    if not selected:
        add_log("❌ No location selected!")
        return
        
    p = get_position()
    region = p['region']
    x = int(p['x'])
    y = int(p['y'])
    z = int(p['z'])

    line = f"path,{region},{x},{y},{z}"

    # Create separate file per location
    
    filename = f"{name}_{selected.replace(' ', '_')}.txt"
    filepath = os.path.join(getPath(), filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(start + "\n" + line + "\n" + SCRIPT)
    add_log(f"💾 Saved position for {selected}")

# -------------------------
# Event Loop
# -------------------------
def event_loop():
    global timer_running, current_rotation_index
    #add_log("⏱ DEBUG not dds")
    dropps(); 
    if not ENABLED: 
        #add_log("⏱ DEBUG not enabled")
        return 
    if not timer_running: 
        return 

    remaining = get_remaining()
    QtBind.setText(gui, lblTime, f"Remaining: {format_time(remaining)}")

    if remaining <= 0: 
        if paused:
            QtBind.setText(gui, lblStatus, "Mode: Paused (Time Over)")
            return
        add_log("⏱ It's time to move on. Changing script.")
            
        timer_running = False
        
        rebuild_rotation_list()
        
        if not rotation_order: 
            add_log("❌ No active locations.")
            return 
        
        current_rotation_index += 1
        if current_rotation_index >= len(rotation_order): 
            current_rotation_index = 0
            
        next_location = rotation_order[current_rotation_index]
        start_training(next_location)
    return 


# ------------------------
# External Call Function
# ------------------------
def get_hole(a): 
    btn_start_clicked()
    return True
def report(a): 
    send_report()
    return True


# Plugin loaded
add_log("Plugin: "+pName+" ❴ by KriKo ❵ v"+pVersion+" successfully loaded ✔")

if os.path.exists(getPath()):
    # Adding RELOAD plugin support
    _rebuild_combos()
else:
    # Creating configs folder
    os.makedirs(getPath())
    _rebuild_combos()
    add_log('Plugin: '+pName+' folder has been created')
