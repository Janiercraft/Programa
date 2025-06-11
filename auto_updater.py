import os
import json
import threading
import time
import requests
import subprocess
from pathlib import Path

from kivy.app import App
from kivy.clock import mainthread, Clock
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from Clases_y_Funciones.Clases.gestion_recursos import Recursos

# CONFIGURACIÓN
VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "updates")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/Janiercraft/Programa/main/version.json"
LOCAL_EXE = os.path.join(os.path.dirname(__file__), "dist", "Calculadora R.Prestige.exe")

# Ahora el timestamp irá dentro de la carpeta Recursos
TIMESTAMP_FILE = Recursos.ruta("last_check.json")

CHECK_INTERVAL = 3600  # segundos

# Verificar si debe ejecutarse el updater o lanzar app directamente
def should_run_updater():
    now = time.time()
    last = 0
    if os.path.isfile(TIMESTAMP_FILE):
        try:
            with open(TIMESTAMP_FILE, 'r', encoding='utf-8') as f:
                last = json.load(f).get('last', 0)
        except:
            last = 0

    if now - last < CHECK_INTERVAL:
        # … resto sin cambios …
        subprocess.Popen([LOCAL_EXE])
        return False

    # Actualizamos timestamp en Recursos/last_check.json
    try:
        with open(TIMESTAMP_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last': now}, f)
    except:
        pass
    return True

class AutoUpdater(BoxLayout):
    progress = NumericProperty(0)
    status = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.lbl_status = Label(text=self.status, size_hint_y=None, height=30)
        self.pb = ProgressBar(max=100, value=self.progress, size_hint_y=None, height=30)
        self.add_widget(self.lbl_status)
        self.add_widget(self.pb)
        self.bind(progress=self._update_progress)
        self.bind(status=self._update_status)
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        self._set_status("Buscando actualizaciones...")
        # Comprobar conectividad
        try:
            requests.head("https://raw.githubusercontent.com", timeout=5)
        except requests.RequestException:
            self._set_status("Sin internet. Abriendo aplicación...")
            self._launch_local(delay=1)
            return
        # Leer versiones
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                local = json.load(f).get('version', '')
            r = requests.get(REMOTE_VERSION_URL, timeout=10)
            r.raise_for_status()
            remote = r.json().get('version', '')
        except Exception as e:
            self._set_status(f"Error al comprobar: {e}")
            self._launch_local(delay=1)
            return

        if remote and local and remote != local:
            self.download_update()
        else:
            self._set_status("No hay actualizaciones. Abriendo calculadora...")
            self._launch_local(delay=1)

    def download_update(self):
        self._set_status("Preparando rollback…")
        old_path = LOCAL_EXE + ".old"
        try:
            if os.path.isfile(LOCAL_EXE):
                os.replace(LOCAL_EXE, old_path)
        except Exception as e:
            self._set_status(f"Error rollback: {e}")
            self._launch_local(delay=1)
            return

        self._set_status("Descargando actualización…")
        try:
            r = requests.get(REMOTE_VERSION_URL, timeout=10)
            r.raise_for_status()
            url = r.json().get('url', '')
            if not url:
                raise ValueError("URL no encontrada")
        except Exception as e:
            self._set_status(f"Error URL: {e}")
            # Restaurar backup
            if os.path.isfile(old_path):
                os.replace(old_path, LOCAL_EXE)
            self._launch_local(delay=1)
            return

        # Descargamos directamente en LOCAL_EXE
        try:
            with requests.get(url, stream=True, timeout=10) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get('content-length', 0))
                downloaded = 0
                with open(LOCAL_EXE, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pct = int(downloaded * 100 / total) if total else 0
                            self._set_progress(pct)
        except Exception as e:
            self._set_status(f"Error descarga: {e}")
            # Restaurar backup
            if os.path.isfile(old_path):
                os.replace(old_path, LOCAL_EXE)
            self._launch_local(delay=1)
            return

        # Arrancamos la nueva versión
        subprocess.Popen([LOCAL_EXE])

        # Borramos el respaldo antiguo
        try:
            if os.path.isfile(old_path):
                os.remove(old_path)
                self._set_status("Respaldo eliminado.")
        except:
            pass

        Clock.schedule_once(lambda dt: App.get_running_app().stop(), 1)
        
    def _launch_local(self, delay=0):
        if os.path.isfile(LOCAL_EXE): subprocess.Popen([LOCAL_EXE])
        if delay>0: Clock.schedule_once(lambda dt: App.get_running_app().stop(), delay)
        else: self._stop_app()

    @mainthread
    def _set_progress(self, v): self.progress = v
    @mainthread
    def _set_status(self, t): self.status = t
    @mainthread
    def _stop_app(self): App.get_running_app().stop()
    @mainthread
    def _update_progress(self, *_): self.pb.value = self.progress
    @mainthread
    def _update_status(self, *_): self.lbl_status.text = self.status

class AutoUpdaterApp(App):
    def build(self): return AutoUpdater()

if __name__ == '__main__':
    if should_run_updater():
        AutoUpdaterApp().run()
