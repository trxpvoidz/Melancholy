"""
Melancholy Skin Pack Manager
Copyright (c) 2026 TrxpVoidz (Ecliptix)
All rights reserved.
"""

import sys, os, json, zipfile, shutil, tempfile, ctypes, time, subprocess, winreg
from pathlib import Path
from io import BytesIO
from hashlib import sha256
from base64 import b64encode

import requests
from PIL import Image
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QMessageBox, QProgressBar, QTextEdit, QTabWidget,
    QFileDialog, QListWidget, QListWidgetItem, QComboBox, QSplashScreen,
    QSizePolicy, QLineEdit, QPlainTextEdit, QCheckBox, QFrame, QGraphicsOpacityEffect
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

# ---------------- CONSTANTS ----------------
DISCORD_INVITE = "https://discord.gg/3x3M289anm"
GITHUB_URL     = "https://github.com/trxpvoidz/Melancholy"
APP_VERSION    = "1.1.5"

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
"""

# ---------------- RESOURCE PATH ----------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ---------------- CUSTOM WARNING POPUP ----------------
def show_warning(parent, title, message):
    msg = QMessageBox(QMessageBox.Warning, title, message, parent=parent)
    icon_path = resource_path("assets/Warning_alex.png")
    if os.path.exists(icon_path):
        msg.setIconPixmap(QPixmap(icon_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return msg.exec()

# ---------------- FONT LOADING ----------------
def load_minecraft_font():
    font_path = resource_path("assets/Minecraft-Seven_v2.ttf")
    if not os.path.exists(font_path):
        return QFont()
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        return QFont()
    family = QFontDatabase.applicationFontFamilies(font_id)[0]
    return QFont(family, 10)

# ---------------- VERSION DETECTION & PATHS ----------------
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
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

SKIN_PACK_DIR, PERSONA_DIR = get_mc_paths(USE_UWP)
LEGACY_VAULT_DIR = SKIN_PACK_DIR.parent / "legacy_vault"
LEGACY_VAULT_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = SKIN_PACK_DIR / ".skinpack_manager_state.json"
LEGACY_STATE_FILE = LEGACY_VAULT_DIR / ".legacy_vault_state.json"
MARKETPLACE_URL = "https://raw.githubusercontent.com/trxpvoidz/Skin-Pack-Store-Importer/main/store.json"

# ---------------- STATE ----------------
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

# ---------------- MANIFEST ----------------
def find_manifest(folder):
    for r, _, f in os.walk(folder):
        if "manifest.json" in f:
            return Path(r) / "manifest.json"
    return None

def read_manifest(path):
    data = json.loads(path.read_text())
    return data["header"]["uuid"], data["header"].get("version", [0,0,0])

# ---------------- LOCALIZATION ----------------
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

# ---------------- SKIN PACK MERGER UTILITIES ----------------
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

# ---------------- BACKGROUND WIDGET ----------------
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

# ---------------- WORKERS ----------------
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

class StoreLoader(QThread):
    finished = Signal(list)
    error = Signal(str)
    def run(self):
        try:
            r = requests.get(MARKETPLACE_URL, timeout=15)
            packs = r.json()["packs"]
            self.finished.emit(packs)
        except Exception as e:
            self.error.emit(str(e))

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
            tmp_dir = Path(tempfile.gettempdir()) / "mcbe_skin_downloads"
            tmp_dir.mkdir(exist_ok=True)
            zip_path = tmp_dir / "pack.zip"
            r = requests.get(self.url, stream=True, timeout=30)
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

class ThumbnailLoader(QThread):
    finished = Signal(QPixmap)
    error = Signal()
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            r = requests.get(self.url, timeout=10)
            img = Image.open(BytesIO(r.content))
            img.thumbnail((200, 200))
            buf = BytesIO()
            img.save(buf, "PNG")
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            self.finished.emit(pix)
        except:
            self.error.emit()

# ---------------- CUSTOM WIDGETS ----------------
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

    def update_badge(self, state):
        if any(info.get("store_name") == self.pack.get("name") for info in state.get("known", [])):
            self.badge.setText("Installed")
            self.badge.setStyleSheet("color: white; font-size: 11px;")
        else:
            self.badge.clear()
    def load_thumb(self, url):
        if not url:
            return
        self.loader = ThumbnailLoader(url)
        self.loader.finished.connect(self.thumb.setPixmap)
        self.loader.error.connect(lambda: self.thumb.setText("No image"))
        self.loader.start()

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

# ---------------- HOME TAB ----------------
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

# ---------------- SETTINGS TAB ----------------
class SettingsTab(QWidget):
    def __init__(self, parent, hover_sound, click_sound):
        super().__init__(parent)
        self.parent = parent
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

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

        sound_layout = QHBoxLayout()
        sound_layout.addStretch()
        sound_label = QLabel("Sound:")
        self.sound_check = QCheckBox("Enable sounds")
        self.sound_check.setChecked(settings.get("sound_enabled", True))
        # Use `toggled` signal (sends a bool) instead of `stateChanged`
        self.sound_check.toggled.connect(self.toggle_sound)
        sound_layout.addWidget(sound_label)
        sound_layout.addWidget(self.sound_check)
        sound_layout.addStretch()
        layout.addLayout(sound_layout)

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

# ---------------- MERGER TAB ----------------
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
        if len(self.pack_dirs) < 2:
            show_warning(self, "Not Enough Packs", "Select at least 2 packs.")
            return
        output_dir = Path(tempfile.gettempdir()) / "merged_skinpack"
        if output_dir.exists():
            shutil.rmtree(output_dir)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.merge_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
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
            self.merged_pack_path = Path(tempfile.gettempdir()) / "merged_skinpack"
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

# ---------------- MAIN APP ----------------
class App(QMainWindow):
    def __init__(self, splash):
        super().__init__()
        self.splash = splash
        self.downloading = False
        self.porter_running = False
        self.porter_folder = None
        self.rpc = None
        self.mc_launched = False
        self.sound_enabled = settings.get("sound_enabled", True)
        self.setWindowTitle("Melancholy")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.resize(1200, 800)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.background = BackgroundWidget(self)
        self.background.lower()
        self.background.setGeometry(self.rect())

        saved_theme = settings.get("theme", "dark")
        self.background.set_theme(saved_theme)
        self.current_theme = saved_theme

        self.init_sound()
        self.hover_sound = self.load_sound("hover.wav")
        self.click_sound = self.load_sound("click.wav")
        self.state = load_state()
        self.legacy_state = load_legacy_state()
        self.scan_local()
        self.scan_capes()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header = QHBoxLayout()
        self.app_title = QLabel("Melancholy")
        self.app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-left: 8px;")
        header.addWidget(self.app_title)
        header.addStretch()

        self.version_combo = QComboBox()
        self.version_combo.addItems(["GDK", "UWP"])
        self.version_combo.setCurrentIndex(0 if not USE_UWP else 1)
        self.version_combo.setStyleSheet("""
            QComboBox { background: rgba(40,40,40,200); border: 1px solid #555; border-radius: 6px; padding: 4px 8px; color: #e0e0e0; }
            QComboBox::drop-down { border: none; }
        """)
        self.version_combo.currentIndexChanged.connect(self.switch_mc_version)
        header.addWidget(QLabel("MC:"))
        header.addWidget(self.version_combo)

        self.launch_btn = SoundButton("Launch", self.hover_sound, self.click_sound)
        self.launch_btn.setStyleSheet("QPushButton { background: rgba(255,255,255,15); border: 1px solid #555; border-radius: 6px; padding: 5px 10px; color: white; } QPushButton:hover { background: rgba(255,255,255,30); }")
        self.launch_btn.clicked.connect(self.launch_minecraft)
        header.addWidget(self.launch_btn)

        self.restart_btn = SoundButton("Restart", self.hover_sound, self.click_sound)
        self.restart_btn.setStyleSheet("QPushButton { background: rgba(255,255,255,15); border: 1px solid #555; border-radius: 6px; padding: 5px 10px; color: white; } QPushButton:hover { background: rgba(255,255,255,30); }")
        self.restart_btn.clicked.connect(self.restart_minecraft)
        header.addWidget(self.restart_btn)

        header.addStretch()
        self.sound_btn = SoundButton("", self.hover_sound, self.click_sound)
        self.sound_btn.setStyleSheet("QPushButton { background: transparent; border: 1px solid #555; border-radius: 6px; color: white; padding: 5px 10px; } QPushButton:hover { background: rgba(255,255,255,10); }")
        self.sound_btn.clicked.connect(self.toggle_sound)
        header.addWidget(self.sound_btn)
        self.credits_btn = SoundButton("", self.hover_sound, self.click_sound)
        self.credits_btn.setText("Credits")
        self.credits_btn.setStyleSheet("QPushButton { background: transparent; border: 1px solid #555; border-radius: 6px; color: white; padding: 5px 10px; } QPushButton:hover { background: rgba(255,255,255,10); }")
        self.credits_btn.clicked.connect(self.show_credits)
        header.addWidget(self.credits_btn)
        main_layout.addLayout(header)

        self.update_sound_button()

        self.tabs = QTabWidget()

        self.home_tab = HomeTab(self, self.hover_sound, self.click_sound)
        self.store_tab = QWidget()
        self.installed_tab = QWidget()
        self.porter_tab = QWidget()
        self.capes_tab = QWidget()
        self.merger_tab = MergerTab(self, self.hover_sound, self.click_sound)
        self.settings_tab = SettingsTab(self, self.hover_sound, self.click_sound)

        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.store_tab, "Store")
        self.tabs.addTab(self.installed_tab, "Installed")
        self.tabs.addTab(self.porter_tab, "Porter")
        self.tabs.addTab(self.capes_tab, "Persona Explorer")
        self.tabs.addTab(self.merger_tab, "Merger")
        self.tabs.addTab(self.settings_tab, "Settings")

        main_layout.addWidget(self.tabs)

        self.build_store()
        self.build_installed()
        self.build_porter()
        self.build_capes()
        self.load_store()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.tabs.setCurrentIndex(0)

        self.apply_theme(saved_theme)

        self.setWindowOpacity(0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(1000)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_anim.start()
        QTimer.singleShot(1500, self.splash.close)
        self.init_discord_rpc()

        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(30000)
        self._idle_timer.timeout.connect(self._enter_idle_mode)
        self._idle_timer.start()
        self._idle = False
        self.setMouseTracking(True)

    # ... (sound, RPC, Minecraft, idle, and other methods remain exactly the same as the last full version – they are unchanged)
    # I'll include the rest unchanged for completeness.

    # ------------------------------------------------------------
    #  SOUND MANAGEMENT
    # ------------------------------------------------------------
    def load_sound(self, filename):
        sound = QSoundEffect()
        sound.setLoopCount(1)
        sound.setVolume(1.0)
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        cwd = Path(os.getcwd())
        locations = [script_dir / "assets", cwd / "assets", script_dir, cwd]
        for folder in locations:
            candidate = folder / filename
            if candidate.exists():
                sound.setSource(QUrl.fromLocalFile(str(candidate)))
                return sound
        print(f"Warning: Sound file {filename} not found.")
        return None

    def init_sound(self):
        try:
            self.sound = QSoundEffect()
            self.sound.setLoopCount(1)
            self.sound.setVolume(1.0)
            script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            cwd = Path(os.getcwd())
            locations = [script_dir / "assets", cwd / "assets", script_dir, cwd]
            for folder in locations:
                candidate = folder / "startup_sound.wav"
                if candidate.exists():
                    self.sound.setSource(QUrl.fromLocalFile(str(candidate)))
                    if self.sound_enabled:
                        self.sound.play()
                    break
        except:
            pass

    def update_sound_button(self):
        self.sound_btn.setText(f"Sound: {'On' if self.sound_enabled else 'Off'}")

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.update_sound_button()
        settings["sound_enabled"] = self.sound_enabled
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        if not self.sound_enabled and self.sound and self.sound.isPlaying():
            self.sound.stop()

    # ------------------------------------------------------------
    #  DISCORD RICH PRESENCE
    # ------------------------------------------------------------
    def init_discord_rpc(self):
        try:
            from pypresence import Presence
            self.rpc = Presence("1522470438930747559")
            self.rpc.connect()
            self.mc_launched = False
            self.update_rpc_state("Managing skin packs", buttons=[
                {"label": "Join Discord", "url": DISCORD_INVITE},
                {"label": "Download GitHub", "url": GITHUB_URL}
            ])
            self._mc_check_timer = QTimer(self)
            self._mc_check_timer.timeout.connect(self._check_mc_status)
            self._mc_check_timer.start(5000)
            self.on_tab_changed(0)
            print("Discord Rich Presence connected")
        except Exception as e:
            self.rpc = None
            print(f"Discord RPC not available: {e}")

    def update_rpc_state(self, details, state=None, large_image="melancholy",
                         large_text="Melancholy", small_image=None, small_text=None, buttons=None):
        if self.rpc:
            try:
                kwargs = {
                    "details": details,
                    "large_image": large_image,
                    "large_text": large_text,
                    "start": time.time()
                }
                if state:
                    kwargs["state"] = state
                if small_image:
                    kwargs["small_image"] = small_image
                if small_text:
                    kwargs["small_text"] = small_text
                if buttons:
                    kwargs["buttons"] = buttons
                self.rpc.update(**kwargs)
            except Exception as e:
                print(f"Failed to update Discord presence: {e}")

    def _set_mc_presence_lock(self, lock: bool):
        if lock:
            try:
                self.tabs.currentChanged.disconnect(self.on_tab_changed)
            except Exception:
                pass
        else:
            try:
                self.tabs.currentChanged.connect(self.on_tab_changed)
            except Exception:
                pass

    def _check_mc_status(self):
        if not self.rpc or not self.mc_launched:
            return
        if getattr(self, '_mc_ignore_checks', 0) > 0:
            self._mc_ignore_checks -= 1
            return
        mc_running = False
        if psutil:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and ('Minecraft.Windows.exe' in proc.info['name'] or
                                           'Minecraft.exe' in proc.info['name']):
                    mc_running = True
                    break
        else:
            try:
                output = subprocess.check_output(
                    'tasklist /FI "IMAGENAME eq Minecraft.Windows.exe"', shell=True
                ).decode()
                if "Minecraft.Windows.exe" in output:
                    mc_running = True
            except:
                pass
        if not mc_running:
            self.mc_launched = False
            self._set_mc_presence_lock(False)
            tab = getattr(self, 'last_tab_name', None)
            details = f"Viewing {tab}" if tab else "Managing skin packs"
            self.update_rpc_state(details, "Managing skin packs", buttons=[
                {"label": "Join Discord", "url": DISCORD_INVITE},
                {"label": "Download GitHub", "url": GITHUB_URL}
            ])
            self.on_tab_changed(self.tabs.currentIndex())

    def on_tab_changed(self, index):
        if self.mc_launched:
            return
        self.refresh_all()
        tab_names = ["Home", "Store", "Installed", "Porter", "Persona Explorer", "Merger", "Settings"]
        if index < len(tab_names):
            self.last_tab_name = tab_names[index]
            self.update_rpc_state(
                "Managing skin packs",
                f"Viewing {self.last_tab_name}",
                buttons=[
                    {"label": "Join Discord", "url": DISCORD_INVITE},
                    {"label": "Download GitHub", "url": GITHUB_URL}
                ]
            )

    # ------------------------------------------------------------
    #  MINECRAFT LAUNCH / RESTART
    # ------------------------------------------------------------
    @staticmethod
    def find_gdk_executables():
        exes = []
        for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            base = Path(f"{drive}:\\XboxGames")
            if not base.exists():
                continue
            for c in [base / "Minecraft for Windows" / "Content",
                      base / "Minecraft Preview for Windows" / "Content"]:
                mc = c / "Minecraft.Windows.exe"
                if mc.exists():
                    exes.append(str(mc))
            try:
                for root, dirs, files in os.walk(base):
                    if root[len(str(base)):].count(os.sep) > 3:
                        del dirs[:]
                        continue
                    if "Minecraft.Windows.exe" in files:
                        exes.append(str(Path(root) / "Minecraft.Windows.exe"))
            except PermissionError:
                continue
        return exes

    def launch_minecraft(self):
        try:
            if USE_UWP:
                subprocess.Popen(
                    'explorer.exe shell:appsFolder\\Microsoft.MinecraftUWP_8wekyb3d8bbwe!Game',
                    shell=True
                )
                self._set_mc_presence()
                QMessageBox.information(self, "Launched", "Minecraft UWP has been launched.")
                return
            exes = self.find_gdk_executables()
            if exes:
                subprocess.Popen([exes[0]], shell=True)
                self._set_mc_presence()
                QMessageBox.information(self, "Launched", "Minecraft Bedrock has been launched.")
                return
            try:
                subprocess.Popen(
                    'explorer.exe shell:appsFolder\\Microsoft.MinecraftWindows_8wekyb3d8bbwe!Game',
                    shell=True
                )
                self._set_mc_presence()
                QMessageBox.information(self, "Launched", "Minecraft (GDK) launched via App ID.")
                return
            except:
                pass
            launcher_paths = [
                Path(os.getenv("PROGRAMFILES(X86)", "")) / "Minecraft Launcher" / "Minecraft.exe",
                Path(os.getenv("PROGRAMFILES", "")) / "Minecraft Launcher" / "Minecraft.exe",
            ]
            for lp in launcher_paths:
                if lp.exists():
                    subprocess.Popen([str(lp)], shell=True)
                    self._set_mc_presence()
                    QMessageBox.information(self, "Launcher", "Minecraft Launcher opened.")
                    return
            subprocess.Popen('start ms-windows-store://pdp/?productid=9NBLGGH2JHXJ', shell=True)
            show_warning(self, "Game Not Found",
                         "Minecraft executable not found. Opening Microsoft Store.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch Minecraft: {e}")

    def _set_mc_presence(self):
        self.mc_launched = True
        self._mc_ignore_checks = 2
        if hasattr(self, '_mc_check_timer'):
            self._mc_check_timer.start(5000)
        self._set_mc_presence_lock(True)
        self.update_rpc_state(
            "Playing Minecraft Bedrock",
            state="Launched via Melancholy",
            large_image="mcbe",
            large_text="Minecraft Bedrock",
            small_image="melancholy",
            small_text="Melancholy",
            buttons=None
        )

    def restart_minecraft(self):
        if psutil is None:
            show_warning(self, "psutil required", "Install 'psutil' to restart Minecraft.\n(pip install psutil)")
            return
        killed = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and ('Minecraft.Windows.exe' in proc.info['name'] or
                                       'Minecraft.exe' in proc.info['name']):
                try:
                    proc.kill()
                    killed = True
                except:
                    pass
        if killed:
            time.sleep(1)
        self.launch_minecraft()
        if killed:
            QMessageBox.information(self, "Restarted", "Minecraft has been restarted.")

    # ------------------------------------------------------------
    #  IDLE MODE
    # ------------------------------------------------------------
    def _enter_idle_mode(self):
        if self._idle:
            return
        self._idle = True
        if hasattr(self, '_mc_check_timer'):
            self._mc_check_timer.setInterval(30000)
        try:
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        except:
            pass

    def _exit_idle_mode(self):
        if not self._idle:
            return
        self._idle = False
        if hasattr(self, '_mc_check_timer'):
            self._mc_check_timer.setInterval(5000)
        try:
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(psutil.NORMAL_PRIORITY_CLASS)
        except:
            pass
        self._idle_timer.start(30000)

    def event(self, event):
        if event.type() in (QEvent.MouseMove, QEvent.KeyPress, QEvent.MouseButtonPress):
            self._exit_idle_mode()
            self._idle_timer.start(30000)
        return super().event(event)

    # ---------------- STANDARD METHODS ----------------
    def show_credits(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Credits")
        msg.setText("Melancholy Skin Pack Manager\n\nCreated by TrxpVoidz (Ecliptix)\nSpecial Thanks to a6wwp")
        msg.exec()

    def switch_mc_version(self, index):
        global SKIN_PACK_DIR, PERSONA_DIR, LEGACY_VAULT_DIR, STATE_FILE, LEGACY_STATE_FILE, USE_UWP
        USE_UWP = (index == 1)
        SKIN_PACK_DIR, PERSONA_DIR = get_mc_paths(USE_UWP)
        LEGACY_VAULT_DIR = SKIN_PACK_DIR.parent / "legacy_vault"
        LEGACY_VAULT_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE = SKIN_PACK_DIR / ".skinpack_manager_state.json"
        LEGACY_STATE_FILE = LEGACY_VAULT_DIR / ".legacy_vault_state.json"
        settings["use_uwp"] = USE_UWP
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
        self.state = load_state()
        self.refresh_all()
        self.load_store()
        QMessageBox.information(self, "Version Switched",
                                f"Now using {'UWP' if USE_UWP else 'GDK'} Minecraft paths.")

    def scan_local(self):
        self.state["known"] = []
        for folder in SKIN_PACK_DIR.iterdir():
            if not folder.is_dir():
                continue
            manifest = find_manifest(folder)
            if not manifest:
                continue
            try:
                uuid, version = read_manifest(manifest)
            except:
                continue
            self.state["known"].append({
                "uuid": uuid,
                "version": version,
                "path": str(folder),
                "store_name": get_pack_display_name(folder),
                "source": "local"
            })
        save_state(self.state)

    def load_persona_catalog(self):
        catalog_path = PERSONA_DIR / "personaCatalogItemCache.json"
        if not catalog_path.exists():
            return {}
        try:
            raw = json.loads(catalog_path.read_text())
            pieces = raw.get("pieceids", {})
            catalog = {}
            for pid, info in pieces.items():
                catalog[pid] = {
                    "name": info.get("piecename", "Unknown"),
                    "icon": info.get("iconurl", "")
                }
            return catalog
        except:
            return {}

    def scan_capes(self):
        self.state["capes"] = []
        for item in PERSONA_DIR.iterdir():
            if item.is_file() and (item.suffix == '' or item.suffix == '.='):
                try:
                    new_path = item.with_suffix('.zip')
                    item.rename(new_path)
                    extract_dir = new_path.with_suffix('')
                    extract_dir.mkdir(exist_ok=True)
                    with zipfile.ZipFile(new_path, 'r') as z:
                        z.extractall(extract_dir)
                    new_path.unlink()
                except Exception as e:
                    print(f"Could not extract {item.name}: {e}")
                    if new_path.exists():
                        new_path.rename(item)
        catalog = self.load_persona_catalog()
        for folder in PERSONA_DIR.iterdir():
            if not folder.is_dir():
                continue
            manifest = find_manifest(folder)
            if not manifest:
                continue
            try:
                uuid, version = read_manifest(manifest)
            except:
                continue
            thumb_url = catalog.get(uuid, {}).get("icon", None)
            self.state["capes"].append({
                "uuid": uuid,
                "version": version,
                "path": str(folder),
                "store_name": get_pack_display_name(folder),
                "source": "local",
                "thumbnail_url": thumb_url
            })
        save_state(self.state)

    def build_store(self):
        layout = QVBoxLayout(self.store_tab)
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search store...")
        self.search_bar.textChanged.connect(self.filter_store)
        search_layout.addWidget(self.search_bar)
        layout.addLayout(search_layout)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }")
        self.grid_host = QWidget()
        self.grid_host.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(12)
        self.scroll.setWidget(self.grid_host)
        layout.addWidget(self.scroll)
        self.progress = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(100)
        layout.addWidget(self.progress)
        layout.addWidget(self.log)
        self.store_cards = []

    def filter_store(self, text):
        for card in self.store_cards:
            card.setVisible(text.lower() in card.pack.get("name", "").lower())

    def load_store(self):
        self.store_loader = StoreLoader()
        self.store_loader.finished.connect(self.populate_store)
        self.store_loader.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.store_loader.start()

    def populate_store(self, packs):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        self.store_cards.clear()
        StoreCard.instances.clear()
        row = col = 0
        for pack in packs:
            card = StoreCard(pack, self.state, self.start_download, self.uninstall_pack, self.hover_sound, self.click_sound)
            self.grid.addWidget(card, row, col)
            self.store_cards.append(card)
            col += 1
            if col == 4:
                col = 0
                row += 1
        self.filter_store(self.search_bar.text())
        self.apply_theme(self.current_theme)

    def start_download(self, pack):
        if self.downloading:
            return
        self.downloading = True
        self.progress.setValue(0)
        self.log.clear()
        self.worker = DownloadWorker(pack["zip_url"])
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log.append)
        self.worker.finished.connect(lambda tmp: self.finish_download(tmp, pack))
        self.worker.error.connect(self.download_error)
        self.worker.start()

    def finish_download(self, tmp, pack):
        self.downloading = False
        self.install_pack(tmp, pack, original_name=pack.get("name"))

    def download_error(self, err):
        self.downloading = False
        QMessageBox.critical(self, "Download Error", err)

    def install_pack(self, source: Path, pack, original_name=None, target_dir=None):
        if target_dir is None:
            target_dir = SKIN_PACK_DIR
        self.log.append("Installing...")
        try:
            is_zip = False
            extracted_temp = None
            if source.is_file() and (source.suffix.lower() == '.zip' or source.suffix == ''):
                is_zip = True
                zip_path = source
                if source.suffix == '':
                    zip_path = source.with_suffix('.zip')
                    shutil.copy2(source, zip_path)
                try:
                    zipfile.ZipFile(zip_path, 'r')
                except:
                    raise Exception("File is not a valid zip archive.")
                temp_extract = target_dir / "__temp_install__"
                if temp_extract.exists():
                    shutil.rmtree(temp_extract)
                temp_extract.mkdir()
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(temp_extract)
                pack_root_candidate = temp_extract
            elif source.is_dir():
                pack_root_candidate = source
            else:
                raise Exception("Source must be a folder or a zip file (or extensionless zip).")

            manifest_path = None
            for root, dirs, files in os.walk(pack_root_candidate):
                if "manifest.json" in files:
                    manifest_path = Path(root) / "manifest.json"
                    break
            if not manifest_path:
                raise Exception("manifest.json not found")

            new_uuid, version = read_manifest(manifest_path)

            existing = None
            if target_dir == SKIN_PACK_DIR:
                existing = next((i for i in self.state["known"] if i["uuid"] == new_uuid), None)
            else:
                existing = next((i for i in self.state["capes"] if i["uuid"] == new_uuid), None)

            if existing:
                msg = QMessageBox(self)
                msg.setWindowTitle("Existing Pack Found")
                msg.setText(f"A pack with the same UUID already exists.\n\nInstalled: {existing['store_name']}\nUUID: {new_uuid}\n\nReplace it?")
                msg.setStyleSheet("""
                    QMessageBox { background-color: rgba(20,20,20,230); color: white; }
                    QMessageBox QLabel { color: white; }
                    QPushButton { background: rgba(255,255,255,50); border: 1px solid rgba(255,255,255,100); border-radius: 5px; color: white; padding: 5px 15px; }
                    QPushButton:hover { background: rgba(255,255,255,100); }
                """)
                replace_btn = msg.addButton("Replace", QMessageBox.AcceptRole)
                cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
                msg.exec()
                if msg.clickedButton() == cancel_btn:
                    if is_zip:
                        shutil.rmtree(pack_root_candidate, ignore_errors=True)
                    return
                shutil.rmtree(existing["path"], ignore_errors=True)
                if target_dir == SKIN_PACK_DIR:
                    self.state["known"].remove(existing)
                else:
                    self.state["capes"].remove(existing)

            dest_name = original_name if is_zip and original_name else (source.stem if is_zip else source.name)
            dest = target_dir / dest_name
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(manifest_path.parent, dest)
            if is_zip:
                shutil.rmtree(pack_root_candidate, ignore_errors=True)

            display_name = get_pack_display_name(dest)
            entry = {
                "uuid": new_uuid, "version": version, "path": str(dest),
                "store_name": display_name, "source": "store" if is_zip else "local"
            }
            if target_dir == SKIN_PACK_DIR:
                self.state["known"].append(entry)
            else:
                self.state["capes"].append(entry)
            save_state(self.state)
            self.log.append("Installation complete.")
            self.refresh_all()
            self.load_store()
        except Exception as e:
            QMessageBox.critical(self, "Install Error", str(e))
            if 'extracted_temp' in locals() and extracted_temp and extracted_temp.exists():
                shutil.rmtree(extracted_temp, ignore_errors=True)

    # ---------------- INSTALLED TAB ----------------
    def build_installed(self):
        layout = QVBoxLayout(self.installed_tab)
        search_layout = QHBoxLayout()
        self.installed_search_bar = QLineEdit()
        self.installed_search_bar.setPlaceholderText("Search installed...")
        self.installed_search_bar.textChanged.connect(self.filter_installed)
        search_layout.addWidget(self.installed_search_bar)
        layout.addLayout(search_layout)
        btn_row = QHBoxLayout()
        refresh = SoundButton("Refresh", self.hover_sound, self.click_sound)
        refresh.clicked.connect(self.refresh_installed)
        btn_row.addWidget(refresh)
        wipe = SoundButton("Safe Wipe", self.hover_sound, self.click_sound)
        wipe.clicked.connect(self.safe_wipe)
        btn_row.addWidget(wipe)
        delete_btn = SoundButton("Delete", self.hover_sound, self.click_sound)
        delete_btn.clicked.connect(self.delete_selected)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.import_drop = DragDropWidget("Drop skin pack folder or ZIP here", folder_mode=True, allow_zip=True, callback=self.handle_import_drop)
        layout.addWidget(self.import_drop)
        self.installed_list = QListWidget()
        self.installed_list.itemClicked.connect(self.on_installed_item_selected)
        layout.addWidget(self.installed_list)

        self.installed_path_label = QLabel("")
        self.installed_path_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px;")
        self.installed_path_label.setWordWrap(True)
        layout.addWidget(self.installed_path_label, alignment=Qt.AlignCenter)

        self.installed_open_btn = SoundButton("Open Folder", self.hover_sound, self.click_sound)
        self.installed_open_btn.clicked.connect(self.open_selected_folder)
        layout.addWidget(self.installed_open_btn, alignment=Qt.AlignCenter)

        self.refresh_installed()

    def filter_installed(self, text):
        for i in range(self.installed_list.count()):
            item = self.installed_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def handle_import_drop(self, path):
        p = Path(path)
        if p.is_dir():
            self.install_pack(p, {"name": p.stem}, original_name=p.stem)
        elif p.is_file() and (p.suffix.lower() == '.zip' or p.suffix == ''):
            self.install_pack(p, {"name": p.stem}, original_name=p.stem)
        else:
            show_warning(self, "Invalid", "Only folders or ZIP files are supported.")

    def refresh_installed(self):
        self.scan_local()
        self.installed_list.clear()
        for info in self.state.get("known", []):
            item = QListWidgetItem(info["store_name"])
            item.setData(Qt.UserRole, info)
            self.installed_list.addItem(item)
        self.filter_installed(self.installed_search_bar.text())

    def on_installed_item_selected(self, item):
        info = item.data(Qt.UserRole)
        folder = Path(info["path"])
        self.installed_path_label.setText(str(folder))
        self.installed_open_btn.setProperty("folder_path", str(folder))

    def delete_selected(self):
        item = self.installed_list.currentItem()
        if not item:
            return
        info = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete", f"Delete {info['store_name']}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            shutil.rmtree(info["path"], ignore_errors=True)
            self.state["known"].remove(info)
            save_state(self.state)
            self.refresh_all()
            self.load_store()

    def safe_wipe(self):
        reply = QMessageBox.question(self, "Safe Wipe", "Remove ALL installed packs?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for info in list(self.state["known"]):
                shutil.rmtree(info["path"], ignore_errors=True)
            self.state["known"] = []
            save_state(self.state)
            self.refresh_all()
            self.load_store()

    # ---------------- PERSONA EXPLORER TAB ----------------
    def build_capes(self):
        layout = QVBoxLayout(self.capes_tab)
        search_layout = QHBoxLayout()
        self.cape_search_bar = QLineEdit()
        self.cape_search_bar.setPlaceholderText("Search persona items...")
        self.cape_search_bar.textChanged.connect(self.filter_capes)
        search_layout.addWidget(self.cape_search_bar)
        layout.addLayout(search_layout)
        btn_row = QHBoxLayout()
        refresh = SoundButton("Refresh", self.hover_sound, self.click_sound)
        refresh.clicked.connect(self.refresh_capes)
        btn_row.addWidget(refresh)
        wipe = SoundButton("Safe Wipe", self.hover_sound, self.click_sound)
        wipe.clicked.connect(self.safe_wipe_capes)
        btn_row.addWidget(wipe)
        delete_btn = SoundButton("Delete", self.hover_sound, self.click_sound)
        delete_btn.clicked.connect(self.delete_cape_selected)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.cape_import_drop = DragDropWidget("Drop persona pack folder or ZIP (or extensionless file) here", folder_mode=True, allow_zip=True, callback=self.handle_cape_import_drop)
        layout.addWidget(self.cape_import_drop)
        self.cape_list = QListWidget()
        self.cape_list.itemClicked.connect(self.on_cape_item_selected)
        layout.addWidget(self.cape_list)

        self.cape_path_label = QLabel("")
        self.cape_path_label.setStyleSheet("color: #aaa; font-size: 11px; padding: 4px;")
        self.cape_path_label.setWordWrap(True)
        layout.addWidget(self.cape_path_label, alignment=Qt.AlignCenter)

        self.cape_open_btn = SoundButton("Open Folder", self.hover_sound, self.click_sound)
        self.cape_open_btn.clicked.connect(self.open_selected_folder)
        layout.addWidget(self.cape_open_btn, alignment=Qt.AlignCenter)

        self.refresh_capes()

    def filter_capes(self, text):
        for i in range(self.cape_list.count()):
            item = self.cape_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def handle_cape_import_drop(self, path):
        p = Path(path)
        if p.is_dir():
            self.install_pack(p, {"name": p.stem}, original_name=p.stem, target_dir=PERSONA_DIR)
        elif p.is_file() and (p.suffix.lower() == '.zip' or p.suffix == ''):
            self.install_pack(p, {"name": p.stem}, original_name=p.stem, target_dir=PERSONA_DIR)
        else:
            show_warning(self, "Invalid", "Only folders or ZIP files (or extensionless) are supported.")

    def refresh_capes(self):
        self.scan_capes()
        self.cape_list.clear()
        for info in self.state.get("capes", []):
            item = QListWidgetItem(info["store_name"])
            item.setData(Qt.UserRole, info)
            self.cape_list.addItem(item)
        self.filter_capes(self.cape_search_bar.text())

    def on_cape_item_selected(self, item):
        info = item.data(Qt.UserRole)
        folder = Path(info["path"])
        self.cape_path_label.setText(str(folder))
        self.cape_open_btn.setProperty("folder_path", str(folder))

    def delete_cape_selected(self):
        item = self.cape_list.currentItem()
        if not item:
            return
        info = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete", f"Delete {info['store_name']}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            shutil.rmtree(info["path"], ignore_errors=True)
            self.state["capes"].remove(info)
            save_state(self.state)
            self.refresh_all()

    def safe_wipe_capes(self):
        reply = QMessageBox.question(self, "Safe Wipe", "Remove ALL installed persona items?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for info in list(self.state["capes"]):
                shutil.rmtree(info["path"], ignore_errors=True)
            self.state["capes"] = []
            save_state(self.state)
            self.refresh_all()

    def open_selected_folder(self):
        btn = self.sender()
        if btn and btn.property("folder_path"):
            path = btn.property("folder_path")
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def refresh_all(self):
        self.refresh_installed()
        self.refresh_capes()
        if hasattr(self, 'home_tab') and isinstance(self.home_tab, HomeTab):
            self.home_tab.update_counts()

    # ---------------- PORTER ----------------
    def build_porter(self):
        layout = QVBoxLayout(self.porter_tab)
        self.porter_title = QLabel("Porter -- Copy -> Encrypt -> Import")
        self.porter_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        self.porter_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.porter_title)
        self.porter_folder_btn = SoundButton("Select Folder", self.hover_sound, self.click_sound)
        self.porter_folder_btn.clicked.connect(self.select_porter_folder)
        layout.addWidget(self.porter_folder_btn)
        self.manifest_dropdown = QComboBox()
        self.manifest_dropdown.addItems(list(MANIFEST_OPTIONS.keys()))
        layout.addWidget(self.manifest_dropdown)
        self.porter_drop = DragDropWidget("Drop skin pack folder or ZIP here", folder_mode=True, allow_zip=True, callback=self.set_porter_folder_from_drop)
        layout.addWidget(self.porter_drop)
        self.porter_progress = QProgressBar()
        layout.addWidget(self.porter_progress)
        self.porter_run_btn = SoundButton("Run Porter", self.hover_sound, self.click_sound)
        self.porter_run_btn.clicked.connect(self.run_porter)
        layout.addWidget(self.porter_run_btn)
        self.porter_status = QTextEdit()
        self.porter_status.setReadOnly(True)
        layout.addWidget(self.porter_status)

    def select_porter_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Skin Pack Folder")
        if folder:
            self.porter_folder = folder
            self.porter_status.append(f"Selected: {folder}")

    def set_porter_folder_from_drop(self, path):
        self.porter_folder = path
        self.porter_status.append(f"Selected: {path}")

    def run_porter(self):
        if self.porter_running:
            show_warning(self, "Porter Running", "Already processing.")
            return
        if not self.porter_folder:
            show_warning(self, "Porter", "Select a folder or zip first")
            return
        self.porter_running = True
        self.porter_progress.setValue(0)
        extracted_temp = None
        try:
            original_path = Path(self.porter_folder)
            if original_path.is_file() and (original_path.suffix.lower() == '.zip' or original_path.suffix == ''):
                self.porter_status.append("Extracting ZIP...")
                zip_path = original_path
                if original_path.suffix == '':
                    zip_path = original_path.with_suffix('.zip')
                    shutil.copy2(original_path, zip_path)
                extracted_temp = Path(tempfile.gettempdir()) / f"porter_zip_{int(time.time())}"
                extracted_temp.mkdir(exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(extracted_temp)
                pack_folder = None
                for root, dirs, files in os.walk(extracted_temp):
                    if "manifest.json" in files:
                        pack_folder = Path(root)
                        break
                if not pack_folder:
                    raise Exception("No manifest.json in zip")
                folder = str(pack_folder)
            else:
                folder = str(original_path)
            choice = self.manifest_dropdown.currentText()
            self.porter_status.append("Copying pack...")
            temp_copy = copy_pack_first(folder)
            self.porter_progress.setValue(25)
            self.porter_status.append("Setting manifest...")
            setup_porter(temp_copy, choice)
            self.porter_progress.setValue(50)
            self.porter_status.append("Encrypting...")
            tool_porter(temp_copy)
            self.porter_progress.setValue(75)
            self.porter_status.append("Checking for existing packs...")
            self.remove_existing_manifest_pack(temp_copy)
            self.porter_status.append("Importing...")
            import_to_minecraft_porter(temp_copy)
            self.porter_progress.setValue(100)
            self.porter_status.append("Done")
        except Exception as e:
            QMessageBox.critical(self, "Porter Error", str(e))
            self.porter_status.append(f"Error: {e}")
        finally:
            if extracted_temp and extracted_temp.exists():
                shutil.rmtree(extracted_temp, ignore_errors=True)
            self.porter_running = False

    def uninstall_pack(self, pack):
        name = pack.get("name")
        existing = next((i for i in self.state["known"] if i["store_name"] == name), None)
        if not existing:
            return
        shutil.rmtree(existing["path"], ignore_errors=True)
        self.state["known"].remove(existing)
        save_state(self.state)
        self.refresh_all()
        self.load_store()

    def remove_existing_manifest_pack(self, temp_folder):
        manifest = Path(temp_folder) / "manifest.json"
        if not manifest.exists():
            return
        try:
            uuid, _ = read_manifest(manifest)
        except:
            return
        existing = next((i for i in self.state["known"] if i["uuid"] == uuid), None)
        if existing:
            shutil.rmtree(existing["path"], ignore_errors=True)
            self.state["known"].remove(existing)
            save_state(self.state)
            self.refresh_all()

    # ---------------- THEME APPLICATION ----------------
    def apply_theme(self, theme):
        self.current_theme = theme
        app = QApplication.instance()
        if theme == "light":
            stylesheet = LIGHT_STYLESHEET
            text_color = "#222"
            dim_color = "#555"
            header_btn_style = "QPushButton { background: transparent; border: 1px solid #aaa; border-radius: 6px; color: #222; padding: 5px 10px; } QPushButton:hover { background: rgba(0,0,0,10); }"
            combo_style = "QComboBox { background: rgba(230,230,230,200); border: 1px solid #bbb; border-radius: 6px; padding: 4px 8px; color: #222; } QComboBox::drop-down { border: none; }"
            dd_style = "QLabel { border: 2px dashed rgba(0,0,0,80); border-radius: 10px; color: #555; }"
            card_bg = "rgba(0,0,0,10)"
            card_border = "rgba(0,0,0,30)"
            card_name_color = "#222"
            install_btn_style = "QPushButton { background: rgba(0,0,0,15); border: 1px solid rgba(0,0,0,100); border-radius: 6px; color: #222; } QPushButton:hover { background: rgba(0,0,0,30); }"
            remove_btn_style = "QPushButton { background: rgba(0,0,0,10); border: 1px solid rgba(0,0,0,60); border-radius: 6px; color: #222; } QPushButton:hover { background: rgba(0,0,0,25); }"
        else:
            stylesheet = DARK_STYLESHEET
            text_color = "#e0e0e0"
            dim_color = "#aaa"
            header_btn_style = "QPushButton { background: transparent; border: 1px solid #555; border-radius: 6px; color: #e0e0e0; padding: 5px 10px; } QPushButton:hover { background: rgba(255,255,255,10); }"
            combo_style = "QComboBox { background: rgba(40,40,40,200); border: 1px solid #555; border-radius: 6px; padding: 4px 8px; color: #e0e0e0; } QComboBox::drop-down { border: none; }"
            dd_style = "QLabel { border: 2px dashed rgba(255,255,255,80); border-radius: 10px; color: #ccc; }"
            card_bg = "rgba(255,255,255,15)"
            card_border = "rgba(255,255,255,40)"
            card_name_color = "#e0e0e0"
            install_btn_style = "QPushButton { background: rgba(255,255,255,40); border: 1px solid rgba(255,255,255,100); border-radius: 6px; color: white; } QPushButton:hover { background: rgba(255,255,255,100); }"
            remove_btn_style = "QPushButton { background: rgba(255,255,255,20); border: 1px solid rgba(255,255,255,80); border-radius: 6px; color: white; } QPushButton:hover { background: rgba(255,255,255,60); }"

        app.setStyleSheet(stylesheet)
        self.background.set_theme(theme)

        # Header elements
        self.app_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {text_color}; margin-left: 8px;")
        self.version_combo.setStyleSheet(combo_style)
        self.launch_btn.setStyleSheet(header_btn_style)
        self.restart_btn.setStyleSheet(header_btn_style)
        self.sound_btn.setStyleSheet(header_btn_style)
        self.credits_btn.setStyleSheet(header_btn_style)

        # Drag‑drop widgets
        for dd in DragDropWidget.instances:
            dd.setStyleSheet(dd_style)

        # Store cards
        for card in StoreCard.instances:
            card.setStyleSheet(f"QWidget {{ background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; }}")
            card.name_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {card_name_color}; border: none;")
            card.badge.setStyleSheet(f"color: {text_color}; font-size: 11px;")
            card.install_btn.setStyleSheet(install_btn_style)
            if card.remove_btn:
                card.remove_btn.setStyleSheet(remove_btn_style)

        # Sub‑tabs
        if hasattr(self, 'home_tab'):
            self.home_tab.apply_theme(theme)
        if hasattr(self, 'merger_tab'):
            self.merger_tab.apply_theme(theme)
        if hasattr(self, 'porter_title'):
            self.porter_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color};")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background.setGeometry(self.rect())

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

def import_to_minecraft_porter(temp_path):
    manifest = None
    for root, dirs, files in os.walk(temp_path):
        if "manifest.json" in files:
            manifest = Path(root) / "manifest.json"
            break
    if not manifest:
        raise Exception("manifest.json not found after porter")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    uuid = data["header"]["uuid"]
    dest_folder = SKIN_PACK_DIR / uuid
    if dest_folder.exists():
        shutil.rmtree(dest_folder, ignore_errors=True)
    dest_folder.mkdir(parents=True, exist_ok=True)
    pack_root = manifest.parent
    for item in pack_root.iterdir():
        shutil.move(str(item), str(dest_folder / item.name))
    shutil.rmtree(temp_path, ignore_errors=True)

def copy_pack_first(folder):
    temp_root = os.path.join(tempfile.gettempdir(), "porter_temp")
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root, ignore_errors=True)
    os.makedirs(temp_root, exist_ok=True)
    new_name = f"{os.path.basename(folder)}_PORTED"
    temp_dest = os.path.join(temp_root, new_name)
    shutil.copytree(folder, temp_dest)
    return temp_dest

# ---------------- RUN ----------------
if __name__ == "__main__":
    myappid = 'ecliptix.melancholy.1.1.5'
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