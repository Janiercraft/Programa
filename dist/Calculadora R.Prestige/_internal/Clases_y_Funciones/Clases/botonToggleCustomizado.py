from Clases_y_Funciones.Clases.gestion_recursos import Recursos
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import BooleanProperty


class CustomToggleButton(ToggleButton):
    # Nueva propiedad para habilitar modo solo lectura en instancias específicas
    readonly = BooleanProperty(False)

    def __init__(self, readonly=False, **kwargs):
        # Configuraciones por defecto
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (30, 30))
        kwargs.setdefault('font_size', 20)
        kwargs.setdefault('text', '☐')
        # Asigna la fuente desde la carpeta 'recursos'
        if 'font_name' not in kwargs:
            kwargs.setdefault('font_name', Recursos.ruta('DejaVuSans.ttf'))
        # Asignamos el flag readonly antes de inicializar
        self.readonly = readonly
        super().__init__(**kwargs)
        self.bind(state=self.on_state_change)

    def on_state_change(self, instance, value):
        # Cambia el símbolo: ☑ si está presionado ("down"), sino ☐
        self.text = '☑' if value == 'down' else '☐'

    def on_touch_down(self, touch):
        # Si está en modo readonly, ignoramos cualquier pulsación
        if self.readonly:
            return False
        return super().on_touch_down(touch)
