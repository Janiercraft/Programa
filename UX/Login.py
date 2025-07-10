# UX/Login.py

from kivy.config import Config
# Desactiva el provider de lápiz digital (wm_pen)
Config.set('kivy', 'input_exclude', 'wm_pen')

# Configura el mouse y desactiva el multitouch simulado con el mouse
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle
from kivy.metrics import dp
from kivy.clock import Clock

from Clases_y_Funciones.Clases.tema_sistema import obtener_ruta_fondo, obtener_color_texto
from Clases_y_Funciones.Funciones.validar_dispositivo import validar_credenciales_y_dispositivo

# Redimensionar la ventana
Window.size = (500, 200)

class LoginLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        ruta_fondo = obtener_ruta_fondo()
        color_texto = obtener_color_texto()

        # Fondo dinámico
        with self.canvas.before:
            self.fondo = Rectangle(source=ruta_fondo, pos=self.pos, size=self.size)
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
            pos_hint={"x": 0.31, "y": 0.725},
            foreground_color=color_texto,
            background_color=(0, 0, 0, 0.3)
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
            password=True,
            size_hint=(.6, .15),
            pos_hint={"x": 0.31, "y": 0.477},
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
        self.boton_ingresar.bind(on_release=self.intentar_ingresar)
        self.add_widget(self.boton_ingresar)

        # Ajuste dinámico de fuentes
        Window.bind(size=self._redimensionar_fuentes)
        Clock.schedule_once(lambda dt: self._redimensionar_fuentes(Window, Window.size), 0)

    def intentar_ingresar(self, instance):
        email = self.input_usuario.text.strip()
        clave = self.input_contrasena.text.strip()
        self.boton_ingresar.disabled = True

        ok, mensaje = validar_credenciales_y_dispositivo(email, clave)
        popup = Popup(
            title="Login",
            content=Label(text=mensaje),
            size_hint=(0.6, 0.4)
        )
        popup.open()

        if ok:
            Clock.schedule_once(lambda dt: self._ir_a_calculo(popup), 5)
        else:
            popup.bind(on_dismiss=lambda inst: setattr(self.boton_ingresar, 'disabled', False))

    def _ir_a_calculo(self, popup):
        popup.dismiss()
        App.get_running_app().root.current = 'calculo'

    def actualizar_fondo(self, *args):
        self.fondo.pos = self.pos
        self.fondo.size = self.size

    def _redimensionar_fuentes(self, window, size):
        width, height = size
        # Calcula tamaños relativos
        font_label  = height * 0.06
        font_input  = height * 0.06
        font_button = height * 0.08

        self.label_usuario.font_size    = dp(font_label)
        self.label_contrasena.font_size = dp(font_label)
        self.input_usuario.font_size    = dp(font_input)
        self.input_contrasena.font_size = dp(font_input)
        self.boton_ingresar.font_size   = dp(font_button)
