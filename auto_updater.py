import os
import json
import threading
import requests
import subprocess
from kivy.app import App
from kivy.clock import mainthread, Clock
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label

# CONFIGURACIÓN
VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "updates")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/Janiercraft/Programa/main/version.json"
LOCAL_EXE = os.path.join(os.path.dirname(__file__), "dist", "Calculadora R.Prestige.exe")

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
        self._set_status("Preparando rollback...")
        # Renombrar el exe actual a .old
        old_path = LOCAL_EXE + ".old"
        try:
            if os.path.isfile(LOCAL_EXE):
                os.replace(LOCAL_EXE, old_path)
        except Exception as e:
            self._set_status(f"Error preparando rollback: {e}")
            self._launch_local(delay=1)
            return

        self._set_status("Descargando actualización...")
        # Obtener URL de descarga
        try:
            r = requests.get(REMOTE_VERSION_URL, timeout=10)
            r.raise_for_status()
            url = r.json().get('url', '')
            if not url:
                raise ValueError("URL no encontrada")
        except Exception as e:
            self._set_status(f"Error al obtener URL: {e}")
            # rollback
            if os.path.isfile(old_path): os.replace(old_path, LOCAL_EXE)
            self._launch_local(delay=1)
            return

        # Descargar
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        filename = os.path.basename(url)
        dest = os.path.join(DOWNLOAD_DIR, filename)
        try:
            with requests.get(url, stream=True, timeout=10) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get('content-length', 0))
                downloaded = 0
                with open(dest, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pct = int(downloaded * 100 / total) if total else 0
                            self._set_progress(pct)
        except Exception as e:
            self._set_status(f"Error descarga: {e}")
            # rollback
            if os.path.isfile(old_path): os.replace(old_path, LOCAL_EXE)
            self._launch_local(delay=1)
            return

        self._set_status("Descarga completada. Iniciando nueva versión...")
        subprocess.Popen([dest])
        Clock.schedule_once(lambda dt: App.get_running_app().stop(), 1)

    def _launch_local(self, delay=0):
        if os.path.isfile(LOCAL_EXE):
            subprocess.Popen([LOCAL_EXE])
        if delay > 0:
            Clock.schedule_once(lambda dt: App.get_running_app().stop(), delay)
        else:
            self._stop_app()

    @mainthread
    def _set_progress(self, value):
        self.progress = value

    @mainthread
    def _set_status(self, text):
        self.status = text

    @mainthread
    def _stop_app(self):
        App.get_running_app().stop()

    @mainthread
    def _update_progress(self, instance, value):
        self.pb.value = value

    @mainthread
    def _update_status(self, instance, value):
        self.lbl_status.text = value

class AutoUpdaterApp(App):
    def build(self):
        return AutoUpdater()

if __name__ == '__main__':
    AutoUpdaterApp().run()
