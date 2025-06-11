import sys
import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock

import actualizador  # tu updater.py

class UpdateApp(App):
    def build(self):
        # Un widget vacío; la ventana servirá para mostrar popups del updater
        return Widget()

    def on_start(self):
        # Arrancamos el updater tras 0.1 s (para que la ventana ya exista)
        Clock.schedule_once(lambda dt: actualizador.check_for_updates(), 0.1)

if __name__ == "__main__":
    UpdateApp().run()