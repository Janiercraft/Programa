import os
import json
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

# Configuración principal
download_dir = os.path.join(os.path.dirname(__file__), "updates")
version_file = os.path.join(os.path.dirname(__file__), "version.json")

class AutoUpdater(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)
        self.status_label = Label(text="Listo para descargar.")
        self.download_btn = Button(text="Descargar EXE")
        self.download_btn.bind(on_release=self.download_from_json)
        self.add_widget(self.status_label)
        self.add_widget(self.download_btn)

    def download_from_json(self, *args):
        # Crear carpeta de descargas
        os.makedirs(download_dir, exist_ok=True)
        self.status_label.text = "Leyendo version.json..."

        # Leer URL del JSON
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            url = data.get('url')
            if not url:
                raise ValueError("'url' no encontrado en version.json")
        except Exception as e:
            self.status_label.text = f"Error leyendo version.json: {e}"
            return

        # Nombre de archivo destino
        filename = os.path.basename(url)
        dest_path = os.path.join(download_dir, filename)
        self.status_label.text = f"Descargando {filename}..."

        # Descargar el archivo
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            self.status_label.text = f"Error al descargar: {e}"
            return

        # Descarga completada
        abs_path = os.path.abspath(dest_path)
        self.status_label.text = f"Descargado en: {abs_path}"

class AutoUpdaterApp(App):
    def build(self):
        return AutoUpdater()

if __name__ == "__main__":
    AutoUpdaterApp().run()
