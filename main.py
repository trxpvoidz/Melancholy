"""
Melancholy Skin Pack Manager – main module
Copyright (c) 2026 TrxpVoidz (Ecliptix)
All rights reserved.
"""


import sys, os, json, zipfile, shutil, ctypes, time, subprocess, winreg
from pathlib import Path
from io import BytesIO
from hashlib import sha256
from base64 import b64encode
from functools import lru_cache

import requests
from PIL import Image, ImageDraw
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QMessageBox, QProgressBar, QTextEdit, QTabWidget,
    QFileDialog, QListWidget, QListWidgetItem, QComboBox, QSplashScreen,
    QSizePolicy, QLineEdit, QPlainTextEdit, QCheckBox, QFrame, QGraphicsOpacityEffect,
    QDialog, QFormLayout
)
from PySide6.QtGui import (
    QPixmap, QIcon, QDesktopServices, QPainter, QColor, QBrush,
    QLinearGradient, QPalette, QFont, QFontDatabase
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QUrl, QPropertyAnimation, QEasingCurve, QTimer,
    QEvent
)
from PySide6.QtMultimedia import QSoundEffect
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

try:
    import psutil
except ImportError:
    psutil = None

# ---------- CONSTANTS ----------
DISCORD_INVITE = "https://discord.gg/3x3M289anm"
GITHUB_URL     = "https://github.com/trxpvoidz/Melancholy"
APP_VERSION    = "1.1.7"
MARKETPLACE_URL = "https://raw.githubusercontent.com/trxpvoidz/Skin-Pack-Store-Importer/main/store.json"

http_session = requests.Session()
http_session.headers.update({'User-Agent': 'Melancholy/1.1.7'})

STORE_ITEMS_PER_PAGE = 12

DARK_STYLESHEET = """
    QMainWindow { background: transparent; }
    QWidget { color: #e0e0e0; font-size: 13px; }
    QTabWidget::pane { background: rgba(0,0,0,60); border: 1px solid #444; border-radius: 10px; }
    QTabBar { background: rgba(0,0,0,80); border-bottom: 1px solid rgba(255,255,255,30); }
    QTabBar::tab { background: transparent; color: #aaa; padding: 8px 20px; border: none; border-bottom: 2px solid transparent; font-weight: 600; }
    QTabBar::tab:selected { color: #fff; border-bottom: 2px solid #aaa; background: rgba(255,255,255,15); }
    QTabBar::tab:hover { color: #ddd; }
    QLineEdit { background: rgba(255,255,255,10); border: 1px solid #555; border-radius: 8px; padding: 8px 12px; color: #fff; }
    QLineEdit:focus { border: 1px solid #aaa; }
    QListWidget { background: transparent; border: none; outline: none; }
    QListWidget::item { background: rgba(255,255,255,8); border-radius: 6px; margin: 3px 0; padding: 10px 8px; }
    QListWidget::item:selected { background: rgba(255,255,255,20); }
    QListWidget::item:hover { background: rgba(255,255,255,15); }
    QPushButton { background: rgba(255,255,255,10); border: 1px solid #555; border-radius: 6px; padding: 7px 16px; font-weight: 600; color: #fff; }
    QPushButton:hover { background: rgba(255,255,255,20); border: 1px solid #888; }
    QPushButton:pressed { background: rgba(255,255,255,15); }
    QPushButton:disabled { color: #666; border-color: #444; }
    QProgressBar { border: 1px solid #555; border-radius: 4px; text-align: center; background: #222; }
    QProgressBar::chunk { background: #aaa; border-radius: 3px; }
    QScrollArea { background: transparent; border: none; }
    QComboBox { background: rgba(40,40,40,200); border: 1px solid #555; border-radius: 6px; padding: 6px; color: #e0e0e0; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background: #1e1e1e; selection-background-color: #444; }
    QCheckBox { spacing: 8px; }
    QCheckBox::indicator { width: 16px; height: 16px; }
    QMessageBox { background-color: #2e2e2e; color: #e0e0e0; }
    QMessageBox QLabel { color: #e0e0e0; }
    QDialog { background-color: #2e2e2e; color: #e0e0e0; }
    QTextEdit { background: rgba(255,255,255,5); color: #e0e0e0; border: 1px solid #555; border-radius: 6px; }
    QPlainTextEdit { background: rgba(255,255,255,5); color: #e0e0e0; border: 1px solid #555; border-radius: 6px; }
"""

LIGHT_STYLESHEET = """
    QMainWindow { background: transparent; }
    QWidget { color: #222; font-size: 13px; }
    QTabWidget::pane { background: rgba(255,255,255,100); border: 1px solid #aaa; border-radius: 10px; }
    QTabBar { background: rgba(255,255,255,120); border-bottom: 1px solid rgba(0,0,0,20); }
    QTabBar::tab { background: transparent; color: #444; padding: 8px 20px; border: none; border-bottom: 2px solid transparent; font-weight: 600; }
    QTabBar::tab:selected { color: #111; border-bottom: 2px solid #333; background: rgba(0,0,0,15); }
    QTabBar::tab:hover { color: #222; }
    QLineEdit { background: rgba(0,0,0,5); border: 1px solid #bbb; border-radius: 8px; padding: 8px 12px; color: #222; }
    QLineEdit:focus { border: 1px solid #555; }
    QListWidget { background: transparent; border: none; outline: none; }
    QListWidget::item { background: rgba(0,0,0,8); border-radius: 6px; margin: 3px 0; padding: 10px 8px; color: #222; }
    QListWidget::item:selected { background: rgba(0,0,0,15); }
    QListWidget::item:hover { background: rgba(0,0,0,10); }
    QPushButton { background: rgba(0,0,0,10); border: 1px solid #aaa; border-radius: 6px; padding: 7px 16px; font-weight: 600; color: #222; }
    QPushButton:hover { background: rgba(0,0,0,20); border: 1px solid #777; }
    QPushButton:pressed { background: rgba(0,0,0,15); }
    QPushButton:disabled { color: #888; border-color: #ccc; }
    QProgressBar { border: 1px solid #aaa; border-radius: 4px; text-align: center; background: #ddd; }
    QProgressBar::chunk { background: #555; border-radius: 3px; }
    QScrollArea { background: transparent; border: none; }
    QComboBox { background: rgba(230,230,230,200); border: 1px solid #bbb; border-radius: 6px; padding: 6px; color: #222; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background: #e8e8e8; selection-background-color: #ccc; }
    QCheckBox { spacing: 8px; }
    QCheckBox::indicator { width: 16px; height: 16px; }
    QMessageBox { background-color: #f0f0f0; color: #222; }
    QMessageBox QLabel { color: #222; }
    QDialog { background-color: #f0f0f0; color: #222; }
    QTextEdit { background: rgba(0,0,0,5); color: #222; border: 1px solid #aaa; border-radius: 6px; }
    QPlainTextEdit { background: rgba(0,0,0,5); color: #222; border: 1px solid #aaa; border-radius: 6px; }
"""

# ---------- RESOURCE PATH ----------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ---------- WARNING POPUP ----------
def show_warning(parent, title, message):
    msg = QMessageBox(QMessageBox.Warning, title, message, parent=parent)
    icon_path = resource_path("assets/Warning_alex.png")
    if os.path.exists(icon_path):
        msg.setIconPixmap(QPixmap(icon_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return msg.exec()

# ---------- FONT LOADING ----------
@lru_cache(maxsize=1)
def load_minecraft_font():
    font_path = resource_path("assets/Minecraft-Seven_v2.ttf")
    if not os.path.exists(font_path):
        return QFont()
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        return QFont()
    family = QFontDatabase.applicationFontFamilies(font_id)[0]
    return QFont(family, 10)

# ---------- VERSION DETECTION & PATHS ----------
def get_mc_paths(use_uwp):
    if use_uwp:
        skin = Path(os.getenv("LOCALAPPDATA")) / "Packages" / \
               "Microsoft.MinecraftUWP_8wekyb3d8bbwe" / "LocalState" / \
               "premium_cache" / "skin_packs"
        persona = Path(os.getenv("LOCALAPPDATA")) / "Packages" / \
                  "Microsoft.MinecraftUWP_8wekyb3d8bbwe" / "LocalState" / \
                  "premium_cache" / "persona"
    else:
        skin = Path(os.getenv("APPDATA")) / "Minecraft Bedrock" / \
               "premium_cache" / "skin_packs"
        persona = Path(os.getenv("APPDATA")) / "Minecraft Bedrock" / \
                  "premium_cache" / "persona"
    skin.mkdir(parents=True, exist_ok=True)
    persona.mkdir(parents=True, exist_ok=True)
    return skin, persona

def detect_minecraft_version():
    uwp_skin = Path(os.getenv("LOCALAPPDATA")) / "Packages" / \
               "Microsoft.MinecraftUWP_8wekyb3d8bbwe" / "LocalState" / \
               "premium_cache" / "skin_packs"
    if uwp_skin.is_dir():
        return True
    for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        base = Path(f"{drive}:\\XboxGames")
        if base.exists():
            for sub in base.iterdir():
                if (sub / "Minecraft.Windows.exe").exists():
                    return False
    return False

def get_account_name():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\XboxLive")
        gamertag, _ = winreg.QueryValueEx(key, "Gamertag")
        return gamertag
    except:
        pass
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\IdentityCRL\UserExtendedProperties")
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                try:
                    tag, _ = winreg.QueryValueEx(subkey, "Gamertag")
                    return tag
                except:
                    pass
                finally:
                    winreg.CloseKey(subkey)
                i += 1
            except OSError:
                break
    except:
        pass
    return os.getlogin()

SETTINGS_FILE = Path(os.getenv("APPDATA")) / "Melancholy" / "settings.json"
settings = {}
if SETTINGS_FILE.exists():
    try:
        settings = json.loads(SETTINGS_FILE.read_text())
    except:
        pass
USE_UWP = settings.get("use_uwp", None)
if USE_UWP is None:
    USE_UWP = detect_minecraft_version()
    settings["use_uwp"] = USE_UWP
    settings["sound_enabled"] = True
    settings["theme"] = "dark"
    settings["custom_background"] = ""
    settings["light_custom_background"] = ""
    settings["store_presets"] = {
        "Official Store": MARKETPLACE_URL
    }
    settings["active_store_preset"] = "Official Store"
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

SKIN_PACK_DIR, PERSONA_DIR = get_mc_paths(USE_UWP)
CACHE_DIR = Path(os.getenv("APPDATA")) / "Melancholy" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_VAULT_DIR = SKIN_PACK_DIR.parent / "legacy_vault"
LEGACY_VAULT_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = SKIN_PACK_DIR / ".skinpack_manager_state.json"
LEGACY_STATE_FILE = LEGACY_VAULT_DIR / ".legacy_vault_state.json"

if "store_presets" not in settings or not settings["store_presets"]:
    settings["store_presets"] = {"Official Store": MARKETPLACE_URL}
    settings["active_store_preset"] = "Official Store"
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

# ---------- STATE ----------
def load_state():
    state = {"known": [], "capes": []}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            if not isinstance(state.get("known"), list):
                state["known"] = list(state["known"].values())
            if not isinstance(state.get("capes"), list):
                state["capes"] = list(state["capes"].values())
        except:
            state = {"known": [], "capes": []}
    return state

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def load_legacy_state():
    state = {"injected_packs": [], "custom_packs": []}
    if LEGACY_STATE_FILE.exists():
        try:
            state = json.loads(LEGACY_STATE_FILE.read_text())
        except:
            pass
    return state

def save_legacy_state(state):
    LEGACY_STATE_FILE.write_text(json.dumps(state, indent=2))

# ---------- MANIFEST ----------
def find_manifest(folder):
    for r, _, f in os.walk(folder):
        if "manifest.json" in f:
            return Path(r) / "manifest.json"
    return None

def read_manifest(path):
    data = json.loads(path.read_text())
    return data["header"]["uuid"], data["header"].get("version", [0,0,0])

# ---------- LOCALIZATION ----------
def get_pack_display_name(pack_path: Path) -> str:
    texts_dir = pack_path / "texts"
    if texts_dir.exists():
        lang_files = list(texts_dir.glob("en_US.lang")) + [f for f in texts_dir.glob("*.lang") if f.name != "en_US.lang"]
        for lang_file in lang_files:
            try:
                with open(lang_file, 'r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('skinpack.') and '=' in line:
                            return line.split('=', 1)[1].strip()
                        if line.startswith('persona.') and '.title=' in line:
                            return line.split('=', 1)[1].strip()
            except:
                continue
    return pack_path.name

# ---------- SKIN PACK MERGER UTILITIES ----------
def merge_geometry_json(files: list[Path], output_path: Path) -> None:
    geo_dicts = []
    for f in files:
        if f.exists():
            try:
                geo_dicts.append(json.loads(f.read_text()))
            except:
                pass
    if not geo_dicts:
        return
    base = max(geo_dicts, key=lambda d: len(json.dumps(d)))
    merged = base.copy()
    for other in geo_dicts:
        if other is base:
            continue
        for key, value in other.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], list) and isinstance(value, list):
                existing_names = {g.get("name") for g in merged[key] if isinstance(g, dict) and "name" in g}
                for geom in value:
                    if isinstance(geom, dict) and geom.get("name") not in existing_names:
                        merged[key].append(geom)
    output_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))

def process_single_pack(sp_dir: Path, output_dir: Path, tex_start: int, cape_start: int):
    json_path = sp_dir / "skins.json"
    if not json_path.exists():
        return [], tex_start, cape_start
    data = json.loads(json_path.read_text())
    new_skins = []
    cape_map = {}
    for skin in data["skins"]:
        old_tex_path = sp_dir / skin["texture"]
        new_tex_name = f"s{tex_start}.png"
        if old_tex_path.exists():
            shutil.copy(old_tex_path, output_dir / new_tex_name)
        skin["texture"] = new_tex_name
        if "cape" in skin:
            orig_cape_name = skin["cape"]
            if orig_cape_name in cape_map:
                skin["cape"] = cape_map[orig_cape_name]
            else:
                new_cape_name = f"c{cape_start}.png"
                old_cape_path = sp_dir / orig_cape_name
                if old_cape_path.exists():
                    shutil.copy(old_cape_path, output_dir / new_cape_name)
                cape_map[orig_cape_name] = new_cape_name
                skin["cape"] = new_cape_name
                cape_start += 1
        skin["localization_name"] = f"s{tex_start}"
        new_skins.append(skin)
        tex_start += 1
    return new_skins, tex_start, cape_start

def merge_multiple_skinpacks(pack_dirs: list[Path], output_dir: Path, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
    log(f"Merging {len(pack_dirs)} packs into: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    tex_counter = 1
    cape_counter = 1
    all_skins = []
    geometry_files = []
    manifest_copied = False
    for pack_dir in pack_dirs:
        log(f"  -> {pack_dir}")
        skins, tex_counter, cape_counter = process_single_pack(pack_dir, output_dir, tex_counter, cape_counter)
        all_skins.extend(skins)
        geo = pack_dir / "geometry.json"
        if geo.exists():
            geometry_files.append(geo)
        if not manifest_copied:
            manifest = pack_dir / "manifest.json"
            if manifest.exists():
                shutil.copy(manifest, output_dir / "manifest.json")
                manifest_copied = True
                log(f"  Copied manifest from: {pack_dir.name}")
    merged_json = {
        "serialize_name": "merged_pack",
        "localization_name": "merged_pack",
        "skins": all_skins
    }
    (output_dir / "skins.json").write_text(json.dumps(merged_json, indent=2, ensure_ascii=False))
    if geometry_files:
        merge_geometry_json(geometry_files, output_dir / "geometry.json")
    log("Merge complete.")

# ---------- STORE PRESET DIALOG ----------
class StorePresetDialog(QDialog):
    def __init__(self, parent=None, preset_name="", preset_url=""):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Store Preset")
        self.setMinimumWidth(400)
        self.setStyleSheet(QApplication.instance().styleSheet())
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit(preset_name)
        self.url_edit = QLineEdit(preset_url)
        form.addRow("Name:", self.name_edit)
        form.addRow("URL:", self.url_edit)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Store")
        self.test_btn.clicked.connect(self.test_store)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def test_store(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Invalid", "Enter a URL.")
            return
        self.test_btn.setEnabled(False)
        try:
            r = http_session.get(url, timeout=10)
            data = r.json()
            if "packs" in data and isinstance(data["packs"], list):
                QMessageBox.information(self, "Success", f"Store is valid with {len(data['packs'])} packs.")
            else:
                QMessageBox.warning(self, "Invalid Store", "JSON missing 'packs' array.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load store:\n{e}")
        finally:
            self.test_btn.setEnabled(True)

    def get_data(self):
        return self.name_edit.text().strip(), self.url_edit.text().strip()

# ---------- BACKGROUND WIDGET ----------
class BackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = "dark"
        self.dark_custom_path = None
        self.light_custom_path = None
        self.load_custom_backgrounds()

    def load_custom_backgrounds(self):
        dark = settings.get("custom_background", "")
        self.dark_custom_path = dark if dark and os.path.exists(dark) else None
        light = settings.get("light_custom_background", "")
        self.light_custom_path = light if light and os.path.exists(light) else None

    def set_theme(self, theme):
        self.current_theme = theme
        self.update()

    def set_dark_custom_background(self, path):
        self.dark_custom_path = path
        self.update()

    def set_light_custom_background(self, path):
        self.light_custom_path = path
        self.update()

    def reset_custom_backgrounds(self):
        self.dark_custom_path = None
        self.light_custom_path = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        custom_path = None
        if self.current_theme == "light":
            custom_path = self.light_custom_path
        else:
            custom_path = self.dark_custom_path

        if custom_path and os.path.exists(custom_path):
            pix = QPixmap(custom_path)
            if not pix.isNull():
                scaled = pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter.drawPixmap((self.width()-scaled.width())//2, (self.height()-scaled.height())//2, scaled)
                if self.current_theme == "light":
                    painter.fillRect(self.rect(), QColor(255,255,255,30))
                else:
                    painter.fillRect(self.rect(), QColor(0,0,0,50))
                return

        dark_bg = Path(resource_path("assets/background.png"))
        light_bg = Path(resource_path("assets/background_light.png"))
        if self.current_theme == "light" and light_bg.exists():
            pix = QPixmap(str(light_bg))
            if not pix.isNull():
                scaled = pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter.drawPixmap((self.width()-scaled.width())//2, (self.height()-scaled.height())//2, scaled)
                painter.fillRect(self.rect(), QColor(255,255,255,30))
                return
        elif dark_bg.exists():
            pix = QPixmap(str(dark_bg))
            if not pix.isNull():
                scaled = pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter.drawPixmap((self.width()-scaled.width())//2, (self.height()-scaled.height())//2, scaled)
                painter.fillRect(self.rect(), QColor(0,0,0,50))
                return

        if self.current_theme == "light":
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(240,240,240,220))
            gradient.setColorAt(1, QColor(200,200,200,220))
            painter.fillRect(self.rect(), gradient)
            painter.fillRect(self.rect(), QColor(255,255,255,30))
        else:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(20,20,20,220))
            gradient.setColorAt(1, QColor(40,40,40,220))
            painter.fillRect(self.rect(), gradient)
            painter.fillRect(self.rect(), QColor(0,0,0,50))
        super().paintEvent(event)

# ---------- WORKERS ----------
class MergerWorker(QThread):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)
    def __init__(self, pack_dirs, output_dir):
        super().__init__()
        self.pack_dirs = pack_dirs
        self.output_dir = output_dir
    def run(self):
        try:
            def log_callback(msg): self.log.emit(msg)
            self.progress.emit(10)
            merge_multiple_skinpacks(self.pack_dirs, self.output_dir, log_callback)
            self.progress.emit(100)
            self.finished.emit(True, "Merge completed successfully!")
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            self.deleteLater()

class StoreLoader(QThread):
    finished = Signal(list)
    error = Signal(str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            r = http_session.get(self.url, timeout=15)
            packs = r.json()["packs"]
            self.finished.emit(packs)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.deleteLater()

class DownloadWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(Path)
    error = Signal(str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            self.log.emit("Starting download...")
            tmp_dir = CACHE_DIR / "downloads"
            tmp_dir.mkdir(exist_ok=True)
            zip_path = tmp_dir / "pack.zip"
            r = http_session.get(self.url, stream=True, timeout=30)
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            done = 0
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if not chunk: continue
                    f.write(chunk)
                    done += len(chunk)
                    if total: self.progress.emit(int(done / total * 100))
            self.progress.emit(100)
            self.log.emit("Download complete")
            self.finished.emit(zip_path)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.deleteLater()

class ThumbnailLoader(QThread):
    finished = Signal(QPixmap)
    error = Signal()
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            r = http_session.get(self.url, timeout=10)
            img = Image.open(BytesIO(r.content))
            img.thumbnail((200, 200))
            buf = BytesIO()
            img.save(buf, "PNG")
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            self.finished.emit(pix)
        except:
            self.error.emit()
        finally:
            self.deleteLater()

class IconGenerator(QThread):
    icon_ready = Signal(str, object)   # uuid, QPixmap or None
    all_done = Signal()

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks  # list of (uuid, pack_path)

    def run(self):
        for uuid, pack_path in self.tasks:
            try:
                pix = get_pack_head_icon(pack_path)
            except Exception as e:
                pix = None
            self.icon_ready.emit(uuid, pix)
        self.all_done.emit()

# ---------- CUSTOM WIDGETS ----------
class SoundButton(QPushButton):
    def __init__(self, text, hover_sound, click_sound, parent=None):
        super().__init__(text, parent)
        self.hover_sound = hover_sound
        self.click_sound = click_sound
    def enterEvent(self, event):
        if self.hover_sound and self.hover_sound.isLoaded() and self.window().sound_enabled:
            self.hover_sound.play()
        super().enterEvent(event)
    def mousePressEvent(self, event):
        if self.click_sound and self.click_sound.isLoaded() and self.window().sound_enabled:
            self.click_sound.play()
        super().mousePressEvent(event)

class DragDropWidget(QLabel):
    instances = []
    def __init__(self, text, file_types=None, folder_mode=False, callback=None, parent=None,
                 multi_folder=False, allow_zip=False):
        super().__init__(text, parent)
        self.callback = callback
        self.file_types = file_types or []
        self.folder_mode = folder_mode
        self.multi_folder = multi_folder
        self.allow_zip = allow_zip
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setSizePolicy(policy)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 80))
        self.setPalette(palette)
        self.setStyleSheet("QLabel { border: 2px dashed rgba(255,255,255,80); border-radius: 10px; color: #ccc; }")
        DragDropWidget.instances.append(self)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet("QLabel { border: 2px solid rgba(255,255,255,200); background: rgba(255,255,255,10); border-radius: 10px; color: #fff; }")
            event.acceptProposedAction()
    def dragLeaveEvent(self, event):
        self.setStyleSheet("QLabel { border: 2px dashed rgba(255,255,255,80); border-radius: 10px; color: #ccc; }")
    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        if not urls:
            return
        if self.multi_folder and self.folder_mode:
            paths = []
            for url in urls:
                path = url.toLocalFile()
                if os.path.isdir(path):
                    paths.append(path)
            if paths and self.callback:
                self.callback(paths)
            event.acceptProposedAction()
            return
        path = urls[0].toLocalFile()
        if self.folder_mode:
            if os.path.isdir(path):
                if self.callback:
                    self.callback(path)
                    event.acceptProposedAction()
            elif self.allow_zip and os.path.isfile(path) and (path.lower().endswith('.zip') or os.path.splitext(path)[1] == ''):
                if self.callback:
                    self.callback(path)
                    event.acceptProposedAction()
        else:
            if os.path.isfile(path):
                if self.file_types:
                    if any(path.lower().endswith(ext) for ext in self.file_types):
                        if self.callback:
                            self.callback(path)
                            event.acceptProposedAction()
                else:
                    if self.callback:
                        self.callback(path)
                        event.acceptProposedAction()
    def mousePressEvent(self, event):
        if self.folder_mode and self.multi_folder:
            paths = QFileDialog.getExistingDirectory(self, "Select First Folder")
            if paths:
                if self.callback:
                    self.callback([paths])
        elif self.folder_mode:
            if self.allow_zip:
                path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;ZIP Files (*.zip)")
                if path:
                    if self.callback:
                        self.callback(path)
            else:
                path = QFileDialog.getExistingDirectory(self, "Select Folder")
                if path and self.callback:
                    self.callback(path)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;ZIP Files (*.zip)")
            if path and self.callback:
                self.callback(path)

class StoreCard(QWidget):
    instances = []
    _thumbnail_cache = {}
    def __init__(self, pack, state, install_cb, uninstall_cb, hover_sound, click_sound):
        super().__init__()
        self.pack = pack
        self.install_cb = install_cb
        self.uninstall_cb = uninstall_cb
        self.setFixedWidth(210)
        self.setMinimumHeight(280)
        self.setStyleSheet("QWidget { background: rgba(255,255,255,15); border: 1px solid rgba(255,255,255,40); border-radius: 12px; }")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(8)
        self.thumb = QLabel("Loading...")
        self.thumb.setFixedSize(180, 180)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet("background: rgba(0,0,0,80); border-radius: 8px; color: #aaa; border: none;")
        layout.addWidget(self.thumb, alignment=Qt.AlignCenter)
        self.name_label = QLabel(pack.get("name", "Unnamed"))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: white; border: none;")
        layout.addWidget(self.name_label)
        self.badge = QLabel()
        self.badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.badge)
        btns = QHBoxLayout()
        self.install_btn = SoundButton("Install", hover_sound, click_sound)
        self.install_btn.setStyleSheet("QPushButton { background: rgba(255,255,255,40); border: 1px solid rgba(255,255,255,100); border-radius: 6px; color: white; } QPushButton:hover { background: rgba(255,255,255,100); }")
        self.install_btn.clicked.connect(lambda: install_cb(pack))
        btns.addWidget(self.install_btn)
        self.remove_btn = None
        if any(info.get("store_name") == pack.get("name") for info in state.get("known", [])):
            self.remove_btn = SoundButton("Remove", hover_sound, click_sound)
            self.remove_btn.setStyleSheet("QPushButton { background: rgba(255,255,255,20); border: 1px solid rgba(255,255,255,80); border-radius: 6px; color: white; } QPushButton:hover { background: rgba(255,255,255,60); }")
            self.remove_btn.clicked.connect(lambda: uninstall_cb(pack))
            btns.addWidget(self.remove_btn)
        layout.addLayout(btns)
        self.update_badge(state)
        self.load_thumb(pack.get("thumbnail"))
        StoreCard.instances.append(self)
        self.destroyed.connect(lambda obj: StoreCard.instances.remove(obj) if obj in StoreCard.instances else None)
        self._destroyed = False
        self.destroyed.connect(lambda: setattr(self, '_destroyed', True))

    def update_badge(self, state):
        if any(info.get("store_name") == self.pack.get("name") for info in state.get("known", [])):
            self.badge.setText("Installed")
            self.badge.setStyleSheet("color: white; font-size: 11px;")
        else:
            self.badge.clear()
    def load_thumb(self, url):
        if not url:
            return
        if url in StoreCard._thumbnail_cache:
            self.thumb.setPixmap(StoreCard._thumbnail_cache[url])
            return
        self.loader = ThumbnailLoader(url)
        self.loader.finished.connect(lambda pix, u=url: self._on_thumb_loaded(pix, u))
        self.loader.error.connect(lambda: self.thumb.setText("No image"))
        self.loader.start()

    def _on_thumb_loaded(self, pix, url):
        if getattr(self, '_destroyed', False):
            return
        try:
            self.thumb.setPixmap(pix)
            StoreCard._thumbnail_cache[url] = pix
        except RuntimeError:
            pass

class LoadingScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        bg_paths = [Path(resource_path("assets/background.png")), Path(os.getcwd()) / "assets" / "background.png"]
        bg_loaded = False
        for path in bg_paths:
            if path.exists():
                bg = QPixmap(str(path))
                if not bg.isNull():
                    scaled_bg = bg.scaled(600, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    painter.drawPixmap(0, 0, scaled_bg)
                    bg_loaded = True
                break
        if not bg_loaded:
            gradient = QLinearGradient(0, 0, 600, 400)
            gradient.setColorAt(0, QColor(0, 0, 0, 240))
            gradient.setColorAt(1, QColor(50, 50, 50, 240))
            painter.fillRect(pixmap.rect(), gradient)
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 100))
        painter.setPen(QColor(255, 255, 255, 200))
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Melancholy\n\nLoading...")
        painter.setPen(QColor(255, 255, 255, 100))
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 100, 0, 0), Qt.AlignCenter, "Skin Pack Manager")
        painter.end()
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    def show_message(self, msg):
        self.showMessage(msg, Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255, 200))

# ---------- HOME TAB ----------
class HomeTab(QWidget):
    def __init__(self, parent, hover_sound, click_sound):
        super().__init__(parent)
        self.parent = parent
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self.action_cards = []
        self.help_visible = False
        self.help_widget = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        account = get_account_name()
        self.welcome_label = QLabel(f"Welcome, {account}!")
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.welcome_label)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(15)
        self.mc_version_label = self._create_stat_pill("Minecraft", "GDK" if not USE_UWP else "UWP")
        self.packs_count_label = self._create_stat_pill("Skin Packs", str(len(self.parent.state.get("known", []))))
        self.persona_count_label = self._create_stat_pill("Persona Items", str(len(self.parent.state.get("capes", []))))
        summary_row.addStretch()
        summary_row.addWidget(self.mc_version_label)
        summary_row.addWidget(self.packs_count_label)
        summary_row.addWidget(self.persona_count_label)
        summary_row.addStretch()
        main_layout.addLayout(summary_row)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignCenter)

        actions = [
            ("store.png", "Store", 1),
            ("installed.png", "Installed", 2),
            ("porter.png", "Porter", 3),
            ("merger.png", "Merger", 5),
            ("persona.png", "Persona", 4),
            ("settings.png", "Settings", 6)
        ]

        for icon_file, label, tab_idx in actions:
            icon_path = resource_path(f"assets/icons/{icon_file}")
            card = self._create_action_card(icon_path, label, lambda idx=tab_idx: self.parent.tabs.setCurrentIndex(idx))
            cards_layout.addWidget(card)
            self.action_cards.append(card)

        main_layout.addLayout(cards_layout)

        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(30, 30)
        self.help_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,15);
                border: 1px solid rgba(255,255,255,40);
                border-radius: 15px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,30);
            }
        """)
        self.help_btn.clicked.connect(self.toggle_help)
        help_layout = QHBoxLayout()
        help_layout.addStretch()
        help_layout.addWidget(self.help_btn)
        main_layout.addLayout(help_layout)

        self.help_widget = QFrame()
        self.help_widget.setStyleSheet("QFrame { background: rgba(255,255,255,10); border-radius: 8px; }")
        help_vbox = QVBoxLayout(self.help_widget)
        self.help_text = QLabel(
            "How to use each tab:\n"
            "Home - Overview and quick navigation\n"
            "Store - Download official skin packs\n"
            "Installed - Manage your skin packs (drop folders/ZIPs)\n"
            "Porter - Encrypt and import custom packs\n"
            "Persona - Manage capes and persona items\n"
            "Merger - Combine multiple packs into one\n"
            "Settings - Change theme, sound, background"
        )
        self.help_text.setWordWrap(True)
        self.help_text.setStyleSheet("color: #ccc; font-size: 12px; background: transparent;")
        help_vbox.addWidget(self.help_text)
        self.help_widget.setVisible(False)
        main_layout.addWidget(self.help_widget)

        main_layout.addStretch()
        QTimer.singleShot(100, self.start_entrance_animation)

    def _create_stat_pill(self, title, value):
        pill = QFrame()
        pill.setStyleSheet("QFrame { background: rgba(255,255,255,15); border-radius: 10px; padding: 5px; }")
        layout = QVBoxLayout(pill)
        layout.setContentsMargins(10, 5, 10, 5)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #aaa; font-size: 11px; background: transparent;")
        title_lbl.setAlignment(Qt.AlignCenter)
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent;")
        value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        if "Minecraft" in title:
            self.mc_version_value_lbl = value_lbl
        elif "Skin Packs" in title:
            self.packs_count_value_lbl = value_lbl
        elif "Persona" in title:
            self.persona_count_value_lbl = value_lbl
        return pill

    def _create_action_card(self, icon_path, label, callback):
        card = QFrame()
        card.setFixedSize(150, 150)
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,12);
                border: 1px solid rgba(255,255,255,25);
                border-radius: 12px;
            }
            QFrame:hover {
                background: rgba(255,255,255,25);
                border: 1px solid rgba(255,255,255,80);
            }
        """)
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.0)
        card.setGraphicsEffect(opacity_effect)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        pix = QPixmap(icon_path)
        if not pix.isNull():
            icon_lbl.setPixmap(pix.scaled(96, 96, Qt.KeepAspectRatio, Qt.FastTransformation))
        else:
            icon_lbl.setText("[icon]")
            icon_lbl.setStyleSheet("color: #aaa; font-size: 12px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(label)
        text_lbl.setAlignment(Qt.AlignCenter)
        text_lbl.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        layout.addWidget(text_lbl)

        card.mousePressEvent = lambda ev: callback()
        return card

    def start_entrance_animation(self):
        for i, card in enumerate(self.action_cards):
            effect = card.graphicsEffect()
            if effect is None:
                continue
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(400)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.setDelay(i * 100)
            animation.start(QPropertyAnimation.DeleteWhenStopped)

    def toggle_help(self):
        self.help_visible = not self.help_visible
        self.help_widget.setVisible(self.help_visible)

    def update_counts(self):
        if hasattr(self, 'mc_version_value_lbl'):
            self.mc_version_value_lbl.setText("UWP" if USE_UWP else "GDK")
        if hasattr(self, 'packs_count_value_lbl'):
            self.packs_count_value_lbl.setText(str(len(self.parent.state.get("known", []))))
        if hasattr(self, 'persona_count_value_lbl'):
            self.persona_count_value_lbl.setText(str(len(self.parent.state.get("capes", []))))

    def apply_theme(self, theme):
        if theme == "light":
            text_color = "#222"
            dim_color = "#555"
            card_bg = "rgba(0,0,0,10)"
            card_bg_hover = "rgba(0,0,0,20)"
            card_border = "rgba(0,0,0,25)"
            card_border_hover = "rgba(0,0,0,80)"
            help_btn_bg = "rgba(0,0,0,10)"
            help_btn_hover = "rgba(0,0,0,20)"
            help_frame_style = "QFrame { background: rgba(0,0,0,5); border-radius: 8px; }"
            pill_style = "QFrame { background: rgba(0,0,0,8); border-radius: 10px; padding: 5px; }"
        else:
            text_color = "#e0e0e0"
            dim_color = "#aaa"
            card_bg = "rgba(255,255,255,12)"
            card_bg_hover = "rgba(255,255,255,25)"
            card_border = "rgba(255,255,255,25)"
            card_border_hover = "rgba(255,255,255,80)"
            help_btn_bg = "rgba(255,255,255,15)"
            help_btn_hover = "rgba(255,255,255,30)"
            help_frame_style = "QFrame { background: rgba(255,255,255,10); border-radius: 8px; }"
            pill_style = "QFrame { background: rgba(255,255,255,15); border-radius: 10px; padding: 5px; }"

        self.welcome_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {text_color};")

        for pill, title_text in [(self.mc_version_label, "Minecraft"),
                                 (self.packs_count_label, "Skin Packs"),
                                 (self.persona_count_label, "Persona Items")]:
            pill.setStyleSheet(pill_style)
            layout = pill.layout()
            if layout and layout.count() >= 2:
                title_widget = layout.itemAt(0).widget()
                val_widget = layout.itemAt(1).widget()
                if isinstance(title_widget, QLabel):
                    title_widget.setStyleSheet(f"color: {dim_color}; font-size: 11px; background: transparent;")
                if isinstance(val_widget, QLabel):
                    val_widget.setStyleSheet(f"color: {text_color}; font-size: 16px; font-weight: bold; background: transparent;")

        for card in self.action_cards:
            card.setStyleSheet(f"""
                QFrame {{
                    background: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    background: {card_bg_hover};
                    border: 1px solid {card_border_hover};
                }}
            """)
            layout = card.layout()
            if layout and layout.count() >= 2:
                text_lbl = layout.itemAt(1).widget()
                if isinstance(text_lbl, QLabel):
                    text_lbl.setStyleSheet(f"color: {text_color}; font-weight: bold; background: transparent;")

        self.help_btn.setStyleSheet(f"""
            QPushButton {{
                background: {help_btn_bg};
                border: 1px solid rgba(255,255,255,40);
                border-radius: 15px;
                color: {text_color};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {help_btn_hover};
            }}
        """)

        self.help_widget.setStyleSheet(help_frame_style)
        self.help_text.setStyleSheet(f"color: {dim_color}; font-size: 12px; background: transparent;")

# ---------- SETTINGS TAB ----------
class SettingsTab(QWidget):
    def __init__(self, parent, hover_sound, click_sound):
        super().__init__(parent)
        self.parent = parent
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self.plugin_checkboxes = {}
        self.setup_ui()

    def open_plugins_folder(self):          # ← add this
        from plugin_engine import PLUGINS_DIR
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(PLUGINS_DIR)))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        current_theme = settings.get("theme", "dark")
        self.theme_combo.setCurrentIndex(0 if current_theme == "dark" else 1)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # Sound
        sound_layout = QHBoxLayout()
        sound_layout.addStretch()
        sound_label = QLabel("Sound:")
        self.sound_check = QCheckBox("Enable sounds")
        self.sound_check.setChecked(settings.get("sound_enabled", True))
        self.sound_check.toggled.connect(self.toggle_sound)
        sound_layout.addWidget(sound_label)
        sound_layout.addWidget(self.sound_check)
        sound_layout.addStretch()
        layout.addLayout(sound_layout)

        # Icons
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_label = QLabel("Icons:")
        self.icon_check = QCheckBox("Show pack icons")
        self.icon_check.setChecked(settings.get("show_icons", True))
        self.icon_check.toggled.connect(self.toggle_icons)
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_check)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)

        # Plugin Manager
        plugin_label = QLabel("Plugin Manager")
        plugin_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        plugin_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(plugin_label)
        self.open_plugins_btn = SoundButton("Open Plugins Folder", self.hover_sound, self.click_sound)
        self.open_plugins_btn.clicked.connect(self.open_plugins_folder)
        # put it somewhere in the layout, e.g. near the Restart App button

        # Scrollable list of plugin checkboxes
        self.plugin_scroll = QScrollArea()
        self.plugin_scroll.setWidgetResizable(True)
        self.plugin_scroll.setMaximumHeight(200)
        self.plugin_widget = QWidget()
        self.plugin_layout = QVBoxLayout(self.plugin_widget)
        self.plugin_scroll.setWidget(self.plugin_widget)
        layout.addWidget(self.plugin_scroll)

        # Restart button
        restart_layout = QHBoxLayout()
        self.restart_btn = SoundButton("Restart App", self.hover_sound, self.click_sound)
        self.restart_btn.clicked.connect(self.restart_app)
        restart_layout.addWidget(self.restart_btn)
        restart_layout.addStretch()
        layout.addLayout(restart_layout)

        self.refresh_plugin_list()

        # Background buttons
        bg_layout = QHBoxLayout()
        bg_layout.addStretch()
        change_bg_btn = SoundButton("Change Dark BG", self.hover_sound, self.click_sound)
        change_bg_btn.clicked.connect(self.change_dark_background)
        bg_layout.addWidget(change_bg_btn)

        change_light_bg_btn = SoundButton("Change Light BG", self.hover_sound, self.click_sound)
        change_light_bg_btn.clicked.connect(self.change_light_background)
        bg_layout.addWidget(change_light_bg_btn)

        reset_bg_btn = SoundButton("Reset Both BGs", self.hover_sound, self.click_sound)
        reset_bg_btn.clicked.connect(self.reset_backgrounds)
        bg_layout.addWidget(reset_bg_btn)
        bg_layout.addStretch()
        layout.addLayout(bg_layout)

        layout.addStretch()

    # --- Existing methods (change_theme, toggle_sound, background stuff) unchanged ---
    def change_theme(self, index):
        theme = "dark" if index == 0 else "light"
        self.parent.apply_theme(theme)
        settings["theme"] = theme
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

    def toggle_sound(self, checked: bool):
        self.parent.sound_enabled = checked
        self.parent.update_sound_button()
        settings["sound_enabled"] = checked
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

    def toggle_icons(self, checked: bool):
        self.parent.show_icons = checked
        settings["show_icons"] = checked
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        self.parent.refresh_installed()

    # --- Plugin manager methods ---
    def refresh_plugin_list(self):
        # Clear old checkboxes
        for cb in self.plugin_checkboxes.values():
            self.plugin_layout.removeWidget(cb)
            cb.deleteLater()
        self.plugin_checkboxes.clear()

        # Populate from plugin_engine
        from plugin_engine import get_available_plugins, is_plugin_enabled

        plugins = get_available_plugins()
        if not plugins:
            no_plugins = QLabel("No plugins found in 'plugins/' folder.")
            no_plugins.setStyleSheet("color: #aaa; font-size: 12px;")
            no_plugins.setAlignment(Qt.AlignCenter)
            self.plugin_layout.addWidget(no_plugins)
            return

        for name in sorted(plugins.keys()):
            cb = QCheckBox(name)
            cb.setChecked(is_plugin_enabled(name))
            cb.toggled.connect(lambda checked, n=name: self.plugin_toggled(n, checked))
            self.plugin_layout.addWidget(cb)
            self.plugin_checkboxes[name] = cb

        self.plugin_layout.addStretch()

    def plugin_toggled(self, name, enabled):
        from plugin_engine import set_plugin_enabled_state
        set_plugin_enabled_state(name, enabled)

        msg = QMessageBox(self)
        msg.setWindowTitle("Plugin Change")
        msg.setText(f"Changes to plugin '{name}' will take effect after a restart.")
        msg.setInformativeText("Do you want to restart now?")
        restart_btn = msg.addButton("Restart Now", QMessageBox.AcceptRole)
        later_btn = msg.addButton("Later", QMessageBox.RejectRole)
        msg.exec()

        if msg.clickedButton() == restart_btn:
            self.restart_app()

    def rescan_plugins(self):
        from plugin_engine import reload_all_plugins
        reload_all_plugins(self.parent)
        # Refresh the checkbox list in case new plugins appeared
        self.refresh_plugin_list()

    def restart_app(self):
        import sys, os
        if getattr(sys, 'frozen', False):
            # When frozen, sys.executable is the path to the .exe
            os.startfile(sys.executable)
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        QApplication.quit()

    # --- Background methods (unchanged) ---
    def change_dark_background(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Dark Background Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            self.parent.background.set_dark_custom_background(file_path)
            settings["custom_background"] = file_path
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

    def change_light_background(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Light Background Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            self.parent.background.set_light_custom_background(file_path)
            settings["light_custom_background"] = file_path
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

    def reset_backgrounds(self):
        self.parent.background.reset_custom_backgrounds()
        settings["custom_background"] = ""
        settings["light_custom_background"] = ""
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

# ---------------- PORTER / ENCRYPTION FUNCTIONS ----------------
fileSkip = {'manifest.json', 'pack_icon.png'}
fileSkipForce = {'contents.json', 'signatures.json'}
fileSkipFull = fileSkip | fileSkipForce
key = None
encryptedVariable = None
inputPathSkinpack = None
FIXED_KEY = 's5s5ejuDru4uchuF2drUFuthaspAbepE'


MANIFEST_OPTIONS = {
    "1st Birthday": '{"header":{"version":[1,0,5],"description":"pack.description","name":"pack.name","uuid":"202539ce-e6c5-40b5-a4a1-4296277d18f6"},"modules":[{"version":[1,0,5],"type":"skin_pack","uuid":"ef6f8811-933b-4673-b285-c02cf583e56d"}],"format_version":1}',
    "1st Animal Friends": '{"format_version":1,"header":{"name":"1st Animal Friends","uuid":"9a9fa850-0b5e-11ee-9a0f-a795af90f04f","version":[1,0,3]},"modules":[{"type":"skin_pack","uuid":"a162eb70-0b5e-11ee-86cb-9d9dd4413780","version":[1,0,3]}]}',
    "Beap Borp HD": '{"header":{"name":"BeepBorpHD","version":[1,0,4],"uuid":"18215a23-e943-4004-b799-48fdcc926799"},"modules":[{"version":[1,0,4],"type":"skin_pack","uuid":"7eb2682d-9532-4db6-aa7e-b4512e347f2e"}],"format_version":1}',
    "Blockheads": '{"header": {"name": "Blockheads","version": [1,0,0],"uuid": "8b8362a3-cd8c-4f48-9a49-b494659513b6"},"modules": [{"version": [1,0,0],"type": "skin_pack","uuid": "c47ad348-0f17-438f-ae11-6c001445a947"}],"format_version": 1}',
    "Crafty Costumes": '{"format_version":1,"header":{"name":"CraftyCostumes","uuid":"c35ad990-3dc5-4179-bfe9-6f323d94f0b2","version":[1,0,11]},"modules":[{"type":"skin_pack","uuid":"a568d136-49ec-4287-bbe1-29110643a489","version":[1,0,11]}]}',
    "Creepy Creatures": '{"header": {"name": "Creepy Creatures","version": [1,0,1],"uuid": "dd44b7d6-2c05-48a2-bfdf-f78596b59f44"},"modules": [{"version": [1,0,1],"type": "skin_pack","uuid": "f84c0b4a-7b0b-4ed3-9125-dffa2815809f"}],"format_version": 1}',
    "Cute Kitty HD": '{"header":{"name":"CuteKittyHD","version":[1,0,10],"uuid":"7124cf9d-5d0e-4865-9656-03c1f04039c3"},"modules":[{"version":[1,0,10],"type":"skin_pack","uuid":"e9c920a2-fbb1-430a-a951-f240f48c5abc"}],"format_version":1}',
    "Cyborg Skin Pack": '{"header": {"description": "Cyborg Skin Pack","name": "Cyborg Skin Pack","version": [1,0,4],"uuid": "deb3b920-be8a-4b62-b8b1-5c9c7a4272f9"},"modules": [{"version": [1,0,4],"type": "skin_pack","uuid": "94d873ba-6fe7-4374-b5a4-cb36a285fd49"}],"format_version": 1}',
    "Dress Code": '{"header": {"name": "Dress Code","version": [1,0,6],"uuid": "f47107de-385d-4e15-8a5a-cdd40a1df33d"},"modules": [{"version": [1,0,6],"type": "skin_pack","uuid": "683735a6-44f6-40e2-97b0-5039f5251353"}],"format_version": 1}',
    "Builders & Biomes": '{"format_version":1,"header":{"name":"BuildersBiomes","uuid":"05ead86c-572c-40c8-8cb0-8733a7894185","version":[1,0,4]},"modules":[{"type":"skin_pack","uuid":"9d6e6755-42dc-4ac9-8cc8-374a4ca9a9ab","version":[1,0,4]}]}',
    "Haipu": '{"format_version":1,"header":{"name":"Haipu","uuid":"f46a707a-36c7-45d0-becf-88c5e2f4257d","version":[1,0,3]},"modules":[{"type":"skin_pack","uuid":"2791e9a8-e380-4e14-8f9c-6d3c3aa3476b","version":[1,0,3]}]}',
    "Heartfelt": '{"header": {"name": "Heartfelt","version": [1, 0, 0],"uuid": "72fe6a92-121d-40a7-bb47-d08a41579d32"},"modules": [{"version": [1, 0, 0],"type": "skin_pack","uuid": "31a2afa5-b024-444a-822b-46d4bd1dd2c6"}],"format_version": 1}',
    "Lunar New Year of The Ox": '{"header":{"name":"Lunar_New_Year_of_The_Ox","version":[1,0,12],"uuid":"96e8daad-3d7a-4818-bc25-2c815fb3bbc2"},"modules":[{"version":[1,0,12],"type":"skin_pack","uuid":"bed5e4b3-b108-4448-b608-0908e7905db5"}],"format_version":1}',
    "Minecraft x Uniqlo Skins Vol 2": '{"format_version":1,"header":{"name":"pack.name","uuid":"18219eb4-d96f-4b8b-999a-6cbd1b65c58d","version":[1,0,5]},"modules":[{"type":"skin_pack","uuid":"77260103-f950-4280-9a17-89da92391898","version":[1,0,5]}],"metadata":{"authors":["Mike Gaboury"]}}',
    "Norse Mythology Bonus Skins": '{"format_version":1,"header":{"name":"pack.name","uuid":"6dd86351-0191-4a3e-85cf-2a81647b830c","version":[1,0,5]},"modules":[{"type":"skin_pack","uuid":"a29a25d5-4b28-4ddb-a57d-ce272cf5fc39","version":[1,0,5]}]}',
    "Notice Me Senpai HD": '{"header":{"name":"NoticeMeHD","version":[1,0,2],"uuid":"4bf4b0f7-dec8-4cde-b6f4-0222972d0aac"},"modules":[{"version":[1,0,2],"type":"skin_pack","uuid":"39e6f01a-da8a-4106-b66f-a643fbaee1c9"}],"format_version":1}',
    "Onesie Skeletons": '{"header":{"name":"OnesieSkeletons","version":[1,0,3],"uuid":"87e7495b-a219-4a65-837c-654ee97ad8f6"},"modules":[{"version":[1,0,3],"type":"skin_pack","uuid":"d164c220-a005-466d-ac87-d096e08337d7"}],"format_version":1}',
    "Popya": '{"format_version":1,"header":{"name":"Popya","uuid":"e3f6e616-ca3c-492c-bbbf-4d41b859b8cd","version":[1,0,5]},"modules":[{"type":"skin_pack","uuid":"52e87833-4d00-47bb-abb1-62731227a037","version":[1,0,5]}]}',
    "Rockin' Holiday": '{"format_version":1,"header":{"name":"RockinHoliday","uuid":"0887d1fd-a752-47d9-a119-b47e6a5fac67","version":[1,0,7]},"modules":[{"type":"skin_pack","uuid":"d8c125af-9c41-4e0c-998f-52961a0c2a0d","version":[1,0,7]}]}',
    "Safari Adventurers": '{"header": {"name": "Safari Adventurers Skin Pack","version": [1,0,1],"uuid": "219655ca-39b4-4ec4-b04b-281a6ac1e3e5"},"modules": [{"version": [1,0,1],"type": "skin_pack","uuid": "3ad7c0f9-13a0-4e19-861a-04f336eec2a8"}],"format_version": 1}',
    "Sailor Uniform": '{"format_version":1,"header":{"name":"Sailor Uniform","uuid":"00e87c90-b734-4021-88b3-7cca436747cc","version":[1,0,10]},"modules":[{"type":"skin_pack","uuid":"73b4293b-c91b-4d9b-9f12-d00d9455d2b9","version":[1,0,10]}]}',
    "Stay Warm HD": '{"header":{"name":"StayWarmHD","version":[1,0,3],"uuid":"85a2ede9-cce0-42e4-96af-c9fd1e913b37"},"modules":[{"version":[1,0,3],"type":"skin_pack","uuid":"b0afc709-4c72-4578-953b-146f3270bcb7"}],"format_version":1}',
    "Summer Beach Party": '{"format_version": 1,"metadata": {"authors": ["GoE-Craft","All Rights Reserved."]},"header": {"name": "SummerBeachPartySkinPack","uuid": "6fef41b8-4000-4afc-ae5d-03b08755a8e4","version": [1,0,0]},"modules": [{"type": "skin_pack","uuid": "683da9cd-a504-4001-b0bf-400991218560","version": [1,0,0]}]}',
    "Summer Gift": '{"header":{"name":"pack.SummerGift","version":[1,0,1],"uuid":"aed5c500-83e9-44f6-9213-618a9dd32e3e"},"modules":[{"version":[1,0,1],"type":"skin_pack","uuid":"c9fe656a-9cad-48a9-97db-860e1f90021b"}],"format_version":1}',
    "Superman": '{"format_version":1,"header":{"name":"pack.name","version":[1,0,6],"uuid":"50a5f49f-86b3-3b7e-3060-d40000f59dcb"},"modules":[{"version":[1,0,6],"type":"skin_pack","uuid":"0e837629-6794-2d56-76ef-174bb282f3ca"}]}',
    "Timless Toys": '{"format_version":1,"header":{"name":"Timeless Toys Skins","uuid":"727df6bb-5392-4b92-b262-54545731116a","version":[1,0,3]},"modules":[{"type":"skin_pack","uuid":"cbc1286c-aa81-427a-9360-0a9c4042da0a","version":[1,0,3]}]}',
    "Vibrant Adventurers Volume 1": '{"header":{"name":"VibrantAdventurersV1","version":[1,0,1],"uuid":"5cfc95c0-7490-4bdd-a5f9-d1164decbb1b"},"modules":[{"version":[1,0,0],"type":"skin_pack","uuid":"d2dbc6e4-956e-4c7d-83b1-70437a168f3a"}],"format_version":1}',
    "Vibrant Adventurers Volume 2": '{"header":{"name":"VibrantAdventurersV2","version":[1,0,3],"uuid":"b3b5a06a-7dc6-4ec6-a3cc-89c46f9a91e2"},"modules":[{"version":[1,0,0],"type":"skin_pack","uuid":"7e4831cb-9912-4cd3-83a0-76ffee9104d5"}],"format_version":1}',
    "Vibrant Adventurers Volume 3": '{"header":{"name":"VibrantAdventurersV3","version":[1,0,1],"uuid":"ba692d28-b4ca-40ce-9e0e-7f7960baee13"},"modules":[{"version":[1,0,0],"type":"skin_pack","uuid":"96456913-21cc-4b12-99bb-a6f937c9bec1"}],"format_version":1}',
    "Wild West Adventurers": '{"header": {"name": "Cowboys and Indians","version": [1,0,4],"uuid": "222b52e7-d292-4765-838c-66d8cbb4719d"},"modules": [{"version": [1,0,4],"type": "skin_pack","uuid": "942e9425-18c8-4246-9a90-0af9804e3d40"}],"format_version": 1}',
    "Winter Whimsy": '{"header": {"name": "WinterWhimsy","version": [1, 0, 0],"uuid": "163b24c0-5989-4457-a68f-fbbb6099c842"},"modules": [{"version": [1, 0, 0],"type": "skin_pack","uuid": "3b8b7a48-b62a-44a7-b1ff-d93098c31cc6"}],"format_version": 1}',
    "Young Fashion": '{"header": {"name": "Young Fashion","version": [1,0,1],"uuid": "7fdde03a-8dce-4b76-a969-6484d79358fd"},"modules": [{"version": [1,0,1],"type": "skin_pack","uuid": "944a69ab-c924-4155-ad7b-a4f13742fb86"}],"format_version": 1}',
    "Young Gru": '{"header":{"name":"Young Gru","version":[1,0,8],"uuid":"670f5c25-c3a2-4a87-b48c-313b8ee35578"},"modules":[{"version":[1,0,8],"type":"skin_pack","uuid":"e84a3684-808a-42e5-8a68-610c3cb8adb8"}],"format_version":1}'
}


def generateKey(pathOrByte, isPath, variableOrFile):
    global key, encryptedVariable
    key = FIXED_KEY
    cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CFB8(key[:16].encode('utf-8')))
    encryptor = cipher.encryptor()
    if isPath:
        with open(pathOrByte, 'rb') as file:
            data = file.read()
        with open(pathOrByte, 'wb') as file:
            file.write(encryptor.update(data) + encryptor.finalize())
    elif variableOrFile is True:
        encryptedVariable = encryptor.update(pathOrByte) + encryptor.finalize()
    else:
        with open(variableOrFile, 'wb') as file:
            file.write(encryptor.update(pathOrByte) + encryptor.finalize())

def setup_porter(inputPath, manifestChoice):
    global inputPathSkinpack
    inputPathSkinpack = os.path.join(inputPath, '')
    manifest_path = os.path.join(inputPathSkinpack, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(MANIFEST_OPTIONS[manifestChoice])

def tool_porter(inputPath):
    global key, inputPathSkinpack, encryptedVariable
    fileJSONContents = {"version": 1, "content": []}
    for path, dirs, files in os.walk(inputPathSkinpack):
        if os.path.basename(path).lower() == 'texts': continue
        for file in files:
            pathFile = os.path.join(path, file)
            doEncrypt, doNotAdd = True, False
            for pathFileSkip in fileSkipFull:
                if pathFile.endswith(pathFileSkip):
                    doEncrypt = False
                    if pathFileSkip in fileSkipForce:
                        doNotAdd = True
                    break
            relativePath = pathFile.replace(inputPathSkinpack, "").replace("\\", "/")
            if doEncrypt:
                generateKey(pathFile, True, True)
                fileJSONContents["content"].append({'key': key, 'path': relativePath})
            elif not doNotAdd:
                fileJSONContents["content"].append({'path': relativePath})
    contents_path = os.path.join(inputPathSkinpack, 'contents.json')
    with open(contents_path, 'wb') as fileContents:
        manifest_path = os.path.join(inputPathSkinpack, 'manifest.json')
        with open(manifest_path, 'r') as file:
            jsonManifest = json.load(file)
            jsonUUID = jsonManifest['header']['uuid']
        with open(manifest_path, 'rb') as fileManifest:
            hashVal = b64encode(sha256(fileManifest.read()).digest()).decode()
            fileJSONSignatures = [{"hash": hashVal, "path": "manifest.json"}]
            sig_path = os.path.join(inputPathSkinpack, 'signatures.json')
            generateKey(json.dumps(fileJSONSignatures, separators=(',', ':')).encode('utf-8'), False, sig_path)
            fileJSONContents["content"].append({'key': key, 'path': 'signatures.json'})
        headerByte = b'\xfc\xb9\xcf\x9b\x00\x00\x00\x00\x00\x00\x00\x00\x24'
        empty = bytes(256)
        generateKey(json.dumps(fileJSONContents, separators=(',', ':')).encode('utf-8'), False, True)
        headerFinal = empty[:4] + headerByte + jsonUUID.encode('utf-8') + empty[53:] + encryptedVariable
        fileContents.write(headerFinal)

def import_to_minecraft_porter(temp_path, display_name=None):
    manifest = None
    for root, dirs, files in os.walk(temp_path):
        if "manifest.json" in files:
            manifest = Path(root) / "manifest.json"
            break
    if not manifest:
        raise Exception("manifest.json not found after porter")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    uuid = data["header"]["uuid"]
    pack_root = manifest.parent

    final_name = None
    texts_dir = pack_root / "texts"
    if texts_dir.exists():
        lang_files = list(texts_dir.glob("en_US.lang")) + [f for f in texts_dir.glob("*.lang") if f.name != "en_US.lang"]
        for lang_file in lang_files:
            try:
                with open(lang_file, 'r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('skinpack.') and '=' in line:
                            final_name = line.split('=', 1)[1].strip()
                            break
                        if line.startswith('persona.') and '.title=' in line:
                            final_name = line.split('=', 1)[1].strip()
                            break
                if final_name:
                    break
            except:
                continue

    if not final_name and display_name:
        final_name = display_name

    if not final_name:
        final_name = uuid

    invalid_chars = '<>:"/\\|?*'
    final_name = ''.join(c if c not in invalid_chars else '_' for c in final_name).strip()
    if not final_name:
        final_name = uuid

    dest_folder = SKIN_PACK_DIR / final_name
    if dest_folder.exists():
        dest_folder = SKIN_PACK_DIR / f"{final_name}_{uuid}"

    if dest_folder.exists():
        shutil.rmtree(dest_folder, ignore_errors=True)
    dest_folder.mkdir(parents=True, exist_ok=True)

    for item in pack_root.iterdir():
        shutil.move(str(item), str(dest_folder / item.name))
    shutil.rmtree(temp_path, ignore_errors=True)

def copy_pack_first(folder):
    temp_root = str(CACHE_DIR / "porter_temp")
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root, ignore_errors=True)
    os.makedirs(temp_root, exist_ok=True)
    new_name = f"{os.path.basename(folder)}_PORTED"
    temp_dest = os.path.join(temp_root, new_name)
    shutil.copytree(folder, temp_dest)
    return temp_dest

# ---------- DECRYPTION UTILITIES (for icon generation) ----------
def decrypt_file(encrypted_path: Path, output_path: Path, key_str: str = None) -> None:
    """Decrypt a file using the given key string (or fixed key if none provided)."""
    key_bytes = (key_str or FIXED_KEY).encode('utf-8')
    iv = key_bytes[:16]
    cipher = Cipher(algorithms.AES(key_bytes), modes.CFB8(iv))
    decryptor = cipher.decryptor()
    with open(encrypted_path, 'rb') as f:
        data = f.read()
    decrypted = decryptor.update(data) + decryptor.finalize()
    output_path.write_bytes(decrypted)

def decrypt_pack(pack_dir: Path, output_dir: Path) -> Path:
    contents = pack_dir / 'contents.json'
    if not contents.exists():
        # Not encrypted – just copy the folder
        shutil.copytree(pack_dir, output_dir)
        return output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Read and decrypt contents.json
    with open(contents, 'rb') as f:
        raw = f.read()
    # The first 256 bytes are the header (4 zero + 13 magic + 36 UUID + 203 padding)
    header_len = 256
    encrypted_body = raw[header_len:]
    # Decrypt the body using the same AES key
    cipher = Cipher(algorithms.AES(FIXED_KEY.encode('utf-8')), modes.CFB8(FIXED_KEY[:16].encode('utf-8')))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted_body) + decryptor.finalize()

    # Robust parse: ignore any extra bytes after the JSON object
    decoder = json.JSONDecoder()
    manifest_data, _ = decoder.raw_decode(decrypted.decode('utf-8'))
    manifest_data = manifest_data['content']

    # Step 2: Copy / decrypt each file or directory listed
    for item in manifest_data:
        rel_path = item['path']
        src = pack_dir / rel_path
        dst = output_dir / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if 'key' in item:
            decrypt_file(src, dst, item['key'])
        else:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    return output_dir

def get_head_uv_from_geometry(geometry_path: Path, geometry_name: str) -> tuple | None:
    try:
        with open(geometry_path, 'r', encoding='utf-8') as f:
            geo = json.load(f)
    except Exception as e:
        print(f"      -> geometry JSON error: {e}")
        return None

    # ── 1. Try new key‑value format (top‑level keys are identifiers) ──
    if isinstance(geo, dict) and geometry_name in geo:
        model = geo[geometry_name]
    else:
        # ── 2. Old format: {"minecraft:geometry": [ … ]} ──
        geos = geo.get('minecraft:geometry', [])
        for g in geos:
            if g.get('description', {}).get('identifier') == geometry_name:
                model = g
                break
        else:
            # case‑insensitive / last‑part fallback
            for g in geos:
                if g.get('description', {}).get('identifier', '').lower() == geometry_name.lower():
                    model = g
                    break
            else:
                suffix = geometry_name.split('.')[-1].lower()
                for g in geos:
                    if g.get('description', {}).get('identifier', '').split('.')[-1].lower() == suffix:
                        model = g
                        break
                else:
                    print(f"      -> identifier '{geometry_name}' not found in file")
                    return None

    # ── Find head bone and compute front face UV ──
    for bone in model.get('bones', []):
        if bone.get('name', '').lower() == 'head':
            for cube in bone.get('cubes', []):
                uv = cube.get('uv')
                size = cube.get('size', [8, 8, 8])

                # 1) Per‑face UV dict (most precise)
                if isinstance(uv, dict):
                    front = uv.get('front') or uv.get('head') or uv.get('base')
                    if front and isinstance(front, dict):
                        uv_arr = front.get('uv', [0, 0, 0, 0])
                        if len(uv_arr) == 4:          # [u1, v1, u2, v2]
                            u, v, u2, v2 = map(int, uv_arr)
                            return (u, v, u2 - u, v2 - v)
                        elif len(uv_arr) == 2:        # [u, v]  → assume 8×8
                            return (int(uv_arr[0]), int(uv_arr[1]), 8, 8)

                # 2) Simple cube UV: [u, v]
                if isinstance(uv, list) and len(uv) == 2 and all(isinstance(x, (int, float)) for x in uv):
                    u, v = int(uv[0]), int(uv[1])
                    sx, sy, sz = size[0], size[1], size[2]
                    # Bedrock default front face UV = (u + sz, v + sy)   (see note below)
                    front_u = u + sz
                    front_v = v + sy
                    # The front face uses the width (sx) and height (sy)
                    return (front_u, front_v, sx, sy)
            break

    print(f"      -> no usable UV in head bone")
    return None

def extract_head_face(pack_dir: Path) -> QPixmap | None:
    skins_json = pack_dir / 'skins.json'
    if not skins_json.exists():
        print(f"  [icon] No skins.json in {pack_dir.name}")
        return None

    try:
        with open(skins_json, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        decoder = json.JSONDecoder()
        skins_data, _ = decoder.raw_decode(raw_text)
    except Exception as e:
        print(f"  [icon] Failed to parse skins.json: {e}")
        return None

    skins = skins_data.get('skins', [])
    if not skins:
        print(f"  [icon] skins.json has no skins")
        return None

    for idx, skin in enumerate(skins):
        texture_path = skin.get('texture')
        if not texture_path:
            continue

        tex_file = pack_dir / texture_path
        if not tex_file.exists():
            print(f"    Skin {idx}: texture missing {tex_file}")
            continue

        try:
            img = Image.open(tex_file).convert('RGBA')
        except Exception as e:
            print(f"    Skin {idx}: failed to open image {e}")
            continue

        u, v, w, h = 8, 8, 8, 8
        geom_name = skin.get('geometry', None)
        geo_path = pack_dir / 'geometry.json'

        # Always try geometry.json if we have a geometry name and the file exists
        if geom_name and geo_path.exists():
            custom_uv = get_head_uv_from_geometry(geo_path, geom_name)
            if custom_uv:
                u, v, w, h = custom_uv
                print(f"    Skin {idx}: geometry UV: ({u}, {v}, {w}, {h})")
            else:
                # Identifier not found → fall back to scaled default
                scale = img.width / 64.0
                u, v, w, h = int(8*scale), int(8*scale), int(8*scale), int(8*scale)
                print(f"    Skin {idx}: geometry lookup failed, using scaled default ({u},{v},{w},{h})")
        else:
            # No geometry name / no geometry.json → scaled default
            scale = img.width / 64.0
            u, v, w, h = int(8*scale), int(8*scale), int(8*scale), int(8*scale)
            print(f"    Skin {idx}: scaled default UV: ({u}, {v}, {w}, {h})")

        # Safety bounds check
        if img.width < u + w or img.height < v + h:
            print(f"    Skin {idx}: crop out of bounds, falling back to unscaled default")
            u, v, w, h = 8, 8, 8, 8

        face = img.crop((u, v, u + w, v + h))

        # Skip fully transparent crops
        if face.getbbox() is None:
            print(f"    Skin {idx}: head crop is fully transparent, trying next skin")
            continue

        # Skip uniform colour (empty background)
        colors = face.getcolors()
        if colors is not None and len(colors) == 1:
            print(f"    Skin {idx}: head crop is uniform colour {colors[0]}, trying next skin")
            continue

        buf = BytesIO()
        face.save(buf, 'PNG')
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        print(f"    Skin {idx}: SUCCESS, returning pixmap")
        return pix

    print(f"  [icon] No usable skin found in {pack_dir.name}")
    return None

def get_pack_head_icon(pack_path: Path) -> QPixmap:
    temp_root = CACHE_DIR / 'icon_temp'
    if not temp_root.exists():
        temp_root.mkdir(parents=True)
    import uuid as _uuid
    temp_dir = temp_root / str(_uuid.uuid4())
    try:
        decrypt_pack(pack_path, temp_dir)
        pix = extract_head_face(temp_dir)
        return pix
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ---------- MERGER TAB ----------
class MergerTab(QWidget):
    def __init__(self, parent, hover_sound, click_sound):
        super().__init__(parent)
        self.parent = parent
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self.pack_dirs = []
        self.merger_worker = None
        self.merged_pack_path = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.title = QLabel("Skin Pack Merger")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)
        self.desc = QLabel("Drag multiple skin pack folders to merge them into one.\nYou can also encrypt the resulting pack.")
        self.desc.setStyleSheet("color: #aaa; font-size: 12px;")
        self.desc.setAlignment(Qt.AlignCenter)
        self.desc.setWordWrap(True)
        layout.addWidget(self.desc)
        self.drop_area = DragDropWidget("Drop folders here", folder_mode=True, multi_folder=True, callback=self.add_folders)
        self.drop_area.setMinimumHeight(120)
        layout.addWidget(self.drop_area)
        self.pack_list = QListWidget()
        self.pack_list.setMinimumHeight(100)
        layout.addWidget(self.pack_list)
        manifest_layout = QHBoxLayout()
        self.manifest_label = QLabel("Manifest:")
        manifest_layout.addWidget(self.manifest_label)
        self.manifest_dropdown = QComboBox()
        self.manifest_dropdown.addItems(list(MANIFEST_OPTIONS.keys()))
        manifest_layout.addWidget(self.manifest_dropdown)
        manifest_layout.addStretch()
        layout.addLayout(manifest_layout)
        self.encrypt_checkbox = QCheckBox("Encrypt before import")
        self.encrypt_checkbox.setChecked(True)
        layout.addWidget(self.encrypt_checkbox)
        btn_layout = QHBoxLayout()
        self.clear_btn = SoundButton("Clear", self.hover_sound, self.click_sound)
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.clear_btn)
        self.merge_btn = SoundButton("Merge", self.hover_sound, self.click_sound)
        self.merge_btn.clicked.connect(self.start_merge)
        btn_layout.addWidget(self.merge_btn)
        self.import_merged_btn = SoundButton("Import", self.hover_sound, self.click_sound)
        self.import_merged_btn.clicked.connect(self.import_merged_pack)
        self.import_merged_btn.setEnabled(False)
        btn_layout.addWidget(self.import_merged_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        layout.addWidget(self.log_output)

    def apply_theme(self, theme):
        if theme == "light":
            text_color = "#222"
            dim_color = "#555"
        else:
            text_color = "#e0e0e0"
            dim_color = "#aaa"
        self.title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {text_color};")
        self.desc.setStyleSheet(f"color: {dim_color}; font-size: 12px;")
        self.manifest_label.setStyleSheet(f"color: {text_color};")

    def add_folders(self, paths):
        for p in paths:
            p = Path(p)
            if p.is_dir() and (p / "skins.json").exists():
                if str(p) not in [self.pack_list.item(i).text() for i in range(self.pack_list.count())]:
                    self.pack_list.addItem(str(p))
                    self.pack_dirs.append(p)
            else:
                show_warning(self, "Invalid Pack", f"{p} is not a valid skin pack.")
        self.merge_btn.setEnabled(len(self.pack_dirs) >= 2)

    def clear_list(self):
        self.pack_list.clear()
        self.pack_dirs.clear()
        self.log_output.clear()
        self.import_merged_btn.setEnabled(False)

    def start_merge(self):
        if self.merge_btn.isEnabled() == False:
            return
        if len(self.pack_dirs) < 2:
            show_warning(self, "Not Enough Packs", "Select at least 2 packs.")
            return
        self.merge_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        output_dir = CACHE_DIR / "merged_skinpack"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.merger_worker = MergerWorker(self.pack_dirs, output_dir)
        self.merger_worker.log.connect(self.log_output.appendPlainText)
        self.merger_worker.progress.connect(self.progress_bar.setValue)
        self.merger_worker.finished.connect(self.on_merge_finished)
        self.merger_worker.start()

    def on_merge_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.merge_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        if success:
            self.log_output.appendPlainText("\nMerge finished!")
            self.import_merged_btn.setEnabled(True)
            self.merged_pack_path = CACHE_DIR / "merged_skinpack"
        else:
            QMessageBox.critical(self, "Merge Error", message)

    def encrypt_merged_pack(self, pack_path, manifest_choice):
        try:
            self.log_output.appendPlainText(f"Encrypting with {manifest_choice}...")
            temp_copy = copy_pack_first(str(pack_path))
            setup_porter(temp_copy, manifest_choice)
            global key, encryptedVariable, inputPathSkinpack
            original_dir = os.getcwd()
            os.chdir(temp_copy)
            try:
                tool_porter(temp_copy)
            finally:
                os.chdir(original_dir)
            self.log_output.appendPlainText("Encryption done.")
            shutil.rmtree(pack_path)
            shutil.move(temp_copy, pack_path)
            return True
        except Exception as e:
            self.log_output.appendPlainText(f"Encryption failed: {e}")
            return False

    def import_merged_pack(self):
        if not hasattr(self, 'merged_pack_path') or not self.merged_pack_path.exists():
            show_warning(self, "No pack to import", "Please merge packs first.")
            return
        if self.import_merged_btn.isEnabled() == False:
            return
        self.import_merged_btn.setEnabled(False)
        try:
            manifest_path = None
            for root, dirs, files in os.walk(self.merged_pack_path):
                if "manifest.json" in files:
                    manifest_path = Path(root) / "manifest.json"
                    break
            if not manifest_path:
                QMessageBox.critical(self, "Error", "manifest.json not found.")
                return
            with open(manifest_path) as f:
                manifest_data = json.load(f)
            uuid = manifest_data["header"]["uuid"]
            if self.encrypt_checkbox.isChecked():
                choice = self.manifest_dropdown.currentText()
                if not self.encrypt_merged_pack(self.merged_pack_path, choice):
                    QMessageBox.critical(self, "Encryption Failed", "Unable to encrypt.")
                    return
            dest_name = manifest_path.parent.name
            dest = SKIN_PACK_DIR / dest_name
            if dest.exists():
                reply = QMessageBox.question(self, "Overwrite", f"'{dest_name}' exists. Overwrite?", QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(manifest_path.parent, dest)
            shutil.rmtree(self.merged_pack_path, ignore_errors=True)
            self.log_output.appendPlainText(f"Imported to {dest}")
            self.parent.scan_local()
            self.parent.refresh_installed()
        finally:
            self.import_merged_btn.setEnabled(True)

# ------------------------------------------------------------
#  Run the application
# ------------------------------------------------------------
if __name__ == "__main__":
    from app import App

    myappid = 'ecliptix.melancholy.1.1.7'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    app.setStyle('Fusion')
    mc_font = load_minecraft_font()
    if mc_font and mc_font.family():
        app.setFont(mc_font)
    saved_theme = settings.get("theme", "dark")
    app.setStyleSheet(DARK_STYLESHEET if saved_theme == "dark" else LIGHT_STYLESHEET)
    splash = LoadingScreen()
    splash.show()
    app.processEvents()
    win = App(splash)
    QTimer.singleShot(2000, win.show)
    sys.exit(app.exec())