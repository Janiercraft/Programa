from kivy.config import Config
# Esto desactiva el provider de lápiz digital (wm_pen)
Config.set('kivy', 'input_exclude', 'wm_pen')

# Esto configura el mouse y desactiva el multitouch simulado con el mouse
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from threading import Thread
from Clases_y_Funciones.Clases.gestion_recursos import Recursos
from Clases_y_Funciones.Clases.botonToggleCustomizado import CustomToggleButton
from Clases_y_Funciones.Funciones.calculos import calcular_precio_compra, calcular_precio_total, saldo_a_financiar, pago_minimo_mensual
from kivy.uix.screenmanager import ScreenManager, Screen
from UX.Resultados import ResultadosWidget
from Clases_y_Funciones.Clases.texto_dinamico import DynamicTextInput
from Clases_y_Funciones.Clases.tamaño import ANCHO_INICIAL, ALTO_INICIAL, date_input_size
from Clases_y_Funciones.Clases.tema_sistema import obtener_ruta_fondo, obtener_color_texto
from Clases_y_Funciones.Clases.decimal import ThousandSeparatorTextInput
from Clases_y_Funciones.Funciones.obtener_productos import obtener_datos_productos
from Clases_y_Funciones.Clases.autocompletado import AutoCompleteInput
from Clases_y_Funciones.Funciones.formatos_Fecha import on_date_text
from Clases_y_Funciones.Funciones.tasas import obtener_plazos_meses
import re

Window.set_icon(Recursos.ruta('calculadora.png'))

class CalculoScreen(Screen):
    """Contendrá tu MiWidget con dropdowns y botón Procesar."""
    pass

class ResultadosScreen(Screen):
    """Aquí inyectaremos dinámicamente el ResultadosWidget."""
    pass

# --- Clase principal de la aplicación ---
class MiWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Window.size = (ANCHO_INICIAL, ALTO_INICIAL)
        Window.borderless = False

        # Cargar datos y crear mapeo de productos
        self.productos_codigos, self.productos_descripciones,_,_ = obtener_datos_productos()
        self.mapping = {}
        self.mapping_inv = {}
        for codigo, descripcion in zip(self.productos_codigos, self.productos_descripciones):
            self.mapping[codigo] = descripcion
            self.mapping_inv[descripcion] = codigo

        self.extra_pairs = []
        
        self.fondo_imagen = obtener_ruta_fondo()
        self.color_texto  = obtener_color_texto()
        
        with self.canvas.before:
            self.fondo = Rectangle(source=self.fondo_imagen, pos=self.pos, size=self.size)
        self.bind(pos=self.actualizar_fondo, size=self.actualizar_fondo)
        
        self.frame = BoxLayout(size_hint=(None, None), orientation='vertical')
        with self.frame.canvas.before:
            Color(0.5, 0.5, 0.5, 0.3)
            self.rect = Rectangle(pos=self.frame.pos, size=self.frame.size)
        self.frame.bind(pos=self.actualizar_frame, size=self.actualizar_frame)
        
        self.scroll_view = ScrollView(size_hint=(None, None))
        self.grid_layout = GridLayout(cols=1, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        
        self.box_labels = BoxLayout(size_hint=(None, None), orientation='horizontal', spacing=10)
        self.box_combos = BoxLayout(size_hint=(None, None), orientation='horizontal', spacing=10)
        
        self.ancho_combo_codigo, self.alto_combo_codigo = 200, 30
        self.ancho_combo_descripcion, self.alto_combo_descripcion = 400, 30
        
        # Definir altura base y padding para labels
        self.altura_label_base = 20
        self.padding_vertical = 5
        self.altura_total_label = self.altura_label_base + self.padding_vertical * 2
        
        self.label_codigo = Label(
            text='Código',
            color=self.color_texto,
            size_hint=(None, None),
            size=(self.ancho_combo_codigo, self.altura_total_label),
            padding=(0, self.padding_vertical)
        )
        self.label_descripcion = Label(
            text='Descripción del producto',
            color=self.color_texto,
            size_hint=(None, None),
            size=(self.ancho_combo_descripcion, self.altura_total_label),
            padding=(0, self.padding_vertical)
        )

        # Guardamos tamaños de fuente iniciales para los labels
        self.font_size_label_codigo = self.label_codigo.font_size or 14
        self.font_size_label_descripcion = self.label_descripcion.font_size or 14

        # AutoCompleteInput para código y descripción
        self.codigo_input = AutoCompleteInput(
            suggestions=self.productos_codigos,
            size_hint=(None, None),
            size=(self.ancho_combo_codigo, self.alto_combo_codigo)
        )
        self.descripcion_input = AutoCompleteInput(
            suggestions=self.productos_descripciones,
            dropdown_item_height=50,
            size_hint=(None, None),
            size=(self.ancho_combo_descripcion, self.alto_combo_descripcion)
        )
        # Sincronización de campos
        self.codigo_input.on_selection = self.on_codigo_seleccionado
        self.descripcion_input.on_selection = self.on_descripcion_seleccionada

        self.box_labels.add_widget(self.label_codigo)
        self.box_labels.add_widget(self.label_descripcion)
        self.box_combos.add_widget(self.codigo_input)
        self.box_combos.add_widget(self.descripcion_input)
        
        self.grid_layout.add_widget(self.box_labels)
        self.grid_layout.add_widget(self.box_combos)
        
        self.scroll_view.add_widget(self.grid_layout)
        self.frame.add_widget(self.scroll_view)
        self.add_widget(self.frame)
        
        # Botón Procesar
        self.boton = Button(text='Procesar', size_hint=(None, None), size=(150, 30), font_size=14)
        self.add_widget(self.boton)
        self.boton.bind(on_release=self.procesar)
        
        self.ancho_boton_inicial, self.alto_boton_inicial = self.boton.size
        self.font_size_inicial = self.boton.font_size

        # --------------------- Label y toggle para fecha de pago de depósito adicional ---------------------
        # Definir posición y tamaño inicial para el label (se usa para calcular el escalado)
        self.fecha_label_initial_pos = (630, 230)
        self.fecha_label_initial_size = (150, 70)
        # Crear el Label y el toggle como widgets separados
        self.label_fecha = Label(text="Marque si hay \nfecha de pago de \ndeposito adicional", color=self.color_texto, size_hint=(None, None), halign='center', valign='middle')
        # Crear un ToggleButton que actuará como casilla de verificación
        self.toggle_fecha = CustomToggleButton()  
        # Posicionar el toggle de forma similar:
        toggle_x = self.label_fecha.pos[0] + (self.label_fecha.size[0] - self.toggle_fecha.width) / 2
        toggle_y = self.label_fecha.y - self.toggle_fecha.height
        self.toggle_fecha.pos = (toggle_x, toggle_y)

        self.add_widget(self.label_fecha)
        self.add_widget(self.toggle_fecha)
        self.toggle_fecha.bind(state=self.on_toggle_fecha)

        # --- Inicio: Agregar TextInput para fecha de pago (oculto por defecto) ---
        self.date_input = TextInput(
            text="",
            size_hint=(None, None),
            size=date_input_size,
            hint_text="DD/MM/AAAA",
            multiline=False,
            # Cambiado input_filter para que solo permita dígitos en la entrada del usuario
            input_filter=lambda substring, from_undo: ''.join(filter(str.isdigit, substring))
        )
        self.date_input_initial_size = date_input_size

        self.date_input.bind(text=on_date_text)
        self.date_input_visible = False

        # --- Preparar labels fecha de pago adicional y monto de pago adicional, sin agregarlos aún ---
        self.label_F_P_Adicional = Label(text="Fecha de pago adicional", color=self.color_texto, size_hint=(None, None), size=(150, 30), halign='center', valign='middle')
        self.label_M_P_Adicional = Label(text="Monto de \npago adicional", color=self.color_texto, size_hint=(None, None), size=(150, 30), halign='center', valign='middle')

        #Crear TextInput para monto (inicialmente oculto) con las mismas características que el TextInput de cuota
        self.monto_input = ThousandSeparatorTextInput(text="", size_hint=(None, None))

        # Definimos un tamaño inicial similar a cuota
        self.monto_input_initial_size = (150, 28)
        self.monto_input_visible = False

        # --- Fin: Agregar TextInput para fecha de pago ---

        # ********** NUEVA SECCIÓN: Crear los dos nuevos labels **********
        # Se ubicarán 5px debajo de monto_input y separados 10px horizontalmente
        self.deposito_label = Label(
            text="Depósito",
            color=self.color_texto,
            size_hint=(None, None),
            size=(150, 30)
        )
        self.P_total_label = Label(
            text="Pago Total",
            color=self.color_texto,
            size_hint=(None, None),
            size=(150, 30)
        )
        # Nota: No es necesario agregarlos inmediatamente; se pueden agregar cuando se muestre el bloque de monto.

        # **************************** FIN NUEVA SECCIÓN ********************************
        self.toggle_deposito = CustomToggleButton()
        self.toggle_P_total = CustomToggleButton()

        # Definir las banderas de visibilidad:
        self.toggle_deposito_visible = False
        self.toggle_P_total_visible = False

        # Ahora llamamos a actualizar_distribucion sabiendo que los atributos de fecha ya existen
        self.actualizar_distribucion(None, Window.width, Window.height)
        Window.bind(on_resize=self.actualizar_distribucion)

        # ----------------------- TextInput y label cuota ------------------------
        self.cuota_input = ThousandSeparatorTextInput(text="", size_hint=(None, None))
        initial_posicion = (635, 350)
        initial_size = (150, 28)
        self.cuota_input.pos = initial_posicion
        self.add_widget(self.cuota_input)

        # 1) Crear el label y guardar su font_size inicial
        self.numero_cuotas_label = Label(
            text="Número de cuotas",
            color=self.color_texto,
            size_hint=(None, None)
        )
        self.font_size_numero_inicial = self.numero_cuotas_label.font_size
        self.add_widget(self.numero_cuotas_label)

        def actualizar_label_numero(*args):
            # escala vertical respecto al tamaño original de ventana
            escala = Window.height / ALTO_INICIAL

            # 2a) font_size proporcional a la escala
            nueva_fuente = int(self.font_size_numero_inicial * escala)
            self.numero_cuotas_label.font_size = nueva_fuente - 0.1

            # 2b) forzar actualización de textura para medir bien el alto
            self.numero_cuotas_label.texture_update()
            ancho = self.cuota_input.width
            alto = self.numero_cuotas_label.texture_size[1]
            self.numero_cuotas_label.size = (ancho, alto)

            # 2c) posicionar 10px*escala por debajo del input
            x = self.cuota_input.x
            y = self.cuota_input.y - alto - 5 * escala
            self.numero_cuotas_label.pos = (x, y)

        # 3) Conectar a cambios de tamaño/posición del input y al redimensionar la ventana
        self.cuota_input.bind(pos=actualizar_label_numero, size=actualizar_label_numero)
        Window.bind(on_resize=actualizar_label_numero)

        # 4) Llamada inicial
        actualizar_label_numero()

        # 1) Obtenemos dinámicamente la lista de plazos
        plazos = obtener_plazos_meses()
        # 2) Creamos el Spinner con esos valores
        self.cuotas_spinner = Spinner(
            text=plazos[0] if plazos else '',
            values=plazos,
            size_hint=(None, None)
        )
        # tamaño y fuente originales
        self.spinner_size_base = (self.cuota_input.width, self.cuota_input.height)
        self.spinner_font_size_base = self.cuotas_spinner.font_size
        self.add_widget(self.cuotas_spinner)

        # 2) Función que actualiza posición, tamaño y font_size del Spinner
        def actualizar_spinner(*args):
            escala = Window.height / ALTO_INICIAL

            # 2a) font_size proporcional
            self.cuotas_spinner.font_size = int(self.spinner_font_size_base * escala)

            # 2b) tamaño igual al input (o ajusta como prefieras)
            ancho = self.cuota_input.width
            alto = self.cuota_input.height
            self.cuotas_spinner.size = (ancho, alto)

            # 2c) posicionar 10px*escala por debajo del label
            x = self.cuota_input.x
            y = self.numero_cuotas_label.y - alto - 5 * escala
            self.cuotas_spinner.pos = (x, y)

        # 3) Hacer que se ejecute al redimensionar y tras mover/recalcular el label
        Window.bind(on_resize=actualizar_spinner)
        self.numero_cuotas_label.bind(pos=actualizar_spinner, size=actualizar_spinner)

        # 4) Llamada inicial
        actualizar_spinner()

        altura_base = 10

        self.label_cuota = Label(
            text='Cuota Inicial',
            color=self.color_texto,
            size_hint=(None, None),
            size=(self.cuota_input.width, altura_base),
            padding=(0)
        )
        self.add_widget(self.label_cuota)

        def update_label_cuota(*args):
            scale_factor = Window.height / ALTO_INICIAL  # Escala vertical respecto al tamaño inicial
            separation = 7 * scale_factor              # 7 px redimensionados
            # Centrar el label en relación al TextInput
            self.label_cuota.center_x = self.cuota_input.center_x
            # Posicionar el label 5 px (ajustados a la escala) por encima del top del TextInput
            self.label_cuota.y = self.cuota_input.top + separation
            # Opcionalmente, puedes ajustar la fuente
            self.label_cuota.font_size = self.cuota_input.height * 0.6
            self.cuota_input.font_size = int(self.cuota_input.height * 0.6)

        self.cuota_input.bind(pos=update_label_cuota, size=update_label_cuota)
        update_label_cuota()

        self.dynamic_textinput = DynamicTextInput(
            cuota_input=self.cuota_input,
            initial_pos=initial_posicion,
            initial_size=initial_size,
            initial_window=(ANCHO_INICIAL, ALTO_INICIAL)
        )

        # --------------------- Botones + y - ---------------------
        self.ancho_btn_inicial = 80  
        self.alto_btn_inicial = 20   
        
        self.btn_plus = Button(text='+', size_hint=(None, None), size=(self.ancho_btn_inicial, self.alto_btn_inicial))
        self.btn_minus = Button(text='-', size_hint=(None, None), size=(self.ancho_btn_inicial, self.alto_btn_inicial))
        self.add_widget(self.btn_plus)
        self.add_widget(self.btn_minus)

        # Definir función para actualizar la posición de los botones debajo del frame
        def update_buttons_pos(*args):
            espacio_entre = 10
            total_ancho_botones = self.btn_plus.width + self.btn_minus.width + espacio_entre
            x_pos = self.frame.x + (self.frame.width - total_ancho_botones) / 2
            y_pos = self.frame.y - self.btn_plus.height - 2
            self.btn_plus.pos = (x_pos, y_pos)
            self.btn_minus.pos = (x_pos + self.btn_plus.width + espacio_entre, y_pos)

        # Definir función para actualizar el tamaño de los botones con debounce al redimensionar la ventana
        def actualizar_btns(instance, width, height):
            def do_update(dt):
                if width == ANCHO_INICIAL and height == ALTO_INICIAL:
                    nuevo_ancho_btn = self.ancho_btn_inicial
                    nuevo_alto_btn = self.alto_btn_inicial
                else:
                    escala_x, escala_y = width / ANCHO_INICIAL, height / ALTO_INICIAL
                    nuevo_ancho_btn = int(self.ancho_btn_inicial * escala_x)
                    nuevo_alto_btn = int(self.alto_btn_inicial * escala_y)
                self.btn_plus.size = (nuevo_ancho_btn, nuevo_alto_btn)
                self.btn_minus.size = (nuevo_ancho_btn, nuevo_alto_btn)
                nuevo_font_btn = int(min(nuevo_ancho_btn, nuevo_alto_btn) * 0.8)
                self.btn_plus.font_size = nuevo_font_btn
                self.btn_minus.font_size = nuevo_font_btn
                update_buttons_pos()
            Clock.unschedule(do_update)
            Clock.schedule_once(do_update, 0.01)

        # Realizar los bindings correspondientes
        self.frame.bind(pos=update_buttons_pos, size=update_buttons_pos)
        update_buttons_pos()
        Window.bind(on_resize=actualizar_btns)

        self.btn_plus.bind(on_release=self.agregar_par)
        self.btn_minus.bind(on_release=self.eliminar_par)
        
        """
        # --------------------- Botón de Configuración adaptable ---------------------
        self.btn_config = Button(text="⚙", font_name=Recursos.ruta('DejaVuSans.ttf'), font_size=30, size_hint=(None, None), size=(30, 30))
        self.add_widget(self.btn_config)
        Window.bind(on_resize=self.actualizar_config_btn)
        self.actualizar_config_btn(Window, Window.width, Window.height)
        """
        
    # Bind al toggle para mostrar u ocultar el date_input y el monto_input
    def on_toggle_fecha(self, instance, value):
        if value == "down":
            # Calcular escala en función del tamaño de la ventana
            escala_x = 1 if Window.width == ANCHO_INICIAL else Window.width / ANCHO_INICIAL
            escala_y = 1 if Window.height == ALTO_INICIAL else Window.height / ALTO_INICIAL

            # Posicionar y mostrar los labels y toggles asociados
            if self.label_F_P_Adicional.parent is None:
                self.add_widget(self.label_F_P_Adicional)
            if self.label_M_P_Adicional.parent is None:
                self.add_widget(self.label_M_P_Adicional)

            # Posicionar label_F_P_Adicional respecto al toggle_fecha
            self.label_F_P_Adicional.pos = (
                self.toggle_fecha.x - 60 * escala_x,
                self.toggle_fecha.y - self.label_F_P_Adicional.height +2  * escala_y
            )
            if self.label_F_P_Adicional.parent is None:
                self.add_widget(self.label_F_P_Adicional)
            
            # Posicionar y mostrar el date_input
            self.date_input.pos = (
                self.label_F_P_Adicional.x + 15 * escala_x,
                self.label_F_P_Adicional.y - self.date_input.height - 2 * escala_y
            )
            if not self.date_input_visible:
                self.add_widget(self.date_input)
                self.date_input_visible = True

            # Posicionar label_M_P_Adicional
            self.label_M_P_Adicional.pos = (
                self.label_F_P_Adicional.x,
                self.date_input.y - self.label_M_P_Adicional.height - 8 * escala_y
            )
            if self.label_M_P_Adicional.parent is None:
                self.add_widget(self.label_M_P_Adicional)

            # Posicionar y mostrar el monto_input
            if not self.monto_input_visible:
                self.monto_input.pos = (
                    self.label_M_P_Adicional.x,
                    self.label_M_P_Adicional.y - self.monto_input_initial_size[1] * escala_y - 8 * escala_y
                )
                self.monto_input.size = (
                    self.monto_input_initial_size[0] * escala_x,
                    self.monto_input_initial_size[1] * escala_y
                )
                self.monto_input.font_size = int(self.font_size_inicial * min(escala_x, escala_y))
                self.add_widget(self.monto_input)
                self.monto_input_visible = True
            
            # Asegurarse de que los labels adicionales también se agreguen (en caso de haber sido removidos)
            if self.deposito_label.parent is None:
                self.add_widget(self.deposito_label)
            if self.P_total_label.parent is None:
                self.add_widget(self.P_total_label)
            # También puede ser útil, si deseas, mostrar/ocultar los toggle_deposito y toggle_P_total.
            if self.toggle_deposito.parent is None:
                self.add_widget(self.toggle_deposito)
                self.toggle_deposito_visible = True
            if self.toggle_P_total.parent is None:
                self.add_widget(self.toggle_P_total)
                self.toggle_P_total_visible = True

            self.actualizar_distribucion(None, Window.width, Window.height)
        else:
            # Ocultar widgets relacionados a la fecha de pago adicional
            if self.date_input_visible:
                self.remove_widget(self.date_input)
                self.date_input_visible = False
            if self.monto_input_visible:
                self.remove_widget(self.monto_input)
                self.monto_input_visible = False
            if self.toggle_deposito_visible:
                self.remove_widget(self.toggle_deposito)
                self.toggle_deposito_visible = False
            if self.toggle_P_total_visible:
                self.remove_widget(self.toggle_P_total)
                self.toggle_P_total_visible = False
            for w in (self.label_F_P_Adicional, self.label_M_P_Adicional, self.deposito_label, self.P_total_label):
                if w.parent:
                    self.remove_widget(w)
    """
    def actualizar_config_btn(self, instance, width, height):
        scale_x = width / ANCHO_INICIAL
        scale_y = height / ALTO_INICIAL
        new_width = 30 * scale_x
        new_height = 30 * scale_y
        margin_x = 10 * scale_x
        margin_y = 10 * scale_y
        self.btn_config.size = (new_width, new_height)
        self.btn_config.pos = (margin_x, margin_y)
        self.btn_config.font_size = int(min(new_width, new_height) * 0.8)
    """
    def on_codigo_seleccionado(self, codigo):
        if codigo in self.mapping:
            self.descripcion_input.text = self.mapping[codigo]
            self.descripcion_input.dropdown.dismiss()
            self.descripcion_input.focus = False

    def on_descripcion_seleccionada(self, descripcion):
        if descripcion in self.mapping_inv:
            self.codigo_input.text = self.mapping_inv[descripcion]
            self.codigo_input.dropdown.dismiss()
            self.codigo_input.focus = False

    def actualizar_fondo(self, *args):
        self.fondo.pos = self.pos
        self.fondo.size = self.size
    
    def actualizar_frame(self, *args):
        self.rect.pos = self.frame.pos
        self.rect.size = self.frame.size
    
    def actualizar_distribucion(self, instancia, width, height):
        escala_x, escala_y = width / ANCHO_INICIAL, height / ALTO_INICIAL
        nueva_ancho = int(self.ancho_boton_inicial * escala_x)
        nueva_alto = int(self.alto_boton_inicial * escala_y)
        nuevo_font = int(self.font_size_inicial * min(escala_x, escala_y))
    
        self.boton.size = (nueva_ancho, nueva_alto)
        self.boton.pos = (width / 2 - nueva_ancho / 2, 20)
        self.boton.font_size = nuevo_font
        
        frame_ancho, frame_alto = int(width * 0.77), int(height * 0.7)
        self.frame.size = (frame_ancho, frame_alto)
        self.frame.pos = (0, height - frame_alto)
        self.scroll_view.size = (frame_ancho, frame_alto)
        
        nuevo_ancho_codigo = int(self.ancho_combo_codigo * escala_x)
        nuevo_alto_codigo = int(self.alto_combo_codigo * escala_y)
        nuevo_ancho_desc = int(self.ancho_combo_descripcion * escala_x)
        nuevo_alto_desc = int(self.alto_combo_descripcion * escala_y)
        
        self.codigo_input.size = (nuevo_ancho_codigo, nuevo_alto_codigo)
        self.descripcion_input.size = (nuevo_ancho_desc, nuevo_alto_desc)
        
        altura_total_label_nueva = int((self.altura_label_base + self.padding_vertical * 2) * min(escala_x, escala_y))
        self.label_codigo.size = (nuevo_ancho_codigo, altura_total_label_nueva)
        self.label_descripcion.size = (nuevo_ancho_desc, altura_total_label_nueva)
        
        self.label_codigo.font_size = int(self.font_size_label_codigo * min(escala_x, escala_y))
        self.label_descripcion.font_size = int(self.font_size_label_descripcion * min(escala_x, escala_y))
        
        self.box_labels.size = (nuevo_ancho_codigo + nuevo_ancho_desc + 10, altura_total_label_nueva)
        self.box_combos.size = (nuevo_ancho_codigo + nuevo_ancho_desc + 10, max(nuevo_alto_codigo, nuevo_alto_desc))
        
        for box, codigo_inp, desc_inp in self.extra_pairs:
            codigo_inp.size = (nuevo_ancho_codigo, nuevo_alto_codigo)
            desc_inp.size = (nuevo_ancho_desc, nuevo_alto_desc)
            box.size = (nuevo_ancho_codigo + nuevo_ancho_desc + 10, max(nuevo_alto_codigo, nuevo_alto_desc))
        self.actualizar_frame()

        # Actualizar posición, tamaño y fuente del label de fecha y del toggle
        new_pos_label = (self.fecha_label_initial_pos[0] * escala_x, self.fecha_label_initial_pos[1] * escala_y)
        new_size_label = (self.fecha_label_initial_size[0] * escala_x, self.fecha_label_initial_size[1] * escala_y)
        self.label_fecha.pos = new_pos_label
        self.label_fecha.size = new_size_label
        self.label_fecha.font_size = int(14 * min(escala_x, escala_y))
        self.label_fecha.color = self.color_texto  # Actualiza el color según el fondo
        
        new_toggle_size = (30 * escala_x, 30 * escala_y)
        self.toggle_fecha.size = new_toggle_size
        self.toggle_fecha.font_size = self.toggle_fecha.height * 0.8
        toggle_x = new_pos_label[0] + (new_size_label[0] - new_toggle_size[0]) / 2
        toggle_y = new_pos_label[1] - new_toggle_size[1] + 5 * escala_y
        self.toggle_fecha.pos = (toggle_x, toggle_y)

        # Actualizar tamaño y posición del date_input si está visible
        if self.date_input_visible:
            # Primero: Actualizar label_F_P_Adicional
            self.label_F_P_Adicional.size = (150 * escala_x, 30 * escala_y)
            self.label_F_P_Adicional.font_size = int(14 * min(escala_x, escala_y))
            self.label_F_P_Adicional.pos = (self.toggle_fecha.x - 60 * escala_x, self.toggle_fecha.y - self.label_F_P_Adicional.height + 2 * escala_y)

            # Segundo: Actualizar date_input en función de la posición de label_F_P_Adicional
            new_date_input_width = self.date_input_initial_size[0] * escala_x
            new_date_input_height = self.date_input_initial_size[1] * escala_y
            self.date_input.size = (new_date_input_width, new_date_input_height)
            self.date_input.pos = (self.label_F_P_Adicional.x + 15 * escala_x, self.label_F_P_Adicional.y - new_date_input_height - 2 * escala_y)
            nuevo_font_date = int(self.font_size_inicial * min(escala_x, escala_y) * 1.2)
            self.date_input.font_size = nuevo_font_date

            # Tercero: Actualizar label_M_P_Adicional en función de date_input
            self.label_M_P_Adicional.size = (150 * escala_x, 30 * escala_y)
            self.label_M_P_Adicional.font_size = int(14 * min(escala_x, escala_y))
            self.label_M_P_Adicional.pos = (self.label_F_P_Adicional.x, self.date_input.y - self.label_M_P_Adicional.height - 8 * escala_y)

            # **NUEVA PARTE**: Actualizar monto_input si está visible
            if self.monto_input_visible:
                new_monto_input_width = self.monto_input_initial_size[0] * escala_x
                new_monto_input_height = self.monto_input_initial_size[1] * escala_y
                self.monto_input.size = (new_monto_input_width, new_monto_input_height)
                self.monto_input.pos = (self.label_M_P_Adicional.x, self.label_M_P_Adicional.y - new_monto_input_height - 8 * escala_y)
                self.monto_input.font_size = int(self.cuota_input.font_size)

                # ********** NUEVA PARTE: Ubicar los 2 nuevos labels y toggles debajo de monto_input **********
                # --- Reubicar los labels de Depósito y P. Total ---
                # Definir el tamaño de los labels (puedes ajustar estos valores si lo deseas)
                new_label_width = 150 * escala_x
                new_label_height = 30 * escala_y
                self.deposito_label.size = (new_label_width, new_label_height)
                self.P_total_label.size = (new_label_width, new_label_height)

                # Definir la separación horizontal entre los dos labels: 2px (ajustado a escala)
                spacing = -60 * escala_x

                # Calcular el ancho total que ocupan ambos labels más el espacio
                total_labels_width = new_label_width * 2 + spacing

                # Centrar estos dos labels respecto al centro horizontal del monto_input
                monto_center_x = self.monto_input.center_x
                deposito_x = monto_center_x - total_labels_width / 2
                # Posicionar el label Depósito justo debajo del monto_input,
                # por ejemplo, con una separación vertical de 5px (ajustada a escala)
                vertical_offset_labels = 3 * escala_y
                deposito_y = self.monto_input.y - new_label_height - vertical_offset_labels

                self.deposito_label.pos = (deposito_x, deposito_y)
                self.P_total_label.pos = (deposito_x + new_label_width + spacing, deposito_y)

                # Actualizar la fuente de los labels
                new_font_label = int(14 * min(escala_x, escala_y))
                self.deposito_label.font_size = new_font_label
                self.P_total_label.font_size = new_font_label

                # --- Reubicar los toggle buttons asociados ---
                # Definir el tamaño de los toggles (ya calculado)
                toggle_size = (30 * escala_x, 30 * escala_y)
                self.toggle_deposito.size = toggle_size
                self.toggle_P_total.size = toggle_size
                self.toggle_deposito.font_size = self.toggle_deposito.height * 0.8
                self.toggle_P_total.font_size = self.toggle_P_total.height * 0.8

                # Colocar cada toggle debajo de su label correspondiente
                toggle_offset = -2 * escala_y  # separación vertical adicional
                # Calcular posiciones centradas respecto a cada label:
                deposito_center_x = self.deposito_label.center_x
                p_total_center_x = self.P_total_label.center_x
                toggle_y = self.deposito_label.y - toggle_size[1] - toggle_offset

                self.toggle_deposito.pos = (deposito_center_x - toggle_size[0] / 2, toggle_y)
                self.toggle_P_total.pos = (p_total_center_x - toggle_size[0] / 2, toggle_y)
    
    def actualizar_btns(self, instance, width, height):
        if width == ANCHO_INICIAL and height == ALTO_INICIAL:
            nuevo_ancho_btn = self.ancho_btn_inicial
            nuevo_alto_btn = self.alto_btn_inicial
        else:
            escala_x, escala_y = width / ANCHO_INICIAL, height / ALTO_INICIAL
            nuevo_ancho_btn = int(self.ancho_btn_inicial * escala_x)
            nuevo_alto_btn = int(self.alto_btn_inicial * escala_y)
        self.btn_plus.size = (nuevo_ancho_btn, nuevo_alto_btn)
        self.btn_minus.size = (nuevo_ancho_btn, nuevo_alto_btn)
        x_pos = self.frame.x + self.frame.width + 10
        y_pos = self.frame.y + self.frame.height/2 - nuevo_alto_btn/2
        self.btn_plus.pos = (x_pos, y_pos)
        self.btn_minus.pos = (x_pos + nuevo_ancho_btn + 10, y_pos)
    
    def agregar_par(self, instance):
        new_box = BoxLayout(orientation='horizontal', size_hint=(None, None), spacing=10)
        new_box.size = (self.ancho_combo_codigo + self.ancho_combo_descripcion + 10,
                        max(self.alto_combo_codigo, self.alto_combo_descripcion))
        codigo_inp = AutoCompleteInput(
            suggestions=self.productos_codigos,
            size_hint=(None, None),
            size=(self.ancho_combo_codigo, self.alto_combo_codigo)
        )
        desc_inp = AutoCompleteInput(
            suggestions=self.productos_descripciones,
            dropdown_item_height=50,
            size_hint=(None, None),
            size=(self.ancho_combo_descripcion, self.alto_combo_descripcion)
        )
        def on_select_codigo(codigo):
            desc_inp.text = self.mapping.get(codigo, "")
            desc_inp.dropdown.dismiss()
            desc_inp.focus = False
        def on_select_desc(descripcion):
            codigo_inp.text = self.mapping_inv.get(descripcion, "")
            codigo_inp.dropdown.dismiss()
            codigo_inp.focus = False
        codigo_inp.on_selection = on_select_codigo
        desc_inp.on_selection = on_select_desc
        
        new_box.add_widget(codigo_inp)
        new_box.add_widget(desc_inp)
        self.grid_layout.add_widget(new_box)
        self.extra_pairs.append((new_box, codigo_inp, desc_inp))
        self.actualizar_distribucion(None, Window.width, Window.height)
    
    def eliminar_par(self, instance):
        if self.extra_pairs:
            box, _, _ = self.extra_pairs.pop()
            self.grid_layout.remove_widget(box)
    
    def procesar(self, instance):
        """
        Se ejecuta al pulsar el botón “Procesar”.
        Muestra un spinner, lanza el cálculo en un Thread y retorna de inmediato.
        """
        spinner_text = self.cuotas_spinner.text
        match = re.search(r'\d+', spinner_text)
        meses_seleccionados = int(match.group()) if match else 0

        # 1) Recolectar pares de productos
        pares = []

        # 1.a) Primer par (inputs principales)
        c0 = self.codigo_input.text.strip()
        d0 = self.descripcion_input.text.strip()
        if d0:
            pares.append((c0, d0))

        # 1.b) Pares extra agregados por el usuario (self.extra_pairs)
        for _, ci, di in self.extra_pairs:
            c = ci.text.strip()
            d = di.text.strip()
            if d:
                pares.append((c, d))

        if not pares:
            return  # No hay productos válidos para procesar

        # 3) Lanzamos el thread para cálculos en background
        Thread(
            target=self._calcular_en_background,
            args=(pares, meses_seleccionados,),
            daemon=True
        ).start()


    def _calcular_en_background(self, pares, meses_seleccionados):
        """
        Este método corre en un thread aparte. Hace todas las operaciones de cálculo
        (precio_compra, precio_total, saldo, etc.) y al terminar llama a _mostrar_resultados
        en el hilo principal a través de Clock.schedule_once.
        """
        # 1) Obtenemos depósito_pagado a partir de cuota_input
        cuota_text = self.cuota_input.text or "0"
        raw_cuota = cuota_text.replace('.', '').replace(',', '.')
        try:
            deposito_pagado = float(raw_cuota)
        except ValueError:
            deposito_pagado = 0.0

        # 2) Invocamos las funciones de cálculo (que ahora ya usan agregación y cliente persistente)
        P_Compra = calcular_precio_compra(pares)
        P_Total  = calcular_precio_total(pares)
        saldo    = saldo_a_financiar(pares, deposito_pagado)
        pago_minimo = pago_minimo_mensual(pares, deposito_pagado, meses_seleccionados)

        # 3) Extraemos el resto de campos (fecha, depósito adicional, toggles…)
        fecha_text = self.date_input.text.strip() or ""
        estado_deposito   = self.toggle_deposito.state
        estado_pago_total = self.toggle_P_total.state

        monto_text = self.monto_input.text or "0"
        raw_monto  = monto_text.replace('.', '').replace(',', '.')
        try:
            deposito_adicional = float(raw_monto)
        except ValueError:
            deposito_adicional = 0.0

        # 4) Empaquetamos todos los resultados en un diccionario
        resultados = {
            "precio_compra":       P_Compra,
            "precio_total":        P_Total,
            "deposito_pagado":     deposito_pagado,
            "saldo_a_financiar":   saldo,
            "pago_minimo_mensual": pago_minimo,
            "fecha_pago_adicional": fecha_text,
            "deposito_adicional":  deposito_adicional,
            "meses_plazo":         meses_seleccionados,
            "estado_deposito":     estado_deposito,
            "estado_pago_total":   estado_pago_total
        }

        # 5) Regresamos al hilo principal para mostrar resultados
        Clock.schedule_once(lambda dt: self._mostrar_resultados(resultados))

    def _mostrar_resultados(self, resultados):
        """
        Este método corre en el hilo principal (invocado vía Clock).
        Oculta el spinner, crea el ResultadosWidget con los valores calculados
        y cambia la pantalla.
        """

        # 2) Construimos el widget de resultados usando los valores calculados
        widget_res = ResultadosWidget(
            precio_compra       = resultados["precio_compra"],
            precio_total        = resultados["precio_total"],
            deposito_pagado     = resultados["deposito_pagado"],
            saldo_a_financiar   = resultados["saldo_a_financiar"],
            fecha_pago_adicional = resultados["fecha_pago_adicional"],
            deposito_adicional  = resultados["deposito_adicional"],
            estado_deposito     = resultados["estado_deposito"],
            estado_pago_total   = resultados["estado_pago_total"],
            meses_plazo      = resultados["meses_plazo"],
            pago_minimo_mensual  = resultados["pago_minimo_mensual"]
        )

        # 3) Mostramos la pantalla de resultados
        app = App.get_running_app()
        res_screen = app.sm.get_screen('resultados')
        res_screen.clear_widgets()
        res_screen.add_widget(widget_res)
        app.sm.current = 'resultados'



class MiApp(App):
    def build(self):
        self.title = "Calculadora Royal"
        # 1) Crear el ScreenManager
        sm = ScreenManager()
        self.sm = sm  # para luego acceder desde MiWidget

        # 2) Pantalla de cálculo
        calc_screen = CalculoScreen(name='calculo')
        calc_widget = MiWidget()
        calc_screen.add_widget(calc_widget)
        sm.add_widget(calc_screen)

        # 3) Pantalla de resultados (vacía por ahora)
        res_screen = ResultadosScreen(name='resultados')
        sm.add_widget(res_screen)

        return sm

if __name__ == "__main__":
     
    try:
        obtener_datos_productos()
        print("[SYNC] Base local sincronizada con MongoDB")
    except Exception as e:
        print(f"[SYNC OFFLINE] No se pudo sincronizar: {e!r}")

    MiApp().run()
