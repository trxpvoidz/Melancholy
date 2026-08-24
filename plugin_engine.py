import sys, os, json, importlib.util
from pathlib import Path

SETTINGS_FILE = Path(os.getenv("APPDATA")) / "Melancholy" / "settings.json"
# Plugins are stored in AppData – always writable, persists across updates
PLUGINS_DIR = Path(os.getenv("APPDATA")) / "Melancholy" / "plugins"

_registry = {}   # name -> unregister callable

def _load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except:
        return {}

def _save_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))

def ensure_plugins_dir():
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

def get_available_plugins():
    """Return a dict of {name: path} for every .py file in the plugins folder."""
    ensure_plugins_dir()
    return {p.stem: p for p in PLUGINS_DIR.glob("*.py")}

def is_plugin_enabled(name):
    settings = _load_settings()
    enabled_list = settings.get("enabled_plugins", [])
    return name in enabled_list

def set_plugin_enabled_state(name, enabled):
    """Save the desired enabled state, without loading/unloading."""
    settings = _load_settings()
    enabled_list = settings.get("enabled_plugins", [])
    if enabled and name not in enabled_list:
        enabled_list.append(name)
    elif not enabled and name in enabled_list:
        enabled_list.remove(name)
    settings["enabled_plugins"] = enabled_list
    _save_settings(settings)

def load_plugin(name, app):
    """Load and register a single plugin immediately."""
    plugins = get_available_plugins()
    if name not in plugins:
        print(f"Plugin {name} not found")
        return

    path = plugins[name]
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'register'):
            result = mod.register(app)
            if callable(result):
                _registry[name] = result
            elif isinstance(result, dict) and 'unregister' in result:
                _registry[name] = result['unregister']
            else:
                _registry[name] = None
        print(f"Loaded plugin: {name}")
    except Exception as e:
        print(f"Failed to load plugin {name}: {e}")

def unload_plugin(name, app):
    """Unregister a plugin immediately if it has an unregister callback."""
    if name in _registry and callable(_registry[name]):
        try:
            _registry[name](app)
        except Exception as e:
            print(f"Error unloading plugin {name}: {e}")
    if name in _registry:
        del _registry[name]

def load_plugins(app):
    """Called at startup – loads all enabled plugins."""
    ensure_plugins_dir()
    plugins = get_available_plugins()
    for name in plugins:
        if is_plugin_enabled(name):
            load_plugin(name, app)

def reload_all_plugins(app):
    """Unload all currently loaded plugins, then load enabled ones again."""
    for name in list(_registry.keys()):
        unload_plugin(name, app)
    plugins = get_available_plugins()
    for name in plugins:
        if is_plugin_enabled(name):
            load_plugin(name, app)