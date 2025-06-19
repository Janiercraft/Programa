from kivy.core.window import Window
from Clases_y_Funciones.Clases.tamaño import ANCHO_INICIAL, ALTO_INICIAL

class DynamicTextInput:
    def __init__(self, cuota_input, initial_pos, initial_size, initial_window=(ANCHO_INICIAL, ALTO_INICIAL)):
        self.cuota_input = cuota_input
        self.initial_pos = initial_pos
        self.initial_size = initial_size
        self.initial_window = initial_window
        self.rel_x = initial_pos[0] / initial_window[0]
        self.rel_y = initial_pos[1] / initial_window[1]
        self.size_rel_x = initial_size[0] / initial_window[0]
        self.size_rel_y = initial_size[1] / initial_window[1]
        Window.bind(on_resize=self.update_position_size)

    def update_position_size(self, instance, width, height):
        new_x = width * self.rel_x
        new_y = height * self.rel_y
        new_width = width * self.size_rel_x
        new_height = height * self.size_rel_y
        self.cuota_input.pos = (new_x, new_y)
        self.cuota_input.size = (new_width, new_height)