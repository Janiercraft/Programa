from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle
from Clases_y_Funciones.Clases.tema_sistema import obtener_ruta_fondo, obtener_color_texto
from Clases_y_Funciones.Funciones.validar_dispositivo import validar_credenciales_y_dispositivo
from UX.Calculadora import MiApp
import sys

# Redimensionar la ventana
Window.size = (500, 200)

class LoginLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        ruta_fondo = obtener_ruta_fondo()
        color_texto = obtener_color_texto()

        with self.canvas.before:
            self.fondo = Rectangle(
                source=ruta_fondo,
                pos=self.pos,
                size=self.size
            )

        self.bind(pos=self.actualizar_fondo, size=self.actualizar_fondo)

        # Etiqueta Usuario
        self.label_usuario = Label(
            text="Usuario:",
            size_hint=(.2, .1),
            pos_hint={"x": 0.135, "y": 0.75},
            color=color_texto,
            bold=True
        )
        self.add_widget(self.label_usuario)

        # Campo de texto para usuario
        self.input_usuario = TextInput(
            multiline=False,
            size_hint=(.6, .15),
            pos_hint={"x": 0.3, "y": 0.725},
            foreground_color=color_texto,
            background_color=(0, 0, 0, 0.3)  # semi-transparente
        )
        self.add_widget(self.input_usuario)

        # Etiqueta Contraseña
        self.label_contrasena = Label(
            text="Contraseña:",
            size_hint=(.2, .1),
            pos_hint={"x": 0.1, "y": 0.50},
            color=color_texto,
            bold=True
        )
        self.add_widget(self.label_contrasena)

        # Campo de texto para contraseña
        self.input_contrasena = TextInput(
            multiline=False,
            size_hint=(.6, .15),
            pos_hint={"x": 0.3, "y": 0.477},
            foreground_color=color_texto,
            background_color=(0, 0, 0, 0.3)
        )
        self.add_widget(self.input_contrasena)

        # Botón Ingresar
        self.boton_ingresar = Button(
            text="Ingresar",
            size_hint=(.4, .15),
            pos_hint={"x": 0.4, "y": 0.20}
        )
        self.add_widget(self.boton_ingresar)
        self.boton_ingresar.bind(on_release=self.intentar_ingresar)

    def intentar_ingresar(self, instance):
        email = self.input_usuario.text.strip()
        clave = self.input_contrasena.text.strip()

        ok, mensaje = validar_credenciales_y_dispositivo(email, clave)
        popup = Popup(title="Login",
                    content=Label(text=mensaje),
                    size_hint=(0.6, 0.4))
        popup.open()

        if ok:
            App.get_running_app().stop()
            MiApp().run()
            sys.exit(0)

    def actualizar_fondo(self, *args):
        self.fondo.pos = self.pos
        self.fondo.size = self.size

class LoginApp(App):
    def build(self):
        return LoginLayout()

if __name__ == "__main__":
    LoginApp().run()
