"""
Melancholy Skin Pack Manager – main window
Copyright (c) 2026 TrxpVoidz (Ecliptix)
All rights reserved.
"""

import sys, os, json, zipfile, shutil, ctypes, time, subprocess
from io import BytesIO
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QMessageBox, QProgressBar, QTextEdit, QTabWidget,
    QFileDialog, QListWidget, QListWidgetItem, QComboBox,
    QSizePolicy, QLineEdit, QPlainTextEdit, QCheckBox,
    QDialog
)
from PySide6.QtGui import (
    QPixmap, QIcon, QDesktopServices, QPainter, QColor,
    QLinearGradient, QPalette, QFont, QFontDatabase
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QUrl, QPropertyAnimation, QEasingCurve, QTimer, QEvent,
    QSize
)
from PySide6.QtMultimedia import QSoundEffect

from plugin_engine import load_plugins as load_plugins_engine

from main import (
    settings, USE_UWP, SKIN_PACK_DIR, PERSONA_DIR, CACHE_DIR,
    LEGACY_VAULT_DIR, STATE_FILE, LEGACY_STATE_FILE, SETTINGS_FILE,
    load_state, save_state, load_legacy_state, save_legacy_state,
    find_manifest, read_manifest, get_pack_display_name,
    resource_path, show_warning,
    DARK_STYLESHEET, LIGHT_STYLESHEET,
    http_session, STORE_ITEMS_PER_PAGE,
    BackgroundWidget, SoundButton, DragDropWidget, StoreCard,
    LoadingScreen, StorePresetDialog,
    StoreLoader, DownloadWorker, ThumbnailLoader, MergerWorker,
    HomeTab, SettingsTab, MergerTab,
    MANIFEST_OPTIONS, setup_porter, tool_porter, import_to_minecraft_porter, copy_pack_first,
    DISCORD_INVITE, GITHUB_URL, MARKETPLACE_URL, get_mc_paths,
    get_pack_head_icon, IconGenerator
)

try:
    import psutil
except ImportError:
    psutil = None


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
        self.store_packs = []
        self.filtered_packs = []
        self.current_store_page = 1
        self.items_per_page = STORE_ITEMS_PER_PAGE

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
        self.credits_btn = SoundButton("Credits", self.hover_sound, self.click_sound)
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

        self.pack_icons_cache = {}   # <-- MUST be before build_installed
        self.show_icons = settings.get("show_icons", True)

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

        self.load_plugins()

    # --- SOUND MANAGEMENT ---
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

    # --- DISCORD RICH PRESENCE ---
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
            if hasattr(self, '_mc_check_timer'):
                self._mc_check_timer.stop()

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

    # --- MINECRAFT LAUNCH / RESTART ---
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
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Minecraft:\n{e}")

    def _set_mc_presence(self):
        self.mc_launched = True
        self._mc_ignore_checks = 2
        if hasattr(self, '_mc_check_timer'):
            self._mc_check_timer.start(10000)
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

    # --- IDLE MODE ---
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

    # --- STANDARD METHODS ---
    def show_credits(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Credits")
        msg.setText("Melancholy Skin Pack Manager\n\nCreated by TrxpVoidz (Ecliptix)\nSpecial Thanks to a6wwp")
        msg.exec()

    def load_plugins(self):
        from plugin_engine import load_plugins
        load_plugins(self)

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
        # Convert extensionless files into folders (same as scan_capes)
        for item in SKIN_PACK_DIR.iterdir():
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

    # --- STORE BUILD ---
    def build_store(self):
        layout = QVBoxLayout(self.store_tab)

        preset_layout = QHBoxLayout()
        self.store_label = QLabel("Store:")
        preset_layout.addWidget(self.store_label)
        self.store_presets_combo = QComboBox()
        self.store_presets_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.store_presets_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.store_presets_combo)

        self.add_store_btn = SoundButton("Add Store", self.hover_sound, self.click_sound)
        self.add_store_btn.clicked.connect(self.add_store_preset)
        preset_layout.addWidget(self.add_store_btn)

        self.edit_store_btn = SoundButton("Edit", self.hover_sound, self.click_sound)
        self.edit_store_btn.clicked.connect(self.edit_store_preset)
        preset_layout.addWidget(self.edit_store_btn)

        self.remove_store_btn = SoundButton("Remove", self.hover_sound, self.click_sound)
        self.remove_store_btn.clicked.connect(self.remove_store_preset)
        preset_layout.addWidget(self.remove_store_btn)
        layout.addLayout(preset_layout)

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

        self.pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(self.pagination_widget)
        pagination_layout.setContentsMargins(0, 5, 0, 5)

        self.prev_btn = SoundButton("◀ Previous", self.hover_sound, self.click_sound)
        self.prev_btn.clicked.connect(self.prev_store_page)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setStyleSheet("color: #ccc; font-size: 13px;")
        pagination_layout.addWidget(self.page_label)

        self.next_btn = SoundButton("Next ▶", self.hover_sound, self.click_sound)
        self.next_btn.clicked.connect(self.next_store_page)
        pagination_layout.addWidget(self.next_btn)
        layout.addWidget(self.pagination_widget)

        self.progress = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(100)
        layout.addWidget(self.progress)
        layout.addWidget(self.log)

        self.store_cards = []
        self.refresh_presets_combo()

    def refresh_presets_combo(self):
        self.store_presets_combo.blockSignals(True)
        self.store_presets_combo.clear()
        presets = settings.get("store_presets", {"Official Store": MARKETPLACE_URL})
        for name in presets.keys():
            self.store_presets_combo.addItem(name)
        active = settings.get("active_store_preset", "Official Store")
        idx = self.store_presets_combo.findText(active)
        if idx >= 0:
            self.store_presets_combo.setCurrentIndex(idx)
        self.store_presets_combo.blockSignals(False)

    def on_preset_changed(self, index):
        name = self.store_presets_combo.currentText()
        if name:
            settings["active_store_preset"] = name
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
            self.load_store()

    def add_store_preset(self):
        dialog = StorePresetDialog(self)
        dialog.setStyleSheet(QApplication.instance().styleSheet())
        if dialog.exec() == QDialog.Accepted:
            name, url = dialog.get_data()
            if not name or not url:
                QMessageBox.warning(self, "Invalid", "Name and URL required.")
                return
            presets = settings.get("store_presets", {})
            if name in presets:
                reply = QMessageBox.question(self, "Overwrite",
                                             f"Preset '{name}' already exists. Overwrite?")
                if reply != QMessageBox.Yes:
                    return
            presets[name] = url
            settings["store_presets"] = presets
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
            self.refresh_presets_combo()

    def edit_store_preset(self):
        current = self.store_presets_combo.currentText()
        if not current:
            QMessageBox.information(self, "No Selection", "Select a store preset to edit.")
            return
        presets = settings.get("store_presets", {})
        if current not in presets:
            return
        url = presets[current]
        dialog = StorePresetDialog(self, preset_name=current, preset_url=url)
        dialog.setStyleSheet(QApplication.instance().styleSheet())
        if dialog.exec() == QDialog.Accepted:
            new_name, new_url = dialog.get_data()
            if not new_name or not new_url:
                return
            del presets[current]
            presets[new_name] = new_url
            if settings.get("active_store_preset") == current:
                settings["active_store_preset"] = new_name
            settings["store_presets"] = presets
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
            self.refresh_presets_combo()

    def remove_store_preset(self):
        current = self.store_presets_combo.currentText()
        presets = settings.get("store_presets", {})
        if len(presets) <= 1:
            QMessageBox.information(self, "Cannot Remove", "You must keep at least one store preset.")
            return
        reply = QMessageBox.question(self, "Remove Preset",
                                     f"Remove store preset '{current}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del presets[current]
            settings["store_presets"] = presets
            if settings.get("active_store_preset") == current:
                first = next(iter(presets.keys()))
                settings["active_store_preset"] = first
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
            self.refresh_presets_combo()
            self.load_store()

    def filter_store(self, text):
        if not hasattr(self, 'store_packs'):
            return
        if text.strip() == "":
            self.filtered_packs = self.store_packs.copy()
        else:
            lower = text.lower()
            self.filtered_packs = [p for p in self.store_packs if lower in p.get("name", "").lower()]
        self.current_store_page = 1
        self.render_store_page(self.current_store_page)

    def load_store(self):
        presets = settings.get("store_presets", {})
        active_name = settings.get("active_store_preset", "Official Store")
        url = presets.get(active_name, MARKETPLACE_URL)
        self.store_loader = StoreLoader(url)
        self.store_loader.finished.connect(self.populate_store)
        self.store_loader.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.store_loader.start()

    def populate_store(self, packs):
        self.store_packs = packs
        search_text = self.search_bar.text().strip()
        if search_text:
            lower = search_text.lower()
            self.filtered_packs = [p for p in packs if lower in p.get("name", "").lower()]
        else:
            self.filtered_packs = packs.copy()
        self.current_store_page = 1
        self.render_store_page(self.current_store_page)

    def render_store_page(self, page):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        self.store_cards.clear()
        StoreCard.instances.clear()

        if not self.filtered_packs:
            self.page_label.setText("No items to show")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        total_items = len(self.filtered_packs)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page

        page = max(1, min(page, total_pages))
        self.current_store_page = page

        start_idx = (page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        page_packs = self.filtered_packs[start_idx:end_idx]

        row = col = 0
        for pack in page_packs:
            card = StoreCard(pack, self.state, self.start_download, self.uninstall_pack, self.hover_sound, self.click_sound)
            self.grid.addWidget(card, row, col)
            self.store_cards.append(card)
            col += 1
            if col == 4:
                col = 0
                row += 1

        self.page_label.setText(f"Page {page} of {total_pages}  ·  showing {start_idx+1}–{end_idx} of {total_items}")

        self.prev_btn.setEnabled(page > 1)
        self.next_btn.setEnabled(page < total_pages)

        self.apply_theme(self.current_theme)

    def prev_store_page(self):
        if self.current_store_page > 1:
            self.render_store_page(self.current_store_page - 1)

    def next_store_page(self):
        total_pages = (len(self.filtered_packs) + self.items_per_page - 1) // self.items_per_page
        if self.current_store_page < total_pages:
            self.render_store_page(self.current_store_page + 1)

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

    # --- INSTALLED TAB ---
    def build_installed(self):
        layout = QVBoxLayout(self.installed_tab)
        search_layout = QHBoxLayout()
        self.installed_search_bar = QLineEdit()
        self.installed_search_bar.setPlaceholderText("Search installed...")
        self.installed_search_bar.textChanged.connect(self.filter_installed)
        search_layout.addWidget(self.installed_search_bar)
        layout.addLayout(search_layout)
        btn_row = QHBoxLayout()
        self.installed_refresh_btn = SoundButton("Refresh", self.hover_sound, self.click_sound)
        self.installed_refresh_btn.clicked.connect(self.refresh_installed)
        btn_row.addWidget(self.installed_refresh_btn)
        self.installed_wipe_btn = SoundButton("Safe Wipe", self.hover_sound, self.click_sound)
        self.installed_wipe_btn.clicked.connect(self.safe_wipe)
        btn_row.addWidget(self.installed_wipe_btn)
        self.installed_delete_btn = SoundButton("Delete", self.hover_sound, self.click_sound)
        self.installed_delete_btn.clicked.connect(self.delete_selected)
        btn_row.addWidget(self.installed_delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.import_drop = DragDropWidget("Drop skin pack folder or ZIP here", folder_mode=True, allow_zip=True, callback=self.handle_import_drop)
        layout.addWidget(self.import_drop)
        self.installed_list = QListWidget()
        self.installed_list.setIconSize(QSize(64, 64))
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
        # If icons are disabled, just show the list without any icon generation
        if not self.show_icons:
            self.installed_list.clear()
            for info in self.state.get("known", []):
                item = QListWidgetItem(info["store_name"])
                item.setData(Qt.UserRole, info)
                item.setIcon(QIcon())
                self.installed_list.addItem(item)
            self.filter_installed(self.installed_search_bar.text())
            return

        # Otherwise, normal refresh with async icon generation
        self.scan_local()
        self.installed_list.clear()
        tasks = []
        placeholder_icon = QIcon()

        for info in self.state.get("known", []):
            item = QListWidgetItem(info["store_name"])
            item.setData(Qt.UserRole, info)
            uuid = info["uuid"]

            if uuid in self.pack_icons_cache:
                item.setIcon(self.pack_icons_cache[uuid])
            else:
                item.setIcon(placeholder_icon)
                tasks.append((uuid, Path(info["path"])))

            self.installed_list.addItem(item)

        if tasks:
            if hasattr(self, 'icon_worker') and self.icon_worker.isRunning():
                self.icon_worker.quit()
                self.icon_worker.wait()
            self.icon_worker = IconGenerator(tasks)
            self.icon_worker.icon_ready.connect(self.on_icon_ready)
            self.icon_worker.start()

        self.filter_installed(self.installed_search_bar.text())

    def on_icon_ready(self, uuid, pix):
        if pix and not pix.isNull():
            icon_pix = pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.pack_icons_cache[uuid] = QIcon(icon_pix)
        else:
            # Magenta fallback
            from PIL import Image, ImageDraw
            from io import BytesIO
            fallback = Image.new('RGBA', (8, 8), (255, 0, 255, 255))
            fallback = fallback.resize((64, 64), Image.NEAREST)
            buf = BytesIO()
            fallback.save(buf, 'PNG')
            fpix = QPixmap()
            fpix.loadFromData(buf.getvalue())
            self.pack_icons_cache[uuid] = QIcon(fpix)

        # Update the corresponding list item
        for i in range(self.installed_list.count()):
            item = self.installed_list.item(i)
            info = item.data(Qt.UserRole)
            if info['uuid'] == uuid:
                item.setIcon(self.pack_icons_cache[uuid])
                break

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

    # --- PERSONA EXPLORER TAB ---
    def build_capes(self):
        layout = QVBoxLayout(self.capes_tab)
        search_layout = QHBoxLayout()
        self.cape_search_bar = QLineEdit()
        self.cape_search_bar.setPlaceholderText("Search persona items...")
        self.cape_search_bar.textChanged.connect(self.filter_capes)
        search_layout.addWidget(self.cape_search_bar)
        layout.addLayout(search_layout)
        btn_row = QHBoxLayout()
        self.cape_refresh_btn = SoundButton("Refresh", self.hover_sound, self.click_sound)
        self.cape_refresh_btn.clicked.connect(self.refresh_capes)
        btn_row.addWidget(self.cape_refresh_btn)
        self.cape_wipe_btn = SoundButton("Safe Wipe", self.hover_sound, self.click_sound)
        self.cape_wipe_btn.clicked.connect(self.safe_wipe_capes)
        btn_row.addWidget(self.cape_wipe_btn)
        self.cape_delete_btn = SoundButton("Delete", self.hover_sound, self.click_sound)
        self.cape_delete_btn.clicked.connect(self.delete_cape_selected)
        btn_row.addWidget(self.cape_delete_btn)
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
        else:
            if btn is self.installed_open_btn:
                path = str(SKIN_PACK_DIR)
            elif btn is self.cape_open_btn:
                path = str(PERSONA_DIR)
            else:
                return
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def refresh_all(self):
        self.refresh_installed()
        self.refresh_capes()
        if hasattr(self, 'home_tab') and isinstance(self.home_tab, HomeTab):
            self.home_tab.update_counts()

    # --- PORTER ---
    def build_porter(self):
        layout = QVBoxLayout(self.porter_tab)
        self.porter_title = QLabel("Porter -- Copy -> Encrypt -> Import")
        self.porter_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        self.porter_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.porter_title)
        self.porter_folder_btn = SoundButton("Select Folder", self.hover_sound, self.click_sound)
        self.porter_folder_btn.clicked.connect(self.select_porter_folder)
        layout.addWidget(self.porter_folder_btn)
        self.porter_manifest_dropdown = QComboBox()
        self.porter_manifest_dropdown.addItems(list(MANIFEST_OPTIONS.keys()))
        layout.addWidget(self.porter_manifest_dropdown)
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
            if original_path.is_file():
                porter_source_name = original_path.stem
            else:
                porter_source_name = original_path.name

            if original_path.is_file() and (original_path.suffix.lower() == '.zip' or original_path.suffix == ''):
                self.porter_status.append("Extracting ZIP...")
                zip_path = original_path
                if original_path.suffix == '':
                    zip_path = original_path.with_suffix('.zip')
                    shutil.copy2(original_path, zip_path)
                extracted_temp = CACHE_DIR / f"porter_zip_{int(time.time())}"
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
            choice = self.porter_manifest_dropdown.currentText()
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
            import_to_minecraft_porter(temp_copy, display_name=porter_source_name)
            self.scan_local()
            self.refresh_installed()
            self.scan_capes()
            self.refresh_capes()
            self.refresh_all()
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

    # --- THEME ---
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
            path_label_style = f"color: {dim_color}; font-size: 11px; padding: 4px;"
            page_label_style = f"color: {dim_color}; font-size: 13px;"
            log_style = "QTextEdit { background: rgba(0,0,0,5); color: #222; border: 1px solid #aaa; border-radius: 6px; }"
            plain_log_style = "QPlainTextEdit { background: rgba(0,0,0,5); color: #222; border: 1px solid #aaa; border-radius: 6px; }"
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
            path_label_style = f"color: {dim_color}; font-size: 11px; padding: 4px;"
            page_label_style = f"color: {dim_color}; font-size: 13px;"
            log_style = "QTextEdit { background: rgba(255,255,255,5); color: #e0e0e0; border: 1px solid #555; border-radius: 6px; }"
            plain_log_style = "QPlainTextEdit { background: rgba(255,255,255,5); color: #e0e0e0; border: 1px solid #555; border-radius: 6px; }"

        app.setStyleSheet(stylesheet)
        self.background.set_theme(theme)

        self.app_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {text_color}; margin-left: 8px;")
        self.version_combo.setStyleSheet(combo_style)
        self.launch_btn.setStyleSheet(header_btn_style)
        self.restart_btn.setStyleSheet(header_btn_style)
        self.sound_btn.setStyleSheet(header_btn_style)
        self.credits_btn.setStyleSheet(header_btn_style)

        self.store_label.setStyleSheet(f"color: {text_color};")
        self.store_presets_combo.setStyleSheet(combo_style)
        self.add_store_btn.setStyleSheet(header_btn_style)
        self.edit_store_btn.setStyleSheet(header_btn_style)
        self.remove_store_btn.setStyleSheet(header_btn_style)
        self.search_bar.setStyleSheet("")

        self.prev_btn.setStyleSheet(header_btn_style)
        self.next_btn.setStyleSheet(header_btn_style)
        self.page_label.setStyleSheet(page_label_style)

        self.installed_search_bar.setStyleSheet("")
        self.installed_refresh_btn.setStyleSheet(header_btn_style)
        self.installed_wipe_btn.setStyleSheet(header_btn_style)
        self.installed_delete_btn.setStyleSheet(header_btn_style)
        self.installed_path_label.setStyleSheet(path_label_style)
        self.installed_open_btn.setStyleSheet(header_btn_style)

        self.cape_search_bar.setStyleSheet("")
        self.cape_refresh_btn.setStyleSheet(header_btn_style)
        self.cape_wipe_btn.setStyleSheet(header_btn_style)
        self.cape_delete_btn.setStyleSheet(header_btn_style)
        self.cape_path_label.setStyleSheet(path_label_style)
        self.cape_open_btn.setStyleSheet(header_btn_style)

        self.porter_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {text_color};")
        self.porter_folder_btn.setStyleSheet(header_btn_style)
        self.porter_manifest_dropdown.setStyleSheet(combo_style)
        self.porter_run_btn.setStyleSheet(header_btn_style)

        self.log.setStyleSheet(log_style)
        self.porter_status.setStyleSheet(log_style)

        for dd in DragDropWidget.instances:
            dd.setStyleSheet(dd_style)

        for card in StoreCard.instances:
            card.setStyleSheet(f"QWidget {{ background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; }}")
            card.name_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {card_name_color}; border: none;")
            card.badge.setStyleSheet(f"color: {text_color}; font-size: 11px;")
            card.install_btn.setStyleSheet(install_btn_style)
            if card.remove_btn:
                card.remove_btn.setStyleSheet(remove_btn_style)

        if hasattr(self, 'home_tab'):
            self.home_tab.apply_theme(theme)
        if hasattr(self, 'merger_tab'):
            self.merger_tab.apply_theme(theme)
            if hasattr(self.merger_tab, 'log_output'):
                self.merger_tab.log_output.setStyleSheet(plain_log_style)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background.setGeometry(self.rect())

    # --- INSTALL PACK (shared) ---
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
                    self.pack_icons_cache.pop(new_uuid, None)   # <-- add this
                else:
                    self.state["capes"].remove(existing)
                    self.pack_icons_cache.pop(new_uuid, None)   # <-- add this

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