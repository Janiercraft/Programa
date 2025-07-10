import sys
import shutil
from pathlib import Path

from kivy.config import Config
Config.set('kivy', 'input_exclude', 'wm_pen')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.core.window      import Window
from kivy.app              import App
from kivy.uix.screenmanager import ScreenManager, Screen

from Clases_y_Funciones.Clases.gestion_recursos import Recursos, RecursosExternos
from Clases_y_Funciones.Funciones.basesql         import init_local_db, init_local_tasas
from Clases_y_Funciones.Funciones.obtener_productos import obtener_datos_productos

from UX.Login               import LoginLayout
from UX.Calculadora         import CalculoScreen
from UX.Resultados          import ResultadosScreen
from UX.popup               import show_update_popup


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='login', **kwargs)
        self.add_widget(LoginLayout())


class CalculoScreenContainer(Screen):
    def __init__(self, **kwargs):
        super().__init__(name='calculo', **kwargs)
        self.calculo_screen = CalculoScreen()
        self.add_widget(self.calculo_screen)

    def on_pre_enter(self, *args):
        self.calculo_screen.widget.reset()


def extract_updater():
    """
    Copia updater.exe desde el bundle o desde los recursos de desarrollo
    hacia la carpeta externa 'Recursos' junto al ejecutable/script.
    """
    # carpeta destino junto al exe o script
    exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    out_dir = exe_dir / "Recursos"
    out_dir.mkdir(parents=True, exist_ok=True)

    # origen del updater
    if getattr(sys, "frozen", False):
        # En onefile: PyInstaller extrae la carpeta 'Recursos' dentro de _MEIPASS
        origin = Path(sys._MEIPASS) / "Recursos" / "updater.exe"
    else:
        # En desarrollo: usamos la carpeta Recursos del proyecto
        origin = Recursos.RECURSOS_DIR / "updater.exe"

    target = out_dir / "updater.exe"

    if origin.exists() and not target.exists():
        shutil.copy2(str(origin), str(target))
        print(f"[UPDATE] Copiado {origin} → {target}")
    else:
        print(f"[UPDATE] Nada que copiar (¿existe {origin}? destino ya existe?)")


class MainApp(App):
    title = "Calculadora R.Prestige"

    def build(self):
        # 1) Extraemos el updater
        extract_updater()
        # 2) Registramos rutas de recursos
        RecursosExternos.init_kivy()
        Recursos.init_kivy()
        # 3) Bases de datos y sincronización
        init_local_db()
        init_local_tasas()
        try:
            obtener_datos_productos()
        except:
            pass

        Window.title = self.title

        # 4) Montamos el ScreenManager
        sm = ScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(CalculoScreenContainer())
        sm.add_widget(ResultadosScreen())
        return sm

    def on_start(self):
        # La ventana ya está lista: comprobamos actualizaciones
        show_update_popup()


if __name__ == "__main__":
    MainApp().run()