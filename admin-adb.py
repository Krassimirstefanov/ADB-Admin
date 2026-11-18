#!/usr/bin/env python3
# Android ADB Admin - Termux/Linux edition
# Use for Educational Purpose Only
import subprocess
import shutil
import sys
import os
import time
import re
import datetime
import csv
import html
import socket
import struct
from pathlib import Path
# ----------------- Config / Colors -----------------
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
CYAN = "\033[1;36m"
RESET = "\033[0m"
BANNER = r"""
        .-----------------------.
        |    o             o    |
        |                       |
        |        A D B          |
        '----------+--+---------'
                   |  |

          ANDROID ADB ADMIN
"""
HEADER_LINES = [
    " Android ADB Admin | Termux/Linux",
    " Android Device Management & Security Tool ",
    " Use only on devices you own or administer "

]

# ----------------- Language / Preferences -----------------
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "android-adb-admin")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.txt")
LANG = "en"

TR = {
    "en": {
        "choose_lang": "Choose language / Choisir la langue",
        "english": "English",
        "french": "Français",
        "main_title": "MAIN MENU",
        "select": "Select",
        "back": "Back",
        "quit": "Quit",
        "invalid": "Invalid option.",
        "settings_lang": "Language",
        "lang_changed": "Language changed.",
        "apps": "Applications",
        "permissions": "Permissions + AppOps",
        "ports": "Open ports / network",
        "disable_app": "Disable application",
        "enable_app": "Enable application",
        "exports": "SMS + call logs export",
        "profiles": "Quick profiles",
        "shell": "Interactive ADB shell",
        "launcher": "Launcher / home screen",
        "android_manager": "Android Manager",
    },
    "fr": {
        "choose_lang": "Choisir la langue / Choose language",
        "english": "English",
        "french": "Français",
        "main_title": "MENU PRINCIPAL",
        "select": "Choisir",
        "back": "Retour",
        "quit": "Quitter",
        "invalid": "Option invalide.",
        "settings_lang": "Langue",
        "lang_changed": "Langue modifiée.",
        "apps": "Applications",
        "permissions": "Permissions + AppOps",
        "ports": "Ports ouverts / réseau",
        "disable_app": "Désactiver une application",
        "enable_app": "Activer une application",
        "exports": "Export SMS + appels",
        "profiles": "Profils rapides",
        "shell": "Shell ADB interactif",
        "launcher": "Launcher / écran d'accueil",
        "android_manager": "Gestion Android",
    }
}

def t(key):
    return TR.get(LANG, TR["en"]).get(key, key)

def _save_language():
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("language=" + LANG + "\n")
    except OSError:
        pass

def _load_language():
    global LANG
    try:
        if os.path.exists(CONFIG_FILE):
            for line in Path(CONFIG_FILE).read_text(encoding="utf-8").splitlines():
                if line.startswith("language="):
                    value = line.split("=", 1)[1].strip()
                    if value in ("en", "fr"):
                        LANG = value
                        return True
    except OSError:
        pass
    return False

def choose_language(first_run=False):
    global LANG
    print("\n" + t("choose_lang"))
    print("[1] English")
    print("[2] Français")
    if not first_run:
        print("[0] " + t("back"))
    while True:
        choice = input("> ").strip()
        if choice == "1":
            LANG = "en"
            _save_language()
            print(TR["en"]["lang_changed"])
            return
        if choice == "2":
            LANG = "fr"
            _save_language()
            print(TR["fr"]["lang_changed"])
            return
        if choice == "0" and not first_run:
            return
        print(t("invalid"))

# ----------------- Helpers -----------------
def check_dependency(cmd_name, apt_pkg_name=None):
    path = shutil.which(cmd_name)
    return bool(path)
def run_cmd(cmd, capture=False):
    try:
        if capture:
            res = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.stdout.strip(), res.stderr.strip()
        else:
            return subprocess.call(cmd, shell=True)
    except Exception as e:
        return None
def adb_available():
    return check_dependency("adb")
def scrcpy_available():
    return check_dependency("scrcpy")
def clear_screen():
    os.system("clear" if shutil.which("clear") else "cls")
def print_banner():
    clear_screen()
    print(GREEN + BANNER + RESET)
    for line in HEADER_LINES:
        print(GREEN + line.center(55) + RESET)
    print(CYAN + "-"*59 + RESET)
    print()
# ----------------- ADB Helpers -----------------
def adb_devices_list():
    out, err = run_cmd("adb devices", capture=True)
    if out is None:
        return []
    lines = out.splitlines()
    devices = []
    for line in lines[1:]:
        line = line.strip()
        if line:
            parts = line.split()
            devices.append(parts[0])
    return devices
def get_selected_device():
    devices = adb_devices_list()
    if not devices:
        print(RED + "[!] No device detected." + RESET)
        print(YELLOW + "Please connect your device via USB and enable USB Debugging (Developer Options)." + RESET)
        print(YELLOW + "Settings -> Developer options -> USB debugging (enable)." + RESET)
        input("\nPress Enter after connecting device to continue...")
        return None
    if len(devices) == 1:
        return devices[0]
    else:
        print(CYAN + "[+] Multiple devices detected:" + RESET)
        for i, dev in enumerate(devices, 1):
            print(f"{i}. {dev}")
        while True:
            try:
                choice = int(input("Select device number: "))
                if 1 <= choice <= len(devices):
                    return devices[choice - 1]
                else:
                    print(RED + "Invalid choice." + RESET)
            except ValueError:
                print(RED + "Enter a number." + RESET)
# ----------------- Device Connection Logging -----------------
connected_devices = {}  # device_id: connect_time

def update_device_logs():
    current_devices = adb_devices_list()
    now = datetime.datetime.now()
    # Check for disconnected
    for dev in list(connected_devices.keys()):
        if dev not in current_devices:
            start = connected_devices.pop(dev)
            duration = now - start
            with open("connection_log.txt", "a") as f:
                f.write(f"{dev} disconnected at {now}, connected for {duration}\n")
    # Check for new connected
    for dev in current_devices:
        if dev not in connected_devices:
            connected_devices[dev] = now
            with open("connection_log.txt", "a") as f:
                f.write(f"{dev} connected at {now}\n")

def option_view_connection_history():
    update_device_logs()  # Update before viewing
    if not os.path.exists("connection_log.txt"):
        print(YELLOW + "No connection log yet." + RESET)
        return
    print(CYAN + "[*] Device Connection History:" + RESET)
    with open("connection_log.txt", "r") as f:
        print(f.read())
    # Show current connections
    if connected_devices:
        now = datetime.datetime.now()
        print(CYAN + "[*] Currently Connected:" + RESET)
        for dev, start in connected_devices.items():
            duration = now - start
            print(f"{dev} connected since {start}, duration so far: {duration}")
# ----------------- Option Implementations -----------------
def option_check_device():
    print(CYAN + "\n[+] Checking for connected devices..." + RESET)
    device = get_selected_device()
    if device is None:
        return
    print(GREEN + f"[+] Device found: {device}" + RESET)
    print(CYAN + "[*] Gathering device info..." + RESET)
    model, _ = run_cmd(f"adb -s {device} shell getprop ro.product.model", capture=True)
    android_ver, _ = run_cmd(f"adb -s {device} shell getprop ro.build.version.release", capture=True)
    battery_info, _ = run_cmd(f"adb -s {device} shell dumpsys battery | grep level", capture=True)
    if model: print(f"Model: {model}")
    if android_ver: print(f"Android: {android_ver}")
    if battery_info: print(f"Battery: {battery_info}")
    else:
        batt, _ = run_cmd(f"adb -s {device} shell dumpsys battery", capture=True)
        for line in (batt or "").splitlines():
            if "level" in line:
                print(line.strip())
    print()
def option_connect_device():
    print(CYAN + "\n[+] Running 'adb devices'..." + RESET)
    usb_devices = [d for d in adb_devices_list() if ':' not in d]
    enable_tcpip = input("Do you want to enable ADB over WiFi (requires USB, only first time)? (y/n): ").strip().lower()
    if enable_tcpip == 'y':
        if not usb_devices:
            print(RED + "[-] No device detected via USB." + RESET)
            print(YELLOW + "Please connect your device via USB and enable USB Debugging (Developer Options)." + RESET)
            return
        if len(usb_devices) > 1:
            print(CYAN + "[+] Multiple USB devices detected:" + RESET)
            for i, dev in enumerate(usb_devices, 1):
                print(f"{i}. {dev}")
            while True:
                try:
                    choice = int(input("Select USB device number for TCPIP mode: "))
                    if 1 <= choice <= len(usb_devices):
                        usb_device = usb_devices[choice - 1]
                        break
                    print(RED + "Invalid choice." + RESET)
                except ValueError:
                    print(RED + "Enter a number." + RESET)
        else:
            usb_device = usb_devices[0]
        print(GREEN + "[+] Device detected via USB. Switching adb to tcpip mode on port 5555..." + RESET)
        run_cmd(f"adb -s {usb_device} tcpip 5555")
    ip = input("Enter device IP address (e.g. 192.168.1.10): ").strip()
    if not ip:
        print(RED + "No IP provided. Aborting connect." + RESET)
        return
    print(CYAN + f"Connecting to {ip}:5555 ..." + RESET)
    out, err = run_cmd(f"adb connect {ip}:5555", capture=True)
    if "connected" in out.lower() or "already" in out.lower():
        print(GREEN + "[+] Connected successfully over Wi-Fi." + RESET)
        run_cmd("adb devices")
    else:
        print(RED + "[-] Could not connect. Output:" + RESET)
        print(out or err)
def option_disconnect_device():
    print(CYAN + "\n[*] Disconnecting adb connections..." + RESET)
    tcp_devices = [d for d in adb_devices_list() if ':' in d]
    if not tcp_devices:
        print(YELLOW + "[-] No wireless devices connected." + RESET)
        print("\nCurrent adb devices:")
        run_cmd("adb devices")
        return
    if len(tcp_devices) == 1:
        disconnect_cmd = f"adb disconnect {tcp_devices[0]}"
    else:
        print(CYAN + "[+] Multiple wireless devices:" + RESET)
        for i, dev in enumerate(tcp_devices, 1):
            print(f"{i}. {dev}")
        print("0. All")
        while True:
            try:
                choice = int(input("Select number to disconnect (0 for all): "))
                if choice == 0:
                    disconnect_cmd = "adb disconnect"
                    break
                elif 1 <= choice <= len(tcp_devices):
                    disconnect_cmd = f"adb disconnect {tcp_devices[choice - 1]}"
                    break
                print(RED + "Invalid choice." + RESET)
            except ValueError:
                print(RED + "Enter a number." + RESET)
    out, err = run_cmd(disconnect_cmd, capture=True)
    print(GREEN + "[+] Disconnect issued." + RESET)
    print("\nCurrent adb devices:")
    run_cmd("adb devices")
def option_screen_recording():
    device = get_selected_device()
    if device is None:
        return
    dur = input("Enter recording duration (e.g. '15s' or '30' for seconds): ").strip()
    if dur.endswith("s"):
        dur_val = dur[:-1]
    else:
        dur_val = dur
    try:
        dsec = int(dur_val)
    except:
        print(RED + "Invalid duration. Enter seconds as integer (e.g. 15)." + RESET)
        return
    filename = "record.mp4"
    print(CYAN + f"[*] Starting screenrecord for {dsec} seconds..." + RESET)
    cmd = f"adb -s {device} shell screenrecord --time-limit {dsec} /sdcard/{filename}"
    rc = run_cmd(cmd)
    if rc is None:
        print(YELLOW + "Fallback recording method..." + RESET)
        run_cmd(f"adb -s {device} shell screenrecord /sdcard/{filename} &")
        time.sleep(dsec)
        run_cmd(f"adb -s {device} shell pkill -f screenrecord")
    print(CYAN + "[*] Pulling recording to current directory..." + RESET)
    run_cmd(f"adb -s {device} pull /sdcard/{filename} ./")
    print(GREEN + f"[+] Recording saved as ./{filename}" + RESET)
    view = input("Do you want to open the recording now? (y/n): ").strip().lower()
    if view == "y":
        opener = shutil.which("xdg-open") or "xdg-open"
        run_cmd(f"{opener} {filename}")
def option_screen_mirror():
    device = get_selected_device()
    if device is None:
        return
    if not scrcpy_available():
        print(RED + "[!] scrcpy not found." + RESET)
        print(YELLOW + "Install with: sudo apt install scrcpy -y" + RESET)
        return
    print(CYAN + "[*] Launching scrcpy..." + RESET)
    run_cmd(f"scrcpy -s {device}")
def option_show_apk_list():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Fetching installed packages..." + RESET)
    out, err = run_cmd(f"adb -s {device} shell pm list packages -f", capture=True)
    if not out:
        print(RED + "No output. Is device connected?" + RESET)
        return
    # Clean: extract only package names
    cleaned_lines = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            parts = line.split("=")
            if len(parts) > 1:
                pkg = parts[-1]
                cleaned_lines.append(pkg)
    print(CYAN + "[+] Installed Package Names:" + RESET)
    for pkg in cleaned_lines:
        print(pkg)
    print(f"\nTotal: {len(cleaned_lines)} packages")
    save = input("\nDo you want to save the clean list to apk_list.txt? (y/n): ").strip().lower()
    if save == "y":
        with open("apk_list.txt", "w") as f:
            f.write("\n".join(cleaned_lines) + "\n")
        print(GREEN + "[+] Saved clean list to ./apk_list.txt" + RESET)
def option_take_screenshot():
    device = get_selected_device()
    if device is None:
        return
    remote = "/sdcard/screen.png"
    local = "screen.png"
    print(CYAN + "[*] Taking screenshot..." + RESET)
    run_cmd(f"adb -s {device} shell screencap -p {remote}")
    print(CYAN + "[*] Pulling screenshot..." + RESET)
    run_cmd(f"adb -s {device} pull {remote} ./")
    print(GREEN + f"[+] Screenshot saved as ./{local}" + RESET)
    view = input("Do you want to open the screenshot now? (y/n): ").strip().lower()
    if view == "y":
        opener = shutil.which("xdg-open") or "xdg-open"
        run_cmd(f"{opener} {local}")
def option_power_off():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Sending power off command..." + RESET)
    out, err = run_cmd(f"adb -s {device} shell reboot -p", capture=True)
    if err:
        print(RED + "[-] Error powering off device:" + RESET)
        print(err)
    else:
        print(GREEN + "[+] Device is powering off." + RESET)
def option_install_apk():
    device = get_selected_device()
    if device is None:
        return
    apk_path = input("Enter path to APK file (e.g., ./app.apk): ").strip()
    if not os.path.isfile(apk_path):
        print(RED + "[-] File does not exist." + RESET)
        return
    print(CYAN + "[*] Installing APK..." + RESET)
    out, err = run_cmd(f"adb -s {device} install {apk_path}", capture=True)
    if "Success" in out:
        print(GREEN + "[+] APK installed successfully." + RESET)
    else:
        print(RED + "[-] Failed to install APK:" + RESET)
        print(err or out)
def _package_label(device, pkg):
    out, _ = run_cmd(f"adb -s {device} shell dumpsys package {pkg} | grep -m1 'application-label:'", capture=True)
    if out and ':' in out:
        return out.split(':', 1)[1].strip().strip("'\"") or pkg
    # Android cmd package may not expose labels; provide a useful fallback
    return pkg.split('.')[-1].replace('_', ' ').title()

def _package_utility(pkg):
    known = {
        "com.google.android.gms": "Google Play services / Android APIs",
        "com.android.vending": "Google Play Store",
        "com.openai.chatgpt": "ChatGPT assistant",
        "com.xiaomi.payment": "Xiaomi payment / carrier-payment component",
        "com.xiaomi.mi_connect_service": "Xiaomi device connectivity / continuity",
        "com.xiaomi.hypercomm": "Xiaomi connectivity service",
        "com.miui.gallery": "Xiaomi Gallery / photos and videos",
        "com.android.settings": "Android system settings",
        "com.android.phone": "Telephony, SIM and mobile network",
        "com.android.chrome": "Chrome web browser",
    }
    if pkg in known:
        return known[pkg]
    if pkg.startswith(('com.android.', 'android.')): return "Android system component"
    if pkg.startswith(('com.google.', 'com.google.android.')): return "Google component/application"
    if pkg.startswith(('com.miui.', 'com.xiaomi.')): return "Xiaomi/HyperOS component/application"
    return "Unknown / verify before modifying"

def _list_packages(device, third_party=False):
    flag = " -3" if third_party else ""
    out, _ = run_cmd(f"adb -s {device} shell pm list packages{flag}", capture=True)
    return sorted([x.split(':',1)[1].strip() for x in (out or '').splitlines() if x.startswith('package:')])

def _choose_package(device, title="Applications", third_party=False):
    packages = _list_packages(device, third_party)
    if not packages:
        print(RED + "[-] No packages returned." + RESET); return None
    print(CYAN + f"\n=== {title} ===" + RESET)
    print(f"{'N°':>4}  {'Application':<25} {'Package':<45} Utility")
    print('-'*110)
    rows=[]
    for i,pkg in enumerate(packages,1):
        label=_package_label(device,pkg)
        util=_package_utility(pkg)
        rows.append((pkg,label,util))
        print(f"{i:>4}  {label[:25]:<25} {pkg[:45]:<45} {util}")
    raw=input("\nChoose number (0 = cancel): ").strip()
    if raw == '0': return None
    try:
        n=int(raw)
        if 1 <= n <= len(rows): return rows[n-1]
    except ValueError: pass
    print(RED + "Invalid selection." + RESET); return None

def option_delete_apk():
    device = get_selected_device()
    if device is None: return
    selected=_choose_package(device, "Installed applications")
    if not selected: return
    package,label,util=selected
    path,_=run_cmd(f"adb -s {device} shell pm path {package}",capture=True)
    system = bool(path and ('/system/' in path or '/product/' in path or '/vendor/' in path or '/system_ext/' in path))
    print(f"\nApplication : {label}\nPackage     : {package}\nUtility     : {util}\nType        : {'System/preinstalled' if system else 'User application'}")
    print("\n[1] Disable for user 0\n[2] Uninstall for user 0\n[3] Force stop\n[4] Show permissions\n[5] Launcher icon / Icône écran d'accueil\n[0] Cancel")
    act=input("Action: ").strip()
    if act=='1': cmd=f"adb -s {device} shell pm disable-user --user 0 {package}"; desc="Disable"
    elif act=='2': cmd=f"adb -s {device} shell pm uninstall --user 0 {package}"; desc="Uninstall for user 0"
    elif act=='3': cmd=f"adb -s {device} shell am force-stop {package}"; desc="Force stop"
    elif act=='4':
        out,_=run_cmd(f"adb -s {device} shell dumpsys package {package}",capture=True)
        lines=[x.strip() for x in (out or '').splitlines() if 'android.permission.' in x or 'granted=' in x]
        print('\n'.join(lines) if lines else 'No permission details available.'); return
    elif act=='5':
        manager_launcher()
        return
    else: return
    confirm=input(f"{desc} {label}? (y/N): ").strip().lower()
    if confirm!='y': print(YELLOW+'Cancelled.'+RESET); return
    out,err=run_cmd(cmd,capture=True); print((out or err or 'Done.'))

def option_pull_file():
    device = get_selected_device()
    if device is None:
        return
    remote_path = input("Enter remote file path (e.g., /sdcard/file.txt): ").strip()
    local_path = input("Enter local destination path (e.g., ./file.txt): ").strip()
    if not remote_path or not local_path:
        print(RED + "[-] Both remote and local paths are required." + RESET)
        return
    print(CYAN + "[*] Pulling file..." + RESET)
    out, err = run_cmd(f"adb -s {device} pull {remote_path} {local_path}", capture=True)
    if err and "error" in err.lower():
        print(RED + "[-] Failed to pull file:" + RESET)
        print(err)
    else:
        print(GREEN + f"[+] File pulled to {local_path}" + RESET)
def option_push_file():
    device = get_selected_device()
    if device is None:
        return
    local_path = input("Enter local file path (e.g., ./file.txt): ").strip()
    remote_path = input("Enter remote destination path (e.g., /sdcard/file.txt): ").strip()
    if not os.path.isfile(local_path):
        print(RED + "[-] Local file does not exist." + RESET)
        return
    if not remote_path:
        print(RED + "[-] Remote path is required." + RESET)
        return
    print(CYAN + "[*] Pushing file..." + RESET)
    out, err = run_cmd(f"adb -s {device} push {local_path} {remote_path}", capture=True)
    if err and "error" in err.lower():
        print(RED + "[-] Failed to push file:" + RESET)
        print(err)
    else:
        print(GREEN + f"[+] File pushed to {remote_path}" + RESET)
def option_send_sms():
    device = get_selected_device()
    if device is None:
        return
    phone_number = input("Enter phone number (e.g., +1234567890): ").strip()
    message = input("Enter message to send: ").strip()
    if not phone_number or not message:
        print(RED + "[-] Phone number and message are required." + RESET)
        return
    # Sanitize message to escape quotes
    message = message.replace('"', '\\"')
    print(CYAN + "[*] Sending SMS..." + RESET)
    out, err = run_cmd(f'adb -s {device} shell am start -a android.intent.action.SENDTO -d sms:{phone_number} --es sms_body "{message}"', capture=True)
    if err:
        print(RED + "[-] Failed to send SMS:" + RESET)
        print(err)
    else:
        print(GREEN + "[+] SMS sent successfully." + RESET)
def option_dump_contacts():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Dumping contacts..." + RESET)
    # Updated URI for better compatibility on newer Android
    out, err = run_cmd(f"adb -s {device} shell content query --uri content://com.android.contacts/data/phones/", capture=True)
    if not out or "No result found" in out or err:
        print(RED + "[-] No contacts found or access denied (common on Android 10+)." + RESET)
        print(YELLOW + "Tip: Contacts might be synced with Google account, check there." + RESET)
        return
    # Parse: Row format -> display_name=NAME, data1=NUMBER
    cleaned_contacts = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("Row:"):
            continue
        name_match = re.search(r'display_name=([^,]+)', line)
        number_match = re.search(r'data1=([^,]+)', line)
        if name_match and number_match:
            name = name_match.group(1).strip()
            number = number_match.group(1).strip()
            if name and number:
                cleaned_contacts.append(f"{name}: {number}")
    print(CYAN + "[+] Contacts (Name: Number):" + RESET)
    if cleaned_contacts:
        for contact in cleaned_contacts:
            print(contact)
        print(f"\nTotal: {len(cleaned_contacts)} contacts")
    else:
        print(YELLOW + "No contacts parsed (device may have restricted access)." + RESET)
    save = input("\nDo you want to save clean contacts to contacts.txt? (y/n): ").strip().lower()
    if save == "y" and cleaned_contacts:
        with open("contacts.txt", "w") as f:
            f.write("\n".join(cleaned_contacts) + "\n")
        print(GREEN + "[+] Saved clean contacts to ./contacts.txt" + RESET)
def option_reboot_device():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Sending reboot command..." + RESET)
    out, err = run_cmd(f"adb -s {device} shell reboot", capture=True)
    if err:
        print(RED + "[-] Error rebooting device:" + RESET)
        print(err)
    else:
        print(GREEN + "[+] Device is rebooting." + RESET)
def option_start_app():
    device = get_selected_device()
    if device is None:
        return
    package = input("Enter package name to start (e.g., com.example.app): ").strip()
    if not package:
        print(RED + "[-] Package name is required." + RESET)
        return
    print(CYAN + "[*] Starting application..." + RESET)
    out, err = run_cmd(f"adb -s {device} shell monkey -p {package} 1", capture=True)
    if err:
        print(RED + "[-] Failed to start application:" + RESET)
        print(err)
    else:
        print(GREEN + "[+] Application started." + RESET)
def option_get_device_logs():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Fetching device logs..." + RESET)
    filename = "device_log.txt"
    out, err = run_cmd(f"adb -s {device} logcat -d > {filename}", capture=True)
    if os.path.isfile(filename):
        print(GREEN + f"[+] Logs saved to ./{filename}" + RESET)
        view = input("Do you want to open the logs now? (y/n): ").strip().lower()
        if view == "y":
            opener = shutil.which("xdg-open") or "xdg-open"
            run_cmd(f"{opener} {filename}")
    else:
        print(RED + "[-] Failed to fetch logs:" + RESET)
        print(err)
def option_toggle_wifi():
    device = get_selected_device()
    if device is None:
        return
    state = input("Enter Wi-Fi state (enable/disable): ").strip().lower()
    if state not in ["enable", "disable"]:
        print(RED + "[-] Invalid state. Use 'enable' or 'disable'." + RESET)
        return
    print(CYAN + f"[*] {'Enabling' if state == 'enable' else 'Disabling'} Wi-Fi..." + RESET)
    cmd = f"adb -s {device} shell svc wifi {state}"
    out, err = run_cmd(cmd, capture=True)
    if err:
        print(RED + f"[-] Failed to {state} Wi-Fi:" + RESET)
        print(err)
    else:
        print(GREEN + f"[+] Wi-Fi {state}d successfully." + RESET)
def option_check_storage():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Checking storage info..." + RESET)
    out, err = run_cmd(f"adb -s {device} shell df -h", capture=True) # Human readable
    if out:
        print(out)
        save = input("\nDo you want to save storage info to storage_info.txt? (y/n): ").strip().lower()
        if save == "y":
            with open("storage_info.txt", "w") as f:
                f.write(out + "\n")
            print(GREEN + "[+] Saved to ./storage_info.txt" + RESET)
    else:
        print(RED + "[-] Failed to fetch storage info:" + RESET)
        print(err)
def option_take_photo():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Opening Camera app..." + RESET)
    run_cmd(f"adb -s {device} shell am start -a android.media.action.IMAGE_CAPTURE")
    time.sleep(3)
    print(CYAN + "[*] Capturing photo automatically..." + RESET)
    run_cmd(f"adb -s {device} shell input keyevent 27")
    time.sleep(2)
    print(CYAN + "[*] Finding latest photo..." + RESET)
    out, err = run_cmd(f"adb -s {device} shell ls -t /sdcard/DCIM/Camera/ | head -1", capture=True)
    if not out.strip():
        print(RED + "[-] No photo found in DCIM/Camera." + RESET)
        return
    latest = out.strip()
    remote = f"/sdcard/DCIM/Camera/{latest}"
    local = latest
    print(CYAN + f"[*] Pulling {latest}..." + RESET)
    run_cmd(f"adb -s {device} pull {remote} ./")
    if os.path.isfile(local):
        print(GREEN + f"[+] Photo saved as {local}" + RESET)
        view = input("Do you want to open the photo now? (y/n): ").strip().lower()
        if view == "y":
            opener = shutil.which("xdg-open") or "xdg-open"
            run_cmd(f"{opener} {local}")
    else:
        print(RED + "[-] Failed to pull photo." + RESET)
def option_troubleshoot():
    print(CYAN + "[*] Troubleshooting ADB connection..." + RESET)
    run_cmd("adb kill-server")
    run_cmd("adb start-server")
    print(GREEN + "[+] ADB server restarted." + RESET)
    print(CYAN + "[*] Current devices:" + RESET)
    run_cmd("adb devices")

# ----------------- New Cyber Defence Features -----------------
def cyber_root_detection():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Checking for root access..." + RESET)
    methods = [
        f"adb -s {device} shell which su",
        f"adb -s {device} shell getprop ro.build.tags | grep test-keys",
        f"adb -s {device} shell ls /system/bin/su",
        f"adb -s {device} shell ls /system/xbin/su"
    ]
    rooted = False
    for cmd in methods:
        out, _ = run_cmd(cmd, capture=True)
        if out and "not found" not in out.lower() and out != "":
            rooted = True
            break
    if rooted:
        print(RED + "[!] Device appears to be ROOTED (Security Risk for banking apps)" + RESET)
    else:
        print(GREEN + "[+] No root detected." + RESET)

def cyber_apk_permissions():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Dumping dangerous permissions per app (granted only)..." + RESET)
    pkg_out, _ = run_cmd(f"adb -s {device} shell pm list packages", capture=True)
    if not pkg_out:
        print(RED + "[-] Failed to fetch package list." + RESET)
        return
    packages = [line.split(":")[1].strip() for line in pkg_out.splitlines() if line.startswith("package:")]
    
    dangerous_perms = [
        "android.permission.CAMERA", "android.permission.ACCESS_FINE_LOCATION", 
        "android.permission.ACCESS_COARSE_LOCATION", "android.permission.RECORD_AUDIO", 
        "android.permission.READ_SMS", "android.permission.CALL_PHONE", 
        "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.READ_CONTACTS", "android.permission.READ_PHONE_STATE"
    ]
    
    print(YELLOW + "App Package → Granted Dangerous Permissions:" + RESET)
    found_any = False
    for pkg in packages:
        dump_out, _ = run_cmd(f"adb -s {device} shell dumpsys package {pkg}", capture=True)
        if not dump_out:
            continue
        granted = []
        lines = dump_out.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("install permissions:") or line.startswith("runtime permissions:"):
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("install permissions:", "runtime permissions:", "User ")):
                    perm_line = lines[i].strip()
                    if ": granted=true" in perm_line:
                        perm = perm_line.split(":")[0].strip()
                        if perm in dangerous_perms:
                            granted.append(perm)
                    i += 1
                continue
            i += 1
        if granted:
            found_any = True
            print(f"  {pkg}: {', '.join(granted)}")
    
    if not found_any:
        print(GREEN + "[+] No dangerous permissions currently granted to any app." + RESET)
        print(YELLOW + "[*] Note: Runtime permissions need user approval to be granted." + RESET)

def cyber_security_audit():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Running Device Security Audit..." + RESET)
    info = {}
    cmds = {
        "Android Version": f"adb -s {device} shell getprop ro.build.version.release",
        "Security Patch Level": f"adb -s {device} shell getprop ro.build.version.security_patch",
        "Encryption Status": f"adb -s {device} shell getprop ro.crypto.state",
        "Build Tags": f"adb -s {device} shell getprop ro.build.tags"
    }
    for name, cmd in cmds.items():
        out, _ = run_cmd(cmd, capture=True)
        info[name] = out or "Unknown"
        print(f"{name}: {info[name]}")
    
    # Debuggable apps count
    pkg_out, _ = run_cmd(f"adb -s {device} shell pm list packages", capture=True)
    packages = [line.split(":")[1].strip() for line in (pkg_out or "").splitlines() if line.startswith("package:")]
    debuggable_count = 0
    for pkg in packages:
        dump_out, _ = run_cmd(f"adb -s {device} shell dumpsys package {pkg} | grep debuggable", capture=True)
        if "debuggable=true" in (dump_out or "").lower():
            debuggable_count += 1
    print(f"Debuggable Apps Count: {debuggable_count} (Should be 0 in production)")

def cyber_debuggable_apps():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Scanning for debuggable apps..." + RESET)
    pkg_out, _ = run_cmd(f"adb -s {device} shell pm list packages", capture=True)
    packages = [line.split(":")[1].strip() for line in (pkg_out or "").splitlines() if line.startswith("package:")]
    found = []
    for pkg in packages:
        dump_out, _ = run_cmd(f"adb -s {device} shell dumpsys package {pkg} | grep debuggable", capture=True)
        if "debuggable=true" in (dump_out or "").lower():
            found.append(pkg)
    if found:
        print(RED + "[!] Debuggable apps found (Security Risk):" + RESET)
        for pkg in found:
            print(f"  - {pkg}")
    else:
        print(GREEN + "[+] No debuggable apps detected." + RESET)

def cyber_device_shell():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Opening interactive ADB shell (type 'exit' to quit)..." + RESET)
    print(YELLOW + "[*] Use carefully - only on your own device!" + RESET)
    run_cmd(f"adb -s {device} shell")

def cyber_network_check():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Checking connected Wi-Fi security..." + RESET)
    out, _ = run_cmd(f"adb -s {device} shell dumpsys wifi", capture=True)
    if out:
        if "WPA" in out or "WPA2" in out or "WPA3" in out:
            print(GREEN + "[+] Connected to secured Wi-Fi network." + RESET)
        elif "open" in out.lower():
            print(RED + "[!] Connected to OPEN (unsecured) Wi-Fi!" + RESET)
        else:
            print(YELLOW + "[*] Wi-Fi security status unclear." + RESET)
    if check_dependency("nmap"):
        ip_range = input("Enter local network range for scan (e.g. 192.168.1.0/24) or press Enter to skip: ").strip()
        if ip_range:
            print(CYAN + "[*] Running nmap ping scan on host PC..." + RESET)
            run_cmd(f"nmap -sn {ip_range}")
    else:
        print(YELLOW + "[*] nmap not found on host for advanced network scan." + RESET)

def cyber_recent_logs():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "\n[+] Fetching recent security-related logs..." + RESET)
    print(YELLOW + "[*] Filtering for permission, security, and denial events." + RESET)
    run_cmd(f"adb -s {device} logcat -d *:W | grep -i 'permission\\|security\\|denied\\|violation\\|warning'")

def option_scan_device_vulnerabilities():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Scanning for device vulnerabilities..." + RESET)
    patch_level, _ = run_cmd(f"adb -s {device} shell getprop ro.build.version.security_patch", capture=True)
    print(f"Security Patch Level: {patch_level}")
    build_date, _ = run_cmd(f"adb -s {device} shell getprop ro.build.date", capture=True)
    print(f"Build Date: {build_date}")
    try:
        patch_date = datetime.datetime.strptime(patch_level, "%Y-%m-%d")
        if patch_date < datetime.datetime(2025, 1, 1):
            print(RED + "[!] Device may have known vulnerabilities (patch older than 2025-01-01)" + RESET)
        else:
            print(GREEN + "[+] Patch level is recent." + RESET)
    except:
        print(YELLOW + "[?] Unable to parse patch level." + RESET)
    print(YELLOW + "For specific CVEs, search online for your Android version and patch level." + RESET)

def _parse_content_rows(text):
    rows=[]
    for line in (text or '').splitlines():
        if ': ' in line and line.lstrip().startswith('Row:'):
            line=line.split(': ',1)[1]
        d={}
        # content query separates fields by comma+space; body may contain commas, so keep unknown fragments with previous value
        last=None
        for part in line.split(', '):
            if '=' in part:
                k,v=part.split('=',1); d[k.strip()]=v; last=k.strip()
            elif last: d[last] += ', '+part
        if d: rows.append(d)
    return rows

def _write_html_table(path,title,rows):
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(path,'w',encoding='utf-8') as f:
        f.write('<!doctype html><meta charset="utf-8"><title>'+html.escape(title)+'</title>')
        f.write('<style>body{font-family:sans-serif;margin:2rem}table{border-collapse:collapse;width:100%}th,td{border:1px solid #aaa;padding:.4rem;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#eee}</style>')
        f.write('<h1>'+html.escape(title)+'</h1><table><thead><tr>')
        for k in keys: f.write('<th>'+html.escape(k)+'</th>')
        f.write('</tr></thead><tbody>')
        for r in rows:
            f.write('<tr>')
            for k in keys: f.write('<td>'+html.escape(str(r.get(k,'')))+'</td>')
            f.write('</tr>')
        f.write('</tbody></table>')

def _write_xlsx(path,sheets):
    try:
        from openpyxl import Workbook
    except ImportError:
        return False
    wb=Workbook(); wb.remove(wb.active)
    for name,rows in sheets:
        ws=wb.create_sheet(name[:31]); keys=[]
        for r in rows:
            for k in r:
                if k not in keys: keys.append(k)
        ws.append(keys)
        for r in rows: ws.append([r.get(k,'') for k in keys])
        ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
        for col in ws.columns:
            letter=col[0].column_letter
            ws.column_dimensions[letter].width=min(60,max(12,max((len(str(c.value or '')) for c in col),default=12)+2))
    wb.save(path); return True

def option_dump_sms_call_logs():
    device=get_selected_device()
    if device is None: return
    print(CYAN+'[*] Reading SMS and call logs from the selected device...'+RESET)
    sms_out,sms_err=run_cmd(f"adb -s {device} shell content query --uri content://sms/ --projection address:body:date:type",capture=True)
    call_out,call_err=run_cmd(f"adb -s {device} shell content query --uri content://call_log/calls --projection number:duration:date:type",capture=True)
    sms=_parse_content_rows(sms_out); calls=_parse_content_rows(call_out)
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    sms_html=f'sms_{stamp}.html'; call_html=f'calls_{stamp}.html'; xlsx=f'messages_calls_{stamp}.xlsx'
    _write_html_table(sms_html,'SMS export',sms); _write_html_table(call_html,'Call log export',calls)
    print(GREEN+f'[+] HTML: {sms_html} ({len(sms)} rows), {call_html} ({len(calls)} rows)'+RESET)
    if _write_xlsx(xlsx,[('SMS',sms),('Calls',calls)]): print(GREEN+f'[+] XLSX: {xlsx}'+RESET)
    else: print(YELLOW+'[*] XLSX skipped: install openpyxl with: pip install openpyxl'+RESET)
    if sms_err: print(YELLOW+'SMS note: '+sms_err+RESET)
    if call_err: print(YELLOW+'Calls note: '+call_err+RESET)

def option_network_connections():
    device = get_selected_device()
    if device is None:
        return
    print(CYAN + "[*] Monitoring network connections..." + RESET)
    out, _ = run_cmd(f"adb -s {device} shell netstat", capture=True)
    if not out:
        out, _ = run_cmd(f"adb -s {device} shell cat /proc/net/tcp", capture=True)
    print(out)
# ----------------- Android Manager / Port tools -----------------
def manager_permissions():
    device=get_selected_device()
    if device is None:return
    sel=_choose_package(device,'Choose application for permissions')
    if not sel:return
    pkg,label,_=sel
    dump,_=run_cmd(f"adb -s {device} shell dumpsys package {pkg}",capture=True)
    print(CYAN+f"\n=== Permissions: {label} ({pkg}) ==="+RESET)
    interesting=[]
    for line in (dump or '').splitlines():
        t=line.strip()
        if 'android.permission.' in t or ': granted=' in t: interesting.append(t)
    print('\n'.join(interesting) if interesting else 'No permission details available.')
    ops,_=run_cmd(f"adb -s {device} shell cmd appops get {pkg}",capture=True)
    print(CYAN+'\n=== AppOps ==='+RESET); print(ops or 'No AppOps returned.')

def _hex_port(p): return f'{p:04X}'
def _socket_listeners(device):
    # /proc view includes UID even where ss -p is restricted
    out,_=run_cmd(f"adb -s {device} shell 'cat /proc/self/net/tcp /proc/self/net/tcp6 2>/dev/null'",capture=True)
    found=[]
    for line in (out or '').splitlines():
        parts=line.split()
        if len(parts)<10 or parts[0]=='sl': continue
        try:
            local=parts[1]; state=parts[3]; uid=int(parts[7]); inode=parts[9]
            if state!='0A': continue
            port=int(local.rsplit(':',1)[1],16)
            if port and (port,uid,inode) not in found: found.append((port,uid,inode))
        except: pass
    return sorted(found)

def _uid_packages(device,uid):
    out,_=run_cmd(f"adb -s {device} shell pm list packages -U",capture=True)
    result=[]
    for line in (out or '').splitlines():
        if f'uid:{uid}' in line:
            pkg=line.split('package:',1)[1].split()[0] if 'package:' in line else line
            result.append(pkg)
    return result

def manager_ports():
    device=get_selected_device()
    if device is None:return
    listeners=_socket_listeners(device)
    if not listeners:
        print(YELLOW+'No listeners available through /proc; showing ss instead.'+RESET)
        out,_=run_cmd(f"adb -s {device} shell ss -lnt",capture=True); print(out); return
    print(CYAN+'\n=== TCP listening ports ==='+RESET)
    print(f"{'N°':>3} {'Port':>6} {'UID':>7} {'Application/package':<50} Utility")
    rows=[]
    for i,(port,uid,inode) in enumerate(listeners,1):
        pkgs=_uid_packages(device,uid); pkg=', '.join(pkgs) if pkgs else 'system/unknown'
        util=_package_utility(pkgs[0]) if pkgs else 'System or unidentified UID'
        rows.append((port,uid,inode,pkgs))
        print(f"{i:>3} {port:>6} {uid:>7} {pkg[:50]:<50} {util}")
    raw=input('\nSelect port number for actions (0 = back): ').strip()
    if raw=='0':return
    try: row=rows[int(raw)-1]
    except: print(RED+'Invalid selection.'+RESET);return
    port,uid,inode,pkgs=row
    print(f"\nPort {port} | UID {uid} | inode {inode} | {' / '.join(pkgs) if pkgs else 'unknown'}")
    print('[1] Show current connections\n[2] Show owning UID processes\n[3] Force-stop owning app temporarily\n[4] Test port from this host (requires device IP)\n[0] Back')
    act=input('Action: ').strip()
    if act=='1':
        out,_=run_cmd(f"adb -s {device} shell ss -ant",capture=True)
        print('\n'.join(x for x in (out or '').splitlines() if f':{port}' in x) or 'No current connections shown.')
    elif act=='2':
        out,_=run_cmd(f"adb -s {device} shell ps -A -o UID,PID,NAME,ARGS",capture=True)
        aliases=[str(uid),f'u0_a{uid-10000}' if uid>=10000 else '']
        print('\n'.join(x for x in (out or '').splitlines() if any(a and a in x.split()[:1] for a in aliases)) or 'No matching process shown.')
    elif act=='3' and pkgs:
        pkg=pkgs[0]
        if input(f'Force-stop {pkg}? (y/N): ').lower()=='y':
            print(run_cmd(f"adb -s {device} shell am force-stop {pkg}",capture=True)[0] or 'Done.')
    elif act=='4':
        ip=input('Device IP: ').strip()
        if ip:
            if check_dependency('nc'): run_cmd(f"nc -vz -w 3 {ip} {port}")
            else: print(YELLOW+'netcat/nc not installed; Termux: pkg install netcat-openbsd'+RESET)


def _launcher_activity(device, pkg):
    """Resolve the main launcher activity for a package."""
    commands = [
        f"adb -s {device} shell cmd package resolve-activity --brief "
        f"-a android.intent.action.MAIN -c android.intent.category.LAUNCHER {pkg}",
        f"adb -s {device} shell cmd package query-activities --brief --components "
        f"-a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p {pkg}",
    ]
    for cmd in commands:
        out, _ = run_cmd(cmd, capture=True)
        for line in (out or "").splitlines():
            line = line.strip()
            if "/" in line and line.startswith(pkg + "/"):
                return line
    return None

def manager_launcher():
    device = get_selected_device()
    if device is None:
        return
    selected = _choose_package(device, "Launcher / écran d'accueil")
    if not selected:
        return
    pkg, label, util = selected
    component = _launcher_activity(device, pkg)

    print(CYAN + f"\n=== {label} ===" + RESET)
    print(f"Package   : {pkg}")
    print(f"Utility   : {util}")
    print(f"Launcher  : {component or 'not resolved / non résolu'}")
    print("\n[1] Hide icon from launcher / Masquer l'icône")
    print("[2] Restore launcher icon / Restaurer l'icône")
    print("[3] Show launcher component / Afficher le composant")
    print("[0] Back / Retour")
    action = input("> ").strip()

    if action == "3":
        return
    if not component:
        print(YELLOW + "No MAIN/LAUNCHER activity could be resolved for this package." + RESET)
        return

    if action == "1":
        print(YELLOW + "This disables only the launcher activity when Android allows it; the app itself is not uninstalled." + RESET)
        if input("Confirm / Confirmer ? (y/N): ").strip().lower() != "y":
            return
        out, err = run_cmd(
            f"adb -s {device} shell pm disable-user --user 0 {component}",
            capture=True
        )
        print(out or err or "Done.")
    elif action == "2":
        if input("Confirm / Confirmer ? (y/N): ").strip().lower() != "y":
            return
        out, err = run_cmd(
            f"adb -s {device} shell pm enable --user 0 {component}",
            capture=True
        )
        print(out or err or "Done.")

def manager_package_state(enable):
    device=get_selected_device()
    if device is None:return
    sel=_choose_package(device,'Choose application')
    if not sel:return
    pkg,label,_=sel
    verb='enable' if enable else 'disable-user --user 0'
    if input(f"{'Enable' if enable else 'Disable'} {label}? (y/N): ").lower()!='y':return
    out,err=run_cmd(f"adb -s {device} shell pm {verb} {pkg}",capture=True); print(out or err or 'Done.')

def manager_profiles():
    device=get_selected_device()
    if device is None:return
    print('\n[1] Orange/carrier payment: enable Xiaomi Payment\n[2] Privacy: disable Xiaomi Payment\n[3] ADB TCP 5555 ON\n[4] ADB TCP OFF (USB connection recommended)\n[0] Back')
    c=input('Profile/action: ').strip()
    if c=='1': cmd=f'adb -s {device} shell pm enable --user 0 com.xiaomi.payment'
    elif c=='2': cmd=f'adb -s {device} shell pm disable-user --user 0 com.xiaomi.payment'
    elif c=='3': cmd=f'adb -s {device} tcpip 5555'
    elif c=='4': cmd=f'adb -s {device} usb'
    else:return
    out,err=run_cmd(cmd,capture=True); print(out or err or 'Done.')

def android_manager():
    while True:
        print_banner()
        print(GREEN + f"═════ {t('android_manager').upper()} ═════" + RESET)
        print(f"[1] {t('apps')}")
        print(f"[2] {t('permissions')}")
        print(f"[3] {t('ports')}")
        print(f"[4] {t('disable_app')}")
        print(f"[5] {t('enable_app')}")
        print(f"[6] {t('exports')} → HTML/XLSX")
        print(f"[7] {t('profiles')} (Orange / Privacy / ADB)")
        print(f"[8] {t('shell')}")
        print(f"[9] {t('launcher')}")
        print(f"[0] {t('back')}")
        c = input(f"\n{t('select')}: ").strip()
        actions = {
            '1': option_delete_apk,
            '2': manager_permissions,
            '3': manager_ports,
            '4': lambda: manager_package_state(False),
            '5': lambda: manager_package_state(True),
            '6': option_dump_sms_call_logs,
            '7': manager_profiles,
            '8': cyber_device_shell,
            '9': manager_launcher,
        }
        if c == '0':
            return
        if c in actions:
            actions[c]()
            input('\nPress Enter / Entrée pour continuer...')
        else:
            print(RED + t('invalid') + RESET)
            time.sleep(1)

# ----------------- Cyber Defence Sub-Menu -----------------
def show_cyber_menu():
    print_banner()  # Show banner in cyber menu as well
    print(GREEN + "═════ SECURITY / DIAGNOSTIC FEATURES ═════" + RESET)
    print()
    print(CYAN + "[1] Root Detection\n")
    print(CYAN + "[2] APK Dangerous Permissions Dump\n")
    print(CYAN + "[3] Device Security Audit\n")
    print(CYAN + "[4] Check Debuggable Apps\n")
    print(CYAN + "[5] Access Device Shell (Interactive)\n")
    print(CYAN + "[6] Network Security Check\n")
    print(CYAN + "[7] Dump SMS/Call Logs\n")
    print(CYAN + "[8] Recent Security Logs\n")
    print(CYAN + "[9] Scan for Device Vulnerabilities\n")
    print(CYAN + "[10] Network Connections Monitor\n")
    print(CYAN + "[11] Android Manager (apps / permissions / ports / profiles)\n")
    print()
    print(YELLOW + "[0] Back to Main Menu")
    print(GREEN + "══════════════════════════════════" + RESET)
    print()

def cyber_defence_mode():
    print_banner()
    print(GREEN + "[+] Security / Diagnostic Mode Activated!" + RESET)
    while True:
        show_cyber_menu()
        choice = input(GREEN + "Select cyber option (0-11): " + RESET).strip()
        cyber_options = {
            "1": cyber_root_detection,
            "2": cyber_apk_permissions,
            "3": cyber_security_audit,
            "4": cyber_debuggable_apps,
            "5": cyber_device_shell,
            "6": cyber_network_check,
            "7": option_dump_sms_call_logs,
            "8": cyber_recent_logs,
            "9": option_scan_device_vulnerabilities,
            "10": option_network_connections,
            "11": android_manager,
            "0": lambda: "back"
        }
        if choice in cyber_options:
            if choice == "0":
                return
            result = cyber_options[choice]()
            if result == "back":
                return
            input("\nPress Enter to continue...")
        else:
            print(RED + "Invalid option. Please try again." + RESET)
            time.sleep(1)

# ----------------- Menu / Main Loop -----------------
def show_menu():
    print()
    print(GREEN + f"═════ {t('main_title')} ═════" + RESET)
    if LANG == "fr":
        items = [
            ("1", "Vérifier l'appareil"), ("2", "Connecter un appareil"), ("3", "Déconnecter"),
            ("4", "Enregistrement écran"), ("5", "Miroir écran"), ("6", "Liste APK"),
            ("7", "Capture écran"), ("8", "Éteindre"), ("9", "Installer APK"),
            ("10", "Applications / supprimer APK"), ("11", "Récupérer un fichier"), ("12", "Envoyer un fichier"),
            ("13", "Préparer un SMS"), ("14", "Exporter les contacts"), ("15", "Redémarrer"),
            ("16", "Démarrer une application"), ("17", "Logs appareil"), ("18", "Wi-Fi ON/OFF"),
            ("19", "Stockage"), ("20", "Photo"), ("21", "Dépannage connexion"),
            ("22", "Sécurité avancée & gestion Android"), ("23", "Historique connexions"),
            ("24", "Langue"),
        ]
    else:
        items = [
            ("1", "Check Device"), ("2", "Connect a Device"), ("3", "Disconnect Device"),
            ("4", "Screen Recording"), ("5", "Screen Mirror"), ("6", "Show APK List"),
            ("7", "Take Screenshot"), ("8", "Power Off"), ("9", "Install APK"),
            ("10", "Applications / Delete APK"), ("11", "Pull File"), ("12", "Push File"),
            ("13", "Prepare SMS"), ("14", "Dump Contacts"), ("15", "Reboot Device"),
            ("16", "Start App"), ("17", "Get Device Logs"), ("18", "Toggle Wi-Fi"),
            ("19", "Check Storage"), ("20", "Take Photo"), ("21", "Troubleshoot Connection"),
            ("22", "Advanced Security & Android Manager"), ("23", "Connection History"),
            ("24", "Language"),
        ]
    for i in range(0, len(items), 3):
        row = items[i:i+3]
        print(YELLOW + "    ".join(f"[{n}] {label}" for n, label in row) + RESET)
    print(YELLOW + f"[q] {t('quit')}" + RESET)
    print()

def dependencies_check():
    print(CYAN + "[*] Checking dependencies..." + RESET)
    deps = [("adb", adb_available()), ("scrcpy", scrcpy_available())]
    for name, available in deps:
        if available:
            print(GREEN + f"[OK] {name} installed" + RESET)
        else:
            hint = "pkg install android-tools" if name == "adb" and os.environ.get("PREFIX", "").startswith("/data/data/com.termux") else ("pkg install scrcpy" if name == "scrcpy" and os.environ.get("PREFIX", "").startswith("/data/data/com.termux") else f"install {name} with your package manager")
            print(RED + f"[MISSING] {name} ({hint})" + RESET)


# ===========================================================================
# Android ADB Admin 2.0 enhancements
# ===========================================================================
import json as _json
import urllib.request as _urlreq
import urllib.error as _urlerr
import tempfile as _tempfile
import tarfile as _tarfile
import sqlite3 as _sqlite3
import unicodedata as _unicodedata
from pathlib import Path as _Path

AA_VERSION = "2.3"
AA_CONFIG = _Path(CONFIG_DIR) / "admin-config.json"
AA_CACHE = _Path(CONFIG_DIR) / "app-catalog-cache.json"
AA_DEFAULTS = {"wifi_ip":"", "wifi_port":5555, "recordings_path":"/sdcard/Recordings", "hidden_launcher_components":{}}

def _aa_load():
    cfg=dict(AA_DEFAULTS)
    try:
        if AA_CONFIG.exists(): cfg.update(_json.loads(AA_CONFIG.read_text(encoding='utf-8')))
    except Exception: pass
    return cfg

def _aa_save(cfg):
    _Path(CONFIG_DIR).mkdir(parents=True,exist_ok=True)
    AA_CONFIG.write_text(_json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')

AA_CFG=_aa_load(); _aa_save(AA_CFG)

def _aa_cmd(args, timeout=90):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,check=False)
        return p.returncode,(p.stdout or '').strip(),(p.stderr or '').strip()
    except Exception as e:return 1,'',str(e)

def _aa_adb(dev,*args,timeout=90): return _aa_cmd(['adb','-s',dev,*args],timeout=timeout)
def _aa_sh(dev,cmd,timeout=90): return _aa_cmd(['adb','-s',dev,'shell',cmd],timeout=timeout)
def _aa_q(path): return "'"+str(path).replace("'","'\\''")+"'"
def _aa_ts(): return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
def _aa_safe(s):
    s=_unicodedata.normalize('NFKD',str(s or ''))
    s=''.join(c for c in s if not _unicodedata.combining(c))
    return (re.sub(r'[^A-Za-z0-9._-]+','-',s).strip('-._') or 'unknown')[:90]

def _aa_adb_records():
    """Return ``[(serial, state), ...]`` parsed directly from ``adb devices``.

    This is deliberately separate from ``adb_devices_list()`` because the
    historical helper returns only serial strings.  Wi-Fi/USB status code must
    never assume that helper returns two-element tuples.
    """
    rc, out, err = _aa_cmd(['adb', 'devices'])
    if rc != 0:
        return []
    records = []
    for raw in (out or '').splitlines():
        line = raw.strip()
        if not line or line.startswith('List of devices attached') or line.startswith('* daemon'):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        records.append((parts[0], parts[1]))
    return records


def _aa_wifi_devices():
    """Return authorized ADB-over-network devices as ``(serial, state)``."""
    return [
        (serial, state)
        for serial, state in _aa_adb_records()
        if ':' in serial and not serial.startswith('emulator-') and state == 'device'
    ]


def _aa_usb_devices():
    """Return authorized physical USB ADB devices as ``(serial, state)``."""
    return [
        (serial, state)
        for serial, state in _aa_adb_records()
        if ':' not in serial and not serial.startswith('emulator-') and state == 'device'
    ]

def print_banner():
    clear_screen()
    wd=_aa_wifi_devices()
    print(CYAN+'='*52+RESET)
    print(CYAN+f'ANDROID ADB ADMIN {AA_VERSION}'.center(52)+RESET)
    if wd:
        ip=wd[0][0].split(':',1)[0]
        print(GREEN+'● ADB ACTIF'+RESET+f' — {ip}')
    else: print(RED+'● ADB OFF'+RESET)
    print(CYAN+'='*52+RESET); print()

# ---------- App identification / risk ----------
AA_KNOWN={
'com.google.android.apps.docs':('Google Drive','Stockage et synchronisation Google Drive','Google'),
'com.google.android.gm':('Gmail','Messagerie Google','Google'),
'com.google.android.apps.maps':('Google Maps','Cartographie et navigation','Google'),
'com.google.android.apps.translate':('Google Traduction','Traduction','Google'),
'com.google.android.apps.messaging':('Google Messages','SMS / RCS','Google'),
'com.google.android.contacts':('Google Contacts','Gestion des contacts','Google'),
'com.google.android.dialer':('Téléphone Google','Téléphonie et appels','Google'),
'com.google.android.apps.walletnfcrel':('Google Wallet','Paiement NFC / portefeuille','Google'),
'com.google.android.gms':('Services Google Play','Services et API centrales Google','Google système'),
'com.android.vending':('Google Play Store','Installation et mises à jour','Google'),
'com.google.android.googlequicksearchbox':('Google','Recherche Google / widgets / Assistant','Google'),
'com.android.chrome':('Chrome','Navigateur web','Google'),
'com.openai.chatgpt':('ChatGPT','Application ChatGPT','Utilisateur'),
'org.telegram.messenger':('Telegram','Messagerie','Utilisateur'),
'org.thoughtcrime.securesms':('Signal','Messagerie chiffrée','Utilisateur'),
'com.whatsapp':('WhatsApp','Messagerie','Utilisateur'),
'com.instagram.android':('Instagram','Réseau social','Utilisateur'),
'com.facebook.katana':('Facebook','Réseau social','Utilisateur'),
'com.facebook.orca':('Messenger','Messagerie','Utilisateur'),
'com.snapchat.android':('Snapchat','Réseau social / messagerie','Utilisateur'),
'com.termux':('Termux','Terminal Android','Utilisateur'),
'com.termux.api':('Termux:API','API Android pour Termux','Utilisateur'),
'com.termux.x11':('Termux:X11','Affichage X11 pour Termux','Utilisateur'),
'org.fdroid.fdroid':('F-Droid','Catalogue libre','Utilisateur'),
'org.torproject.torbrowser':('Tor Browser','Navigateur Tor','Utilisateur'),
'net.mullvad.mullvadvpn':('Mullvad VPN','VPN','Utilisateur'),
'com.tailscale.ipn':('Tailscale','VPN mesh / réseau privé','Utilisateur'),
'com.x8bit.bitwarden':('Bitwarden','Gestionnaire de mots de passe','Utilisateur'),
'com.beemdevelopment.aegis':('Aegis','TOTP / authentification','Utilisateur'),
'com.revolut.revolut':('Revolut','Banque / paiements','Utilisateur'),
'com.orange.orangeetmoi':('Orange et moi','Gestion ligne Orange','Utilisateur'),
'com.emanuelef.remote_capture':('PCAPdroid','Capture réseau','Utilisateur'),
'com.github.axet.callrecorder':('Call Recorder','Enregistrement d’appels','Utilisateur'),
'com.miui.home':('Launcher HyperOS','Écran d’accueil Xiaomi / HyperOS','Xiaomi système'),
'com.miui.gallery':('Galerie Xiaomi','Photos et vidéos locales','Xiaomi'),
'com.miui.securitycenter':('Sécurité HyperOS','Sécurité, batterie et permissions','Xiaomi système'),
'com.lbe.security.miui':('Gestion permissions Xiaomi','Permissions HyperOS','Xiaomi système'),
'com.xiaomi.payment':('Xiaomi Payment','Paiement Xiaomi / opérateur','Xiaomi'),
'com.xiaomi.finddevice':('Xiaomi Find Device','Localisation appareil','Xiaomi système'),
'com.xiaomi.mi_connect_service':('Mi Connect','Connexion entre appareils Xiaomi','Xiaomi'),
'com.xiaomi.hypercomm':('HyperConnect','Continuité Xiaomi','Xiaomi'),
'com.android.systemui':('Interface système Android','Notifications, barre d’état et navigation','Android système'),
'com.android.settings':('Paramètres Android','Configuration principale','Android système'),
'com.android.phone':('Téléphonie Android','SIM, appels et réseau mobile','Android système'),
'com.android.providers.telephony':('Base téléphonie','SMS/MMS et données téléphonie','Android système'),
'com.android.providers.contacts':('Base contacts','Stockage système des contacts','Android système'),
'com.android.providers.settings':('Base paramètres','Paramètres Android','Android système'),
'com.android.providers.downloads':('Téléchargements Android','Gestion des téléchargements','Android système'),
'com.android.bluetooth':('Bluetooth Android','Pile Bluetooth','Android système'),
'com.android.nfc':('NFC Android','Pile NFC','Android système'),
'com.android.shell':('ADB Shell','Identité système ADB','Android système')}
AA_CRIT=set(['android','com.android.systemui','com.android.settings','com.android.phone','com.android.providers.telephony','com.android.providers.contacts','com.android.providers.settings','com.google.android.permissioncontroller','com.google.android.gms','com.miui.securitycenter','com.lbe.security.miui','com.miui.home','com.android.bluetooth','com.android.nfc'])
AA_CRIT_PREFIX=('vendor.','com.qualcomm.','com.qti.','org.codeaurora.','com.android.server.','com.android.internal.','android.overlay','com.android.overlay.','com.google.android.overlay.')

def _aa_cache():
    try:return _json.loads(AA_CACHE.read_text(encoding='utf-8'))
    except Exception:return {}

def _aa_cache_save(c):
    try:AA_CACHE.write_text(_json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception:pass

def _aa_device_label(dev,pkg):
    _,o,_=_aa_sh(dev,f'dumpsys package {pkg}')
    for pat in (r'nonLocalizedLabel=([^,\n]+)',r"application-label(?:-[^:]+)?:\\s*['\"]?([^'\n\"]+)"):
        m=re.search(pat,o,re.I)
        if m and m.group(1).strip().lower() not in ('null','none'):return m.group(1).strip()
    return ''

def _aa_online_label(pkg):
    c=_aa_cache(); x=c.get(pkg,{})
    if x.get('name'):return x['name'],x.get('source','cache')
    try:
        req=_urlreq.Request(f'https://play.google.com/store/apps/details?id={pkg}&hl=fr',headers={'User-Agent':'Mozilla/5.0'})
        with _urlreq.urlopen(req,timeout=3) as r: body=r.read(160000).decode('utf-8','ignore')
        m=re.search(r'<title[^>]*>(.*?)</title>',body,re.I|re.S)
        if m:
            name=html.unescape(re.sub(r'\\s+',' ',m.group(1))).strip()
            name=re.sub(r'\\s*-\\s*(Applications sur Google Play|Apps on Google Play).*$','',name,flags=re.I)
            if name and 'Google Play' not in name:
                c[pkg]={'name':name[:100],'source':'Google Play','updated':_aa_ts()};_aa_cache_save(c);return name[:100],'Google Play'
    except Exception:pass
    try:
        with _urlreq.urlopen(f'https://f-droid.org/api/v1/packages/{pkg}',timeout=3) as r:d=_json.loads(r.read().decode('utf-8','ignore'))
        if d.get('packageName')==pkg:
            name=d.get('name') or pkg.rsplit('.',1)[-1].replace('_',' ').title()
            c[pkg]={'name':name,'source':'F-Droid','updated':_aa_ts()};_aa_cache_save(c);return name,'F-Droid'
    except Exception:pass
    return '',''

def _aa_info(dev,pkg,online=False):
    if pkg in AA_KNOWN:
        n,u,c=AA_KNOWN[pkg];return {'package':pkg,'name':n,'utility':u,'category':c,'source':'interne'}
    n=_aa_device_label(dev,pkg);src='Android' if n else ''
    if not n:
        cc=_aa_cache().get(pkg,{})
        n=cc.get('name','');src=cc.get('source','cache') if n else ''
    if online and not n:n,src=_aa_online_label(pkg)
    if not n:n=pkg.rsplit('.',1)[-1].replace('_',' ').replace('-',' ').title()
    if pkg.startswith(('com.miui.','com.xiaomi.')):cat='Xiaomi/HyperOS';u='Composant Xiaomi/HyperOS — fonction précise à vérifier'
    elif pkg.startswith(('com.google.','com.google.android.')):cat='Google';u='Composant Google — fonction précise à vérifier'
    elif pkg.startswith(('com.android.','android.','vendor.','com.qualcomm.','com.qti.')):cat='Système';u='Composant Android/constructeur — vérifier avant modification'
    else:cat='Utilisateur/tiers';u='Application tierce — fonction précise non identifiée'
    return {'package':pkg,'name':n,'utility':u,'category':cat,'source':src or 'déduit'}

def _aa_preinstalled(dev,pkg):
    _,o,_=_aa_sh(dev,f'pm path {pkg}')
    return any(p in o for p in ('/system/','/product/','/vendor/','/system_ext/','/apex/','/odm/'))

def _aa_risk(dev,pkg,action):
    critical=pkg in AA_CRIT or pkg.startswith(AA_CRIT_PREFIX)
    system=critical or _aa_preinstalled(dev,pkg) or pkg.startswith(('com.android.','android.','com.miui.','com.xiaomi.'))
    if action in ('inspect','permissions','network','ports'):return 'OK','Lecture/diagnostic : aucune suppression.'
    if critical and action in ('disable','uninstall','delete','force_stop','appops'):
        return 'DECONSEILLE','Composant critique : cela peut casser l’interface, la téléphonie, le réseau, les permissions, les notifications ou d’autres fonctions système.'
    if system and action in ('disable','uninstall','delete'):
        return 'A VERIFIER','Composant préinstallé : la suppression/désactivation peut retirer une fonction HyperOS/Android ou une dépendance.'
    if pkg not in AA_KNOWN and action in ('disable','uninstall','delete'):
        return 'A VERIFIER','Rôle non identifié avec assez de certitude. Vérifie avant modification.'
    return 'OK','Impact faible attendu pour cette action.'

def _aa_pick_pkg(dev,title,third=False,action='uninstall'):
    _,o,_=_aa_sh(dev,'pm list packages'+(' -3' if third else ''))
    pkgs=sorted(x.split(':',1)[1] for x in o.splitlines() if x.startswith('package:'))
    print(CYAN+'\n'+title+RESET)
    print(f"{'N°':>4} {'PACKAGE':<40} {'APPLICATION':<23} {'NIVEAU':<12} UTILITE")
    print('-'*112)
    rows=[]
    for i,p in enumerate(pkgs,1):
        inf=_aa_info(dev,p);lvl,_=_aa_risk(dev,p,action);rows.append(inf)
        print(f"{i:>4} {p[:40]:<40} {inf['name'][:23]:<23} {lvl:<12} {inf['utility'][:55]}")
    try:n=int(input('\nNuméro (0=retour): ').strip())
    except:return None
    if n==0 or not 1<=n<=len(rows):return None
    inf=rows[n-1]
    if inf['package'] not in AA_KNOWN:
        newer=_aa_info(dev,inf['package'],online=True)
        if newer['source'] in ('Google Play','F-Droid'):inf=newer
    return inf

def _aa_confirm(dev,inf,action):
    lvl,why=_aa_risk(dev,inf['package'],action);col=GREEN if lvl=='OK' else YELLOW if lvl=='A VERIFIER' else RED
    print(f"\nApplication : {inf['name']}\nPackage     : {inf['package']}\nUtilité     : {inf['utility']}\nCatégorie   : {inf['category']}")
    print(col+f'Niveau : {lvl}'+RESET);print('Pourquoi : '+why)
    if lvl=='DECONSEILLE':return input('Tape CONFIRMER pour continuer : ').strip()=='CONFIRMER'
    return input('Continuer ? (o/N): ').strip().lower() in ('o','oui','y','yes')

# ---------- Files /sdcard ----------
def _aa_remote_entries(dev,current):
    rc,o,e=_aa_sh(dev,f'ls -1Ap {_aa_q(current)} 2>/dev/null')
    ents=[]
    for ln in o.splitlines():
        s=ln.strip();
        if not s or s in ('.','..'):continue
        d=s.endswith('/');ents.append((s.rstrip('/'),d))
    return sorted(ents,key=lambda x:(not x[1],x[0].lower())),e

def _aa_browser(dev,mode='file',start='/sdcard'):
    cur=start.rstrip('/') or '/sdcard'
    while True:
        ents,e=_aa_remote_entries(dev,cur);print(CYAN+f'\n{cur}/'+RESET)
        if e:print(YELLOW+e+RESET)
        for i,(n,d) in enumerate(ents,1):print(f'[{i}] {n + "/" if d else n}')
        print('[0] '+('Choisir ce dossier' if mode=='dir' else 'Annuler'));print('[..] Dossier précédent');print('[M] Créer un dossier ici')
        r=input('> ').strip()
        if r.lower()=='m':
            n=input('Nom du nouveau dossier : ').strip()
            if not n or '/' in n or n in ('.','..'):print(RED+'Nom invalide.'+RESET);continue
            rc,o,e=_aa_sh(dev,f'mkdir -p {_aa_q(cur+"/"+n)}');print((GREEN if rc==0 else RED)+('Dossier créé.' if rc==0 else (e or o or 'Refusé'))+RESET);continue
        if r=='..':
            if cur not in ('/sdcard','/storage/emulated/0'):cur=cur.rsplit('/',1)[0] or '/sdcard'
            continue
        if r=='0':return cur if mode=='dir' else None
        try:n,d=ents[int(r)-1]
        except:print(RED+'Choix invalide.'+RESET);continue
        p=cur.rstrip('/')+'/'+n
        if d:cur=p
        elif mode=='file':return p

def option_pull_file():
    dev=get_selected_device();
    if not dev:return
    remote=_aa_browser(dev,'file')
    if not remote:return
    dest=os.path.expanduser(input('Chemin de sortie sur cet ordinateur/Termux : ').strip())
    if not dest:return
    _Path(dest).mkdir(parents=True,exist_ok=True) if not _Path(dest).suffix else _Path(dest).parent.mkdir(parents=True,exist_ok=True)
    rc,o,e=_aa_adb(dev,'pull',remote,dest,timeout=300);print((GREEN if rc==0 else RED)+(o or e)+RESET)

def option_push_file():
    dev=get_selected_device();
    if not dev:return
    src=os.path.expanduser(input('Fichier sur cet ordinateur/Termux : ').strip())
    if not _Path(src).is_file():print(RED+'Fichier introuvable.'+RESET);return
    folder=_aa_browser(dev,'dir')
    if not folder:return
    rc,o,e=_aa_adb(dev,'push',src,folder.rstrip('/')+'/',timeout=300);print((GREEN if rc==0 else RED)+(o or e)+RESET)

# ---------- Contacts / SMS / calls ----------
def _aa_rows(text):
    rows=[]
    for ln in (text or '').splitlines():
        if not ln.strip().startswith('Row:'):continue
        x=ln.split(': ',1)[1] if ': ' in ln else ln;d={};last=None
        for part in x.split(', '):
            if '=' in part:last,val=part.split('=',1);last=last.strip();d[last]=val
            elif last:d[last]+=', '+part
        rows.append(d)
    return rows

def _aa_norm(n):
    s=re.sub(r'\D+','',str(n or ''))
    if s.startswith('00'):s=s[2:]
    if len(s)==10 and s.startswith('0'):s='33'+s[1:]
    return s

def _aa_contacts(dev):
    rows=[];last_err=''
    for cmd in ("content query --uri content://com.android.contacts/data/phones --projection contact_id:display_name:data1:data2:data3","content query --uri content://contacts/phones --projection contact_id:display_name:number:type:label"):
        rc,o,e=_aa_sh(dev,cmd,timeout=120);rows=_aa_rows(o);last_err=e
        if rows:break
    cs={}
    for r in rows:
        cid=str(r.get('contact_id') or r.get('_id') or len(cs)+1);c=cs.setdefault(cid,{'contact_id':cid,'display_name':r.get('display_name',''),'phones':[],'emails':[]})
        num=r.get('data1') or r.get('number') or ''
        if num:c['phones'].append({'number':num,'normalized':_aa_norm(num),'type':r.get('data2') or r.get('type'),'label':r.get('data3') or r.get('label')})
    rc,o,e=_aa_sh(dev,"content query --uri content://com.android.contacts/data/emails --projection contact_id:display_name:data1:data2:data3",timeout=120)
    for r in _aa_rows(o):
        cid=str(r.get('contact_id') or '');
        if not cid:continue
        c=cs.setdefault(cid,{'contact_id':cid,'display_name':r.get('display_name',''),'phones':[],'emails':[]})
        if r.get('data1'):c['emails'].append({'address':r.get('data1'),'type':r.get('data2'),'label':r.get('data3')})
    return list(cs.values()),last_err or e

def _aa_cmap(cs):
    d={}
    for c in cs:
        for p in c.get('phones',[]):
            if p.get('normalized'):d[p['normalized']]=c.get('display_name') or 'Inconnu'
    return d

def _aa_cname(num,mp):
    n=_aa_norm(num)
    if n in mp:return mp[n]
    for k,v in mp.items():
        if len(n)>=8 and len(k)>=8 and (n.endswith(k[-9:]) or k.endswith(n[-9:])):return v
    return 'Inconnu'

def _aa_iso(v):
    try:
        n=int(v);n=n/1000 if n>10000000000 else n;return datetime.datetime.fromtimestamp(n).isoformat(timespec='seconds')
    except:return str(v or '')

def option_dump_contacts():
    dev=get_selected_device();
    if not dev:return
    cs,e=_aa_contacts(dev)
    if not cs:print(RED+'ACCÈS REFUSÉ ou aucun contact retourné. '+(e or '')+RESET);return
    payload={'metadata':{'exported_at':datetime.datetime.now().isoformat(timespec='seconds'),'count':len(cs),'format':'Android ADB Admin contacts dump'},'contacts':cs}
    name=f'contacts_{_aa_ts()}.json';kind,target=_aa_destination(dev,name)
    if not kind:return
    with _tempfile.TemporaryDirectory() as td:
        p=_Path(td)/name;p.write_text(_json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');ok,msg=_aa_deliver(dev,p,kind,target)
    print((GREEN if ok else RED)+(('✓ '+msg) if ok else ('✗ '+msg))+RESET)

def _aa_destination(dev,name):
    print('\n[1] Ordinateur / machine locale\n[2] Téléphone\n[0] Annuler');c=input('> ').strip()
    if c=='1':
        d=os.path.expanduser(input('Dossier de sortie : ').strip() or '.');_Path(d).mkdir(parents=True,exist_ok=True);return 'local',str(_Path(d)/name)
    if c=='2':
        d=_aa_browser(dev,'dir');return ('phone',d.rstrip('/')+'/'+name) if d else (None,None)
    return None,None

def _aa_deliver(dev,local,kind,target):
    if kind=='local':shutil.copy2(str(local),target);return True,target
    rc,o,e=_aa_adb(dev,'push',str(local),target,timeout=300);return rc==0,(target if rc==0 else (e or o))

def _aa_sms(dev):
    rc,o,e=_aa_sh(dev,'content query --uri content://sms/ --projection _id:thread_id:address:body:date:type:read:status',timeout=180);return _aa_rows(o),e

def _aa_calls(dev):
    rc,o,e=_aa_sh(dev,'content query --uri content://call_log/calls --projection _id:number:date:duration:type:name',timeout=180);return _aa_rows(o),e

def _aa_enrich_sms(rows,mp):
    z=[]
    for r in rows:
        x=dict(r);x['contact']=_aa_cname(r.get('address'),mp);x['date_iso']=_aa_iso(r.get('date'));x['direction']={'1':'received','2':'sent','3':'draft','4':'outbox','5':'failed','6':'queued'}.get(str(r.get('type','')),str(r.get('type','')));z.append(x)
    return z

def _aa_enrich_calls(rows,mp):
    z=[]
    for r in rows:
        x=dict(r);x['contact']=r.get('name') or _aa_cname(r.get('number'),mp);x['date_iso']=_aa_iso(r.get('date'));x['call_type']={'1':'incoming','2':'outgoing','3':'missed','4':'voicemail','5':'rejected','6':'blocked','7':'answered_externally'}.get(str(r.get('type','')),str(r.get('type','')))
        try:x['duration_seconds']=int(r.get('duration') or 0)
        except:x['duration_seconds']=r.get('duration');z.append(x)
        if x not in z:z.append(x)
    return z

def _aa_pick_contact(rows,key):
    u={}
    for r in rows:
        n=r.get(key) or '';nn=_aa_norm(n)
        if nn:u.setdefault(nn,{'number':n,'name':r.get('contact') or 'Inconnu'})
    arr=sorted(u.values(),key=lambda x:(x['name']=='Inconnu',x['name'].lower(),x['number']))
    for i,c in enumerate(arr,1):print(f"[{i}] {c['name']:<28} {c['number']}")
    print('[0] Retour')
    try:n=int(input('> '));return None if n==0 else arr[n-1]
    except:return None

def _aa_sms_html(path,rows,name,num):
    parts=["<!doctype html><html><head><meta charset='utf-8'><style>body{font-family:system-ui;max-width:900px;margin:auto;padding:20px;background:#eee}.m{max-width:75%;padding:10px 14px;margin:8px;border-radius:14px;white-space:pre-wrap}.sent{margin-left:auto;background:#d8f5d0}.received{background:#fff}.d{font-size:.8em;color:#666}</style></head><body>",f'<h1>{html.escape(name)}</h1><p>{html.escape(num)}</p>']
    for r in sorted(rows,key=lambda x:str(x.get('date') or '')):parts.append(f"<div class='m {'sent' if r.get('direction')=='sent' else 'received'}'><div>{html.escape(str(r.get('body') or ''))}</div><div class='d'>{html.escape(r.get('date_iso',''))} — {html.escape(r.get('direction',''))}</div></div>")
    parts.append('</body></html>');_Path(path).write_text('\n'.join(parts),encoding='utf-8')

def _aa_recordings(dev):
    root=AA_CFG.get('recordings_path','/sdcard/Recordings');rc,o,e=_aa_sh(dev,f"find {_aa_q(root)} -type f \\( -iname '*.ogg' -o -iname '*.oga' \\) 2>/dev/null",timeout=120);arr=[]
    for p in o.splitlines():
        p=p.strip();_,st,_=_aa_sh(dev,f"stat -c '%Y' {_aa_q(p)} 2>/dev/null")
        try:mt=int(st.splitlines()[0])
        except:mt=0
        if p:arr.append({'path':p,'mtime':mt})
    return arr,e

def _aa_match(recs,calls,name,num):
    avail=list(recs);res=[];digits=_aa_norm(num);tok=_aa_safe(name).lower().replace('-','')
    for call in sorted(calls,key=lambda x:str(x.get('date') or '')):
        cand=[]
        for rec in avail:
            base=_Path(rec['path']).name.lower();direct=(digits and digits[-8:] in re.sub(r'\D+','',base)) or (tok and tok!='inconnu' and tok in _aa_safe(base).lower().replace('-',''))
            if direct:cand.append((0,'filename',rec));continue
            try:
                end=int(call.get('date') or 0)/1000+int(call.get('duration') or 0);diff=abs(rec['mtime']-end)
                if rec['mtime'] and diff<=600:cand.append((diff,'timestamp',rec))
            except:pass
        cand.sort(key=lambda x:x[0])
        if not cand:res.append({'call':call,'recording':None,'confidence':'none'});continue
        if cand[0][1]=='timestamp' and len(cand)>1 and abs(cand[1][0]-cand[0][0])<30:res.append({'call':call,'recording':None,'confidence':'ambiguous'});continue
        best=cand[0];avail.remove(best[2]);res.append({'call':call,'recording':best[2],'confidence':'high' if best[1]=='filename' else 'medium'})
    return res

def _aa_export_sms(dev):
    cs,_=_aa_contacts(dev);mp=_aa_cmap(cs);raw,e=_aa_sms(dev)
    if not raw:print(RED+'Aucun SMS accessible. '+(e or '')+RESET);return
    rows=_aa_enrich_sms(raw,mp);c=_aa_pick_contact(rows,'address')
    if not c:return
    nr=_aa_norm(c['number']);chosen=[r for r in rows if _aa_norm(r.get('address'))==nr];name=f"SMS_{_aa_safe(c['name'])}_{nr}_{_aa_ts()}.html";kind,target=_aa_destination(dev,name)
    if not kind:return
    with _tempfile.TemporaryDirectory() as td:p=_Path(td)/name;_aa_sms_html(p,chosen,c['name'],c['number']);ok,msg=_aa_deliver(dev,p,kind,target)
    print((GREEN if ok else RED)+(('✓ '+msg) if ok else ('✗ '+msg))+RESET)

def _aa_export_calls(dev):
    cs,_=_aa_contacts(dev);mp=_aa_cmap(cs);raw,e=_aa_calls(dev)
    if not raw:print(RED+'Aucun journal d’appels accessible. '+(e or '')+RESET);return
    rows=_aa_enrich_calls(raw,mp);c=_aa_pick_contact(rows,'number')
    if not c:return
    nr=_aa_norm(c['number']);chosen=[r for r in rows if _aa_norm(r.get('number'))==nr];recs,_=_aa_recordings(dev);matches=_aa_match(recs,chosen,c['name'],c['number']);folder=f"CALL_{_aa_safe(c['name'])}_{nr}_{_aa_ts()}";kind,target=_aa_destination(dev,folder+'.tar.gz')
    if not kind:return
    with _tempfile.TemporaryDirectory() as td:
        root=_Path(td)/folder;root.mkdir();logs=[]
        for i,m in enumerate(matches,1):
            call=dict(m['call']);call['recording_confidence']=m['confidence'];rec=m['recording']
            if rec:
                fn=f"CALL_{_aa_safe(c['name'])}_{nr}_{_aa_safe(call.get('date_iso') or i)}.ogg";rc,o,er=_aa_adb(dev,'pull',rec['path'],str(root/fn),timeout=300)
                if rc==0:call['recording_file']=fn
                else:call['recording_error']=er or o
            logs.append(call)
        (root/'call_logs.json').write_text(_json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8');arc=_Path(td)/(folder+'.tar.gz')
        with _tarfile.open(arc,'w:gz') as tf:tf.add(root,arcname=folder)
        with _tarfile.open(arc,'r:gz') as tf:assert tf.getmembers()
        ok,msg=_aa_deliver(dev,arc,kind,target)
    print((GREEN if ok else RED)+(('✓ '+msg) if ok else ('✗ '+msg))+RESET)

def _aa_db(path,contacts,sms,calls):
    db=_sqlite3.connect(str(path));c=db.cursor();c.execute('CREATE TABLE contacts(contact_id TEXT,display_name TEXT,json TEXT)');c.execute('CREATE TABLE sms(id TEXT,address TEXT,contact TEXT,body TEXT,date_iso TEXT,direction TEXT,json TEXT)');c.execute('CREATE TABLE calls(id TEXT,number TEXT,contact TEXT,date_iso TEXT,duration_seconds TEXT,call_type TEXT,recording_file TEXT,json TEXT)')
    for x in contacts:c.execute('INSERT INTO contacts VALUES(?,?,?)',(str(x.get('contact_id','')),x.get('display_name',''),_json.dumps(x,ensure_ascii=False)))
    for x in sms:c.execute('INSERT INTO sms VALUES(?,?,?,?,?,?,?)',(str(x.get('_id','')),x.get('address',''),x.get('contact',''),x.get('body',''),x.get('date_iso',''),x.get('direction',''),_json.dumps(x,ensure_ascii=False)))
    for x in calls:c.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?,?)',(str(x.get('_id','')),x.get('number',''),x.get('contact',''),x.get('date_iso',''),str(x.get('duration_seconds','')),x.get('call_type',''),x.get('recording_file',''),_json.dumps(x,ensure_ascii=False)))
    db.commit();db.close()

def _aa_index(path,contacts,sms,calls):
    data=_json.dumps({'contacts':contacts,'sms':sms,'calls':calls},ensure_ascii=False).replace('</','<\\/')
    page="""<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>Emergency Dump</title><style>body{font-family:system-ui;background:#111;color:#eee;margin:0}header,main{padding:16px}header{background:#222;position:sticky;top:0}input,button{padding:8px;margin:3px}table{width:100%;border-collapse:collapse}th,td{padding:7px;border-bottom:1px solid #444;text-align:left;vertical-align:top}a{color:#8cc8ff}</style></head><body><header><h1>Emergency Dump</h1><input id=q size=45 placeholder='Rechercher...' oninput='render()'><button onclick=\"tab='sms';render()\">SMS</button><button onclick=\"tab='calls';render()\">Appels</button><button onclick=\"tab='contacts';render()\">Contacts</button></header><main id=o></main><script>const D=DATA;let tab='sms';const e=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));function render(){let q=document.getElementById('q').value.toLowerCase(),r=D[tab].filter(x=>JSON.stringify(x).toLowerCase().includes(q)),h='<p>'+r.length+' élément(s)</p><table>';if(tab==='sms')h+='<tr><th>Date</th><th>Contact</th><th>Numéro</th><th>Direction</th><th>Message</th></tr>'+r.map(x=>`<tr><td>${e(x.date_iso)}</td><td>${e(x.contact)}</td><td>${e(x.address)}</td><td>${e(x.direction)}</td><td>${e(x.body)}</td></tr>`).join('');if(tab==='calls')h+='<tr><th>Date</th><th>Contact</th><th>Numéro</th><th>Type</th><th>Durée</th><th>Audio</th></tr>'+r.map(x=>`<tr><td>${e(x.date_iso)}</td><td>${e(x.contact)}</td><td>${e(x.number)}</td><td>${e(x.call_type)}</td><td>${e(x.duration_seconds)}</td><td>${x.recording_file?`<audio controls src='${e(x.recording_file)}'></audio>`:''}</td></tr>`).join('');if(tab==='contacts')h+='<tr><th>Nom</th><th>Données</th></tr>'+r.map(x=>`<tr><td>${e(x.display_name)}</td><td><pre>${e(JSON.stringify(x,null,2))}</pre></td></tr>`).join('');document.getElementById('o').innerHTML=h+'</table>'}render()</script></body></html>""".replace('DATA',data)
    _Path(path).write_text(page,encoding='utf-8')

def _aa_emergency_export(dev,delete_after=False):
    cs,ce=_aa_contacts(dev);mp=_aa_cmap(cs);sr,se=_aa_sms(dev);cr,cae=_aa_calls(dev);sms=_aa_enrich_sms(sr,mp);calls=_aa_enrich_calls(cr,mp);recs,re=_aa_recordings(dev);name='Emergency_Dump_'+_aa_ts();kind,target=_aa_destination(dev,name+'.tar.gz')
    if not kind:return
    with _tempfile.TemporaryDirectory() as td:
        root=_Path(td)/name;(root/'database').mkdir(parents=True);(root/'calls'/'recordings').mkdir(parents=True);recorded={}
        for i,r in enumerate(recs,1):
            fn=f'{i:04d}_{_aa_safe(_Path(r["path"]).name)}';fn=fn if fn.lower().endswith(('.ogg','.oga')) else fn+'.ogg';rc,o,e=_aa_adb(dev,'pull',r['path'],str(root/'calls'/'recordings'/fn),timeout=300)
            if rc==0:recorded[r['path']]='calls/recordings/'+fn
        for m in _aa_match(recs,calls,'',''):
            if m['recording'] and m['recording']['path'] in recorded:m['call']['recording_file']=recorded[m['recording']['path']];m['call']['recording_confidence']=m['confidence']
        for fn,obj in [('contacts.json',cs),('sms.json',sms),('calls.json',calls)]: (root/'database'/fn).write_text(_json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
        manifest={'created_at':datetime.datetime.now().isoformat(timespec='seconds'),'counts':{'contacts':len(cs),'sms':len(sms),'calls':len(calls),'recordings':len(recorded)},'recordings_path':AA_CFG.get('recordings_path'), 'errors':[x for x in (ce,se,cae,re) if x]};(root/'database'/'manifest.json').write_text(_json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');_aa_db(root/'database'/'emergency.db',cs,sms,calls);_aa_index(root/'index.html',cs,sms,calls);arc=_Path(td)/(name+'.tar.gz')
        with _tarfile.open(arc,'w:gz') as tf:tf.add(root,arcname=name)
        with _tarfile.open(arc,'r:gz') as tf:
            names=set(tf.getnames());required={name+'/index.html',name+'/database/emergency.db',name+'/database/sms.json',name+'/database/calls.json',name+'/database/contacts.json',name+'/database/manifest.json'}
            if not required.issubset(names):print(RED+'Archive incomplète : aucune suppression.'+RESET);return
        ok,msg=_aa_deliver(dev,arc,kind,target)
    if not ok:print(RED+'Échec export : '+msg+' — aucune suppression.'+RESET);return
    print(GREEN+'✓ Archive vérifiée : '+msg+RESET)
    if delete_after:_aa_emergency_delete(dev)

def _aa_emergency_delete(dev):
    s,_=_aa_sms(dev);c,_=_aa_calls(dev);r,_=_aa_recordings(dev);print(RED+'\n⚠ URGENCE — SUPPRESSION TOTALE'+RESET);print(f'SMS: {len(s)} | appels: {len(c)} | .ogg: {len(r)}')
    if input('Tape SUPPRIMER TOUT : ').strip()!='SUPPRIMER TOUT':print(YELLOW+'Annulé.'+RESET);return
    for label,cmd in [('SMS','content delete --uri content://sms/'),('Call logs','content delete --uri content://call_log/calls')]:
        rc,o,e=_aa_sh(dev,cmd,timeout=180);print(('✓ ' if rc==0 else '✗ ')+label+((' — '+(e or o)) if (e or o) else ''))
    for x in r:
        rc,o,e=_aa_sh(dev,f'rm -f {_aa_q(x["path"])}');print(('✓ ' if rc==0 else '✗ ')+x['path'])

def option_dump_sms_call_logs():
    dev=get_selected_device();
    if not dev:return
    while True:
        print_banner();print('[1] SMS d’un contact\n[2] Appels d’un contact + .ogg\n[3] Urgence\n[0] Retour');c=input('> ').strip()
        if c=='1':_aa_export_sms(dev);input('\nEntrée...')
        elif c=='2':_aa_export_calls(dev);input('\nEntrée...')
        elif c=='3':
            print('[1] Exporter tout\n[2] Exporter puis supprimer tout\n[3] Supprimer tout sans export\n[0] Retour');x=input('> ').strip()
            if x=='1':_aa_emergency_export(dev,False);input('\nEntrée...')
            elif x=='2':_aa_emergency_export(dev,True);input('\nEntrée...')
            elif x=='3':_aa_emergency_delete(dev);input('\nEntrée...')
        elif c=='0':return

# ---------- Apps / launcher ----------
def option_show_apk_list():
    dev=get_selected_device();
    if not dev:return
    _,o,_=_aa_sh(dev,'pm list packages');pkgs=sorted(x.split(':',1)[1] for x in o.splitlines() if x.startswith('package:'));print(f"{'N°':>4} {'PACKAGE':<40} {'APPLICATION':<23} UTILITE")
    for i,p in enumerate(pkgs,1):inf=_aa_info(dev,p);print(f"{i:>4} {p[:40]:<40} {inf['name'][:23]:<23} {inf['utility'][:60]}")

def option_delete_apk():
    dev=get_selected_device();
    if not dev:return
    inf=_aa_pick_pkg(dev,'APPLICATIONS / SUPPRESSION',False,'uninstall')
    if not inf:return
    print('[1] Désinstaller pour utilisateur 0\n[2] Désactiver\n[3] Activer\n[4] Forcer l’arrêt\n[5] Permissions / AppOps\n[0] Retour');c=input('> ').strip();pkg=inf['package']
    if c=='1':act='uninstall';cmd=f'pm uninstall --user 0 {pkg}'
    elif c=='2':act='disable';cmd=f'pm disable-user --user 0 {pkg}'
    elif c=='3':act='inspect';cmd=f'pm enable --user 0 {pkg}'
    elif c=='4':act='force_stop';cmd=f'am force-stop {pkg}'
    elif c=='5':
        _,o,e=_aa_sh(dev,f'dumpsys package {pkg}');print('\n'.join(x.strip() for x in o.splitlines() if 'android.permission.' in x or 'granted=' in x));_,o,e=_aa_sh(dev,f'cmd appops get {pkg}');print(o or e);return
    else:return
    if c!='3' and not _aa_confirm(dev,inf,act):return
    rc,o,e=_aa_sh(dev,cmd);print((GREEN if rc==0 else RED)+(o or e or 'Commande terminée')+RESET)

def option_start_app():
    dev=get_selected_device();
    if not dev:return
    _,o,_=_aa_sh(dev,'cmd package query-activities --brief --components -a android.intent.action.MAIN -c android.intent.category.LAUNCHER');pkgs=[]
    for ln in o.splitlines():
        if '/' in ln:
            p=ln.strip().split('/',1)[0]
            if re.fullmatch(r'[A-Za-z0-9._]+',p) and p not in pkgs:pkgs.append(p)
    rows=[]
    for i,p in enumerate(sorted(pkgs),1):inf=_aa_info(dev,p);rows.append(inf);print(f'[{i}] {inf["name"]}')
    print('[0] Retour')
    try:n=int(input('> '))
    except:return
    if n==0 or not 1<=n<=len(rows):return
    inf=rows[n-1];rc,o,e=_aa_sh(dev,f'monkey -p {inf["package"]} -c android.intent.category.LAUNCHER 1');print((GREEN if rc==0 and 'No activities found' not in (o+e) else RED)+(('✓ '+inf['name']) if rc==0 else (e or o))+RESET)

def _aa_launcher_component(dev,pkg):
    for cmd in (f'cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER {pkg}',f'cmd package query-activities --brief --components -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p {pkg}'):
        _,o,_=_aa_sh(dev,cmd)
        for ln in o.splitlines():
            s=ln.strip()
            if s.startswith(pkg+'/'):return s
    return None

def _aa_launcher_pkg(dev):
    _,o,_=_aa_sh(dev,'cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME');return o.splitlines()[-1].strip() if o else ''

def _aa_query_launcher_components(dev, include_disabled=False):
    """Return launcher components exposed by PackageManager.

    HyperOS/Android versions do not all accept the same cmd package syntax, so
    several read-only variants are tried.  MATCH_DISABLED_COMPONENTS = 0x200.
    """
    cmds=[]
    base='cmd package query-activities --brief --components -a android.intent.action.MAIN -c android.intent.category.LAUNCHER'
    if include_disabled:
        cmds += [
            base+' --query-flags 512',
            base+' --flags 512',
            'cmd package query-activities --brief --components --query-flags 512 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER',
        ]
    else:
        cmds=[base]
    out=set()
    for cmd in cmds:
        rc,o,e=_aa_sh(dev,cmd)
        if rc!=0:
            continue
        for ln in o.splitlines():
            v=ln.strip()
            if '/' in v and not v.lower().startswith(('no activities','error','unknown')):
                # Some builds prefix the result with an index or whitespace.
                v=v.split()[-1]
                if '/' in v:
                    out.add(v)
        if out:
            break
    return out

def _aa_disabled_launcher_components(dev):
    """Find launcher activities that exist but are disabled.

    This also discovers icons hidden before Android ADB Admin recorded them.
    """
    enabled=_aa_query_launcher_components(dev,False)
    all_components=_aa_query_launcher_components(dev,True)
    found={c.split('/',1)[0]:c for c in sorted(all_components-enabled) if '/' in c}

    # Keep previously recorded components too, even if this Android build does
    # not support querying disabled activities through cmd package.
    for pkg,comp in AA_CFG.get('hidden_launcher_components',{}).items():
        if pkg and comp:
            found.setdefault(pkg,comp)
    return found

def _aa_disabled_packages(dev):
    _,o,_=_aa_sh(dev,'pm list packages -d')
    out=[]
    for ln in o.splitlines():
        if ln.startswith('package:'):
            pkg=ln.split(':',1)[1].strip()
            if pkg: out.append(pkg)
    return sorted(set(out))

def _aa_home_search_state(dev):
    """Read the launcher search entrance state directly from Android.

    QSB_SCROLL_ENTRANCE_STATUS controls Xiaomi's launcher search entrance on
    builds that expose it.  Some HyperOS releases implement the swipe-down
    gesture internally in com.miui.home and expose no writable settings key;
    those builds are reported as unsupported instead of claiming success.
    """
    _,raw,_=_aa_sh(dev,'settings get system QSB_SCROLL_ENTRANCE_STATUS')
    raw=(raw or '').strip()
    if raw in ('1','true','on'):
        return True,raw,'QSB_SCROLL_ENTRANCE_STATUS'
    if raw in ('0','false','off'):
        return False,raw,'QSB_SCROLL_ENTRANCE_STATUS'

    # Best-effort discovery only; we deliberately do not write unknown keys.
    candidates=[]
    for table in ('system','secure','global'):
        _,txt,_=_aa_sh(dev,f'settings list {table}')
        for ln in txt.splitlines():
            low=ln.lower()
            if ('search' in low or 'qsb' in low) and ('home' in low or 'launcher' in low or 'scroll' in low or 'swipe' in low):
                candidates.append(f'{table}:{ln.strip()}')
    return None,raw,'; '.join(candidates[:5])

def _aa_set_home_search(dev, enable):
    state,_,source=_aa_home_search_state(dev)
    if source!='QSB_SCROLL_ENTRANCE_STATUS':
        return False,'Ce launcher HyperOS n’expose pas de réglage ADB sûr pour ce geste.'
    value='1' if enable else '0'
    rc,o,e=_aa_sh(dev,f'settings put system QSB_SCROLL_ENTRANCE_STATUS {value}')
    if rc!=0:
        return False,(e or o or 'Écriture refusée.')
    after,_,_=_aa_home_search_state(dev)
    if after is enable:
        return True,'Paramètre modifié et relu depuis Android.'
    return False,'La modification n’a pas pu être vérifiée.'

def manager_launcher():
    dev=get_selected_device()
    if not dev:return
    while True:
        print_banner()
        home=_aa_launcher_pkg(dev)
        st,raw,src=_aa_home_search_state(dev)
        st_txt='ACTIVÉE' if st is True else ('DÉSACTIVÉE' if st is False else 'NON DÉTECTÉE')
        print('Launcher détecté : '+(home or 'inconnu'))
        print('[1] Diagnostic HyperOS / launcher')
        print('[2] Masquer l’icône d’une application')
        print('[3] Restaurer / démasquer une application')
        print(f'[4] Recherche écran d’accueil : {st_txt}')
        print('[0] Retour')
        c=input('> ').strip()
        if c=='0':return
        if c=='1':
            print('\nHOME : '+home)
            _,o,e=_aa_sh(dev,'dumpsys package com.miui.home | grep -E "versionName|versionCode" | head -5')
            print(o or e)
            print('Recherche : '+st_txt)
            print('Source : '+(src or 'inconnue'))
            print(YELLOW+'Le geste exact dépend de la version HyperOS. Le programme ne déclare une modification réussie que si Android la confirme.'+RESET)
        elif c=='2':
            inf=_aa_pick_pkg(dev,'MASQUER UNE ICÔNE',False,'disable_component')
            if not inf:continue
            comp=_aa_launcher_component(dev,inf['package'])
            if not comp:print(YELLOW+'Aucune Activity MAIN/LAUNCHER trouvée.'+RESET);continue
            if not _aa_confirm(dev,inf,'disable_component'):continue
            rc,o,e=_aa_sh(dev,f'pm disable-user --user 0 {comp}')
            if rc==0:
                AA_CFG.setdefault('hidden_launcher_components',{})[inf['package']]=comp;_aa_save(AA_CFG)
            enabled=_aa_query_launcher_components(dev,False)
            print(GREEN+'✓ Icône masquée et composant mémorisé.'+RESET if rc==0 and comp not in enabled else RED+(e or o or 'Échec de vérification.')+RESET)
        elif c=='3':
            hidden=_aa_disabled_launcher_components(dev)
            disabled_pkgs=_aa_disabled_packages(dev)
            entries=[]
            for pkg,comp in hidden.items(): entries.append(('component',pkg,comp))
            # Whole-package disabled apps are also restorable and used by some
            # manual debloat/hide procedures.
            for pkg in disabled_pkgs:
                if pkg not in hidden: entries.append(('package',pkg,pkg))
            if not entries:
                print(YELLOW+'Aucune application/composant launcher désactivé détecté.'+RESET);input('\nEntrée...');continue
            for i,(kind,pkg,target) in enumerate(entries,1):
                suffix='composant launcher' if kind=='component' else 'application désactivée'
                print(f'[{i}] {_aa_info(dev,pkg)["name"]} — {suffix}')
            print('[0] Retour')
            try:n=int(input('> '))
            except:continue
            if n==0 or not 1<=n<=len(entries):continue
            kind,pkg,target=entries[n-1]
            if kind=='component':
                rc,o,e=_aa_sh(dev,f'pm enable --user 0 {target}')
                now=_aa_query_launcher_components(dev,False)
                ok=rc==0 and target in now
            else:
                rc,o,e=_aa_sh(dev,f'pm enable --user 0 {pkg}')
                _,chk,_=_aa_sh(dev,'pm list packages -d')
                ok=rc==0 and ('package:'+pkg) not in chk.splitlines()
            if ok:
                AA_CFG.setdefault('hidden_launcher_components',{}).pop(pkg,None);_aa_save(AA_CFG)
                print(GREEN+'✓ Application restaurée / démasquée.'+RESET)
            else: print(RED+'La restauration n’a pas pu être vérifiée. '+(e or o)+RESET)
        elif c=='4':
            if st is None:
                print(YELLOW+'État non modifiable de façon sûre par ADB sur cette version du launcher.'+RESET)
                if src: print('Indices détectés : '+src)
            else:
                action='désactiver' if st else 'activer'
                print(f'Recherche actuellement {st_txt}.')
                print(f'[1] {action.capitalize()}\n[0] Retour')
                a=input('> ').strip()
                if a=='1':
                    ok,msg=_aa_set_home_search(dev,not st)
                    print((GREEN+'✓ ' if ok else YELLOW+'NON SUPPORTÉ / non vérifié : ')+msg+RESET)
        input('\nEntrée...')

# ---------- Wi-Fi connection ----------
def option_connect_device():
    print_banner();print('[1] Connexion ADB Wi-Fi\n[2] Configuration / réparation via USB\n[0] Retour');c=input('> ').strip();port=int(AA_CFG.get('wifi_port',5555))
    if c=='0':return
    if c=='2':
        usb=_aa_usb_devices()
        if not usb:print(RED+'Aucun appareil USB autorisé.'+RESET);return
        rc,o,e=_aa_adb(usb[0][0],'tcpip',str(port));print(o or e)
        if rc!=0:return
    old=AA_CFG.get('wifi_ip','');ip=input('Adresse IP du téléphone'+(f' [{old}]' if old else '')+' : ').strip() or old
    if not re.fullmatch(r'(?:\d{1,3}\.){3}\d{1,3}',ip or ''):print(RED+'Adresse invalide.'+RESET);return
    rc,o,e=_aa_cmd(['adb','connect',f'{ip}:{port}']);print(o or e);time.sleep(.4)
    if any(s.startswith(ip+':') and st=='device' for s,st in _aa_wifi_devices()):AA_CFG['wifi_ip']=ip;_aa_save(AA_CFG);print(GREEN+'✓ Connexion Wi-Fi vérifiée.'+RESET)
    else:print(RED+'Connexion non vérifiée.'+RESET)

def option_disconnect_device():
    for s,st in _aa_wifi_devices():_aa_cmd(['adb','disconnect',s])
    print(GREEN+'ADB Wi-Fi déconnecté.'+RESET)

# ---------- Quick profiles ----------
def _aa_try_shell(dev, cmd):
    rc,o,e=_aa_sh(dev,cmd)
    return rc,(o or e).strip()

def _aa_carrier_payment_enable(dev):
    """Restore the carrier-billing access that previously fixed Play Store billing.

    Commands are applied individually because OEM/Android builds may refuse a
    permission that is not requested by the installed Play Store version.
    """
    steps=[
        ('Xiaomi Payment', 'pm enable --user 0 com.xiaomi.payment'),
        ('Play Store READ_SMS', 'pm grant com.android.vending android.permission.READ_SMS'),
        ('Play Store RECEIVE_SMS', 'pm grant com.android.vending android.permission.RECEIVE_SMS'),
        ('Play Store SEND_SMS', 'pm grant com.android.vending android.permission.SEND_SMS'),
        ('Play Store READ_PHONE_STATE', 'pm grant com.android.vending android.permission.READ_PHONE_STATE'),
        ('AppOps READ_SMS', 'cmd appops set com.android.vending READ_SMS allow'),
        ('AppOps RECEIVE_SMS', 'cmd appops set com.android.vending RECEIVE_SMS allow'),
        ('AppOps SEND_SMS', 'cmd appops set com.android.vending SEND_SMS allow'),
    ]
    results=[]
    for label,cmd in steps:
        rc,msg=_aa_try_shell(dev,cmd); results.append((label,rc,msg))
    return results

def _aa_carrier_payment_status(dev):
    _,pay,_=_aa_sh(dev,'pm list packages -e com.xiaomi.payment')
    _,ops,_=_aa_sh(dev,'cmd appops get com.android.vending')
    wanted={}
    for op in ('READ_SMS','RECEIVE_SMS','SEND_SMS'):
        m=re.search(r'(?m)^'+re.escape(op)+r':\s*([^\n]+)',ops)
        wanted[op]=m.group(1).strip() if m else 'inconnu'
    return ('package:com.xiaomi.payment' in pay),wanted

def manager_profiles():
    dev=get_selected_device()
    if dev is None:return
    while True:
        enabled,ops=_aa_carrier_payment_status(dev)
        state='ACTIF' if enabled and all(v.startswith('allow') for v in ops.values()) else 'À VÉRIFIER'
        print('\n[1] Paiement opérateur : '+state)
        print('[2] Confidentialité : désactiver Xiaomi Payment')
        print('[3] ADB TCP 5555 ON')
        print('[4] ADB TCP OFF (USB recommandé)')
        print('[0] Retour')
        c=input('Profil/action: ').strip()
        if c=='0':return
        if c=='1':
            print('Restauration du profil paiement opérateur…')
            results=_aa_carrier_payment_enable(dev)
            for label,rc,msg in results:
                print(('✓ ' if rc==0 else '⚠ ')+label+((' — '+msg) if msg else ''))
            enabled,ops=_aa_carrier_payment_status(dev)
            print('Xiaomi Payment : '+('activé' if enabled else 'non confirmé'))
            print('Play Store AppOps : '+', '.join(f'{k}={v}' for k,v in ops.items()))
            if enabled and all(v.startswith('allow') for v in ops.values()):
                print(GREEN+'✓ Profil opérateur restauré et vérifié.'+RESET)
            else:
                print(YELLOW+'Profil partiellement restauré : certaines permissions peuvent être refusées par cette version Android/Play Store.'+RESET)
        elif c=='2':
            rc,o,e=_aa_sh(dev,'pm disable-user --user 0 com.xiaomi.payment');print(o or e or ('OK' if rc==0 else 'Échec'))
        elif c=='3':
            rc,o,e=_aa_adb(dev,'tcpip','5555');print(o or e)
        elif c=='4':
            rc,o,e=_aa_adb(dev,'usb');print(o or e)
        input('\nEntrée...')

# ---------- Advanced menus ----------
def android_manager():
    while True:
        print_banner();print('[1] Applications / suppression / niveau de risque\n[2] Permissions + AppOps\n[3] Ports / réseau\n[4] Désactiver application\n[5] Activer application\n[6] Dump SMS / Call\n[7] Profils rapides\n[8] Shell ADB\n[9] Launcher / écran d’accueil\n[0] Retour');c=input('> ').strip()
        if c=='0':return
        actions={'1':option_delete_apk,'2':manager_permissions,'3':manager_ports,'4':lambda:manager_package_state(False),'5':lambda:manager_package_state(True),'6':option_dump_sms_call_logs,'7':manager_profiles,'8':cyber_device_shell,'9':manager_launcher}
        if c in actions:actions[c]();input('\nEntrée pour continuer...')

def show_menu():
    items=[('1','Vérifier appareil'),('2','Connecter appareil'),('3','Déconnecter'),('4','Enregistrer écran'),('5','Miroir écran'),('6','Liste applications'),('7','Capture écran'),('8','Éteindre'),('9','Installer APK'),('10','Applications / supprimer'),('11','Récupérer un fichier'),('12','Envoyer un fichier'),('13','Préparer un SMS'),('14','Exporter contacts JSON'),('15','Redémarrer'),('16','Démarrer application'),('17','Logs appareil'),('18','Wi-Fi ON/OFF'),('19','Stockage'),('20','Photo'),('21','Dépannage'),('22','Sécurité / gestion Android'),('23','Historique connexions'),('24','Langue')]
    print(GREEN+'MENU PRINCIPAL'+RESET)
    for n,label in items:print(f'[{n:>2}] {label}')
    print('[ q] Quitter\n')

def main():
    first = not _load_language()
    if first:
        print_banner()
        choose_language(first_run=True)

    print_banner()
    dependencies_check()
    update_device_logs()
    while True:
        update_device_logs()
        print_banner()
        show_menu()
        choice = input(GREEN + f"{t('select')} (1-24) / q: " + RESET).strip().lower()
        if choice == "q":
            update_device_logs()
            now = datetime.datetime.now()
            for dev, start in connected_devices.items():
                duration = now - start
                try:
                    with open("connection_log.txt", "a", encoding="utf-8") as f:
                        f.write(f"{dev} session ended at exit, connected for {duration}\n")
                except OSError:
                    pass
            print(CYAN + "Android ADB Admin - bye." + RESET)
            break
        options = {
            "1": option_check_device,
            "2": option_connect_device,
            "3": option_disconnect_device,
            "4": option_screen_recording,
            "5": option_screen_mirror,
            "6": option_show_apk_list,
            "7": option_take_screenshot,
            "8": option_power_off,
            "9": option_install_apk,
            "10": option_delete_apk,
            "11": option_pull_file,
            "12": option_push_file,
            "13": option_send_sms,
            "14": option_dump_contacts,
            "15": option_reboot_device,
            "16": option_start_app,
            "17": option_get_device_logs,
            "18": option_toggle_wifi,
            "19": option_check_storage,
            "20": option_take_photo,
            "21": option_troubleshoot,
            "22": cyber_defence_mode,
            "23": option_view_connection_history,
            "24": choose_language,
        }
        if choice in options:
            options[choice]()
        else:
            print(RED + t("invalid") + RESET)
        input("\nPress Enter / Entrée pour revenir au menu...")

def run():
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + CYAN + "Interrupted. Bye." + RESET)
        sys.exit(0)

if __name__ == "__main__":
    run()
