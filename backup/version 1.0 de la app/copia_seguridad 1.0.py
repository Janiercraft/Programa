import os 
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.togglebutton import ToggleButton
from pymongo import MongoClient
from PIL import Image as PilImage
from kivy.clock import Clock

# Ruta base de recursos
RUTA_RECURSOS = os.path.join(os.path.dirname(__file__), 'Recursos')

# Imágenes específicas
btn_configuracion = os.path.join(RUTA_RECURSOS, 'configuracion.png')
fondo_Blanco = os.path.join(RUTA_RECURSOS, 'blanco.jpg')
fondo_negro = os.path.join(RUTA_RECURSOS, 'negro.jpg')
fuente_DejaVu = os.path.join(RUTA_RECURSOS, 'DejaVuSans.ttf')

# Tamaño inicial de la ventana
ANCHO_INICIAL = 800  
ALTO_INICIAL = 400  

Config.set('graphics', 'width', str(ANCHO_INICIAL))
Config.set('graphics', 'height', str(ALTO_INICIAL))
Config.set('graphics', 'resizable', True)

def calcular_luminosidad(imagen_path):
    """Calcula la luminosidad promedio de la imagen."""
    try:
        imagen = PilImage.open(imagen_path).convert('L')
        histograma = imagen.histogram()
        brillo_promedio = sum(i * histograma[i] for i in range(256)) / sum(histograma)
        return brillo_promedio
    except Exception as e:
        print(f"Error al calcular la luminosidad: {e}")
        return 128

def obtener_datos_productos():
    try:
        # Reemplaza MONGO_URI por tu cadena de conexión real a MongoDB Atlas
        MONGO_URI = "mongodb+srv://Janiercraft:Soy.Janiercraft.aDmin@royal-colombia.2a7ox.mongodb.net/?retryWrites=true&w=majority&appName=Royal-Colombia"
        client = MongoClient(MONGO_URI)
        db = client['Royal']
        collection = db['productos']
        productos = list(collection.find({}))
        codigos = [str(prod.get("CODIGO", "")) for prod in productos]
        descripciones = [str(prod.get("DESCRIPCION DEL PRODUCTO", "")) for prod in productos]
        return codigos, descripciones
    except Exception as e:
        print(f"Error al conectarse a la base de datos: {e}")
        return ['001', '002', '003'], ['Producto A', 'Producto B', 'Producto C']

class DynamicTextInput:
    def __init__(self, text_input, initial_pos, initial_size, initial_window=(ANCHO_INICIAL, ALTO_INICIAL)):
        self.text_input = text_input
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
        self.text_input.pos = (new_x, new_y)
        self.text_input.size = (new_width, new_height)

def cargar_archivo(nombre_archivo):
    return os.path.join(os.path.dirname(__file__), 'Recursos', nombre_archivo)

#cambiar tamaño del date input
date_input_size = (120, 30)

# --- Clase AutoCompleteInput ---
class AutoCompleteInput(TextInput):
    def __init__(self, suggestions=[], dropdown_item_height=30, **kwargs):
        super().__init__(**kwargs)
        self.suggestions = suggestions
        self.dropdown_item_height = dropdown_item_height
        self.multiline = False
        self.dropdown = DropDown()
        self.on_selection = None  # Callback al seleccionar un item
        self.bind(text=self.on_text)
        self.bind(focus=self.on_focus)

    def on_text(self, instance, value):
        self.dropdown.dismiss()
        if not value:
            return
        matching = [s for s in self.suggestions if value.lower() in s.lower()]
        if matching:
            self.dropdown = DropDown()
            for item in matching:
                btn = Button(text=item, size_hint_y=None, height=self.dropdown_item_height)
                btn.bind(on_release=lambda btn, text=item: self.select_item(text))
                self.dropdown.add_widget(btn)
            self.dropdown.open(self)

    def select_item(self, text):
        self.text = text
        self.dropdown.dismiss()
        self.focus = False
        if self.on_selection:
            self.on_selection(text)

    def on_focus(self, instance, focused):
        if not focused:
            self.dropdown.dismiss()

# --- Clase principal de la aplicación ---
class MiWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Cargar datos y crear mapeo de productos
        self.productos_codigos, self.productos_descripciones = obtener_datos_productos()
        self.mapping = {}
        self.mapping_inv = {}
        for codigo, descripcion in zip(self.productos_codigos, self.productos_descripciones):
            self.mapping[codigo] = descripcion
            self.mapping_inv[descripcion] = codigo

        self.extra_pairs = []
        
        self.fondo_imagen = cargar_archivo('blanco.jpg')
        self.luminosidad = calcular_luminosidad(self.fondo_imagen)
        # Usamos la misma variable de color para el texto en función de la luminosidad
        self.color_texto = (0, 0, 0, 1) if self.luminosidad > 128 else (1, 1, 1, 1)
        
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
        
        self.ancho_boton_inicial, self.alto_boton_inicial = self.boton.size
        self.font_size_inicial = self.boton.font_size

        # --------------------- Label y toggle para fecha de pago de depósito adicional ---------------------
        # Definir posición y tamaño inicial para el label (se usa para calcular el escalado)
        self.fecha_label_initial_pos = (630, 276)
        self.fecha_label_initial_size = (150, 70)
        # Crear el Label y el toggle como widgets separados
        self.label_fecha = Label(text="marque si \nhay fecha de \npago de deposito\nadicional", color=self.color_texto, size_hint=(None, None))
        # Crear un ToggleButton que actuará como casilla de verificación
        self.toggle_fecha = ToggleButton(
            text="☐",   # Símbolo de casilla vacía
            size_hint=(None, None),
            size=(30, 30),
            state="normal",
            font_size=20,  # Ajustá según convenga
            font_name=cargar_archivo('DejaVuSans.ttf')
        )
        # Posicionar el toggle de forma similar:
        toggle_x = self.label_fecha.pos[0] + (self.label_fecha.size[0] - self.toggle_fecha.width) / 2
        toggle_y = self.label_fecha.y - self.toggle_fecha.height + 5
        self.toggle_fecha.pos = (toggle_x, toggle_y)

        self.add_widget(self.label_fecha)
        self.add_widget(self.toggle_fecha)
        
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

        # Se limita la entrada a 8 dígitos y se formatea automáticamente
        def on_date_text(instance, value):
            # Inicializar prev_text si no existe
            if not hasattr(instance, 'prev_text'):
                instance.prev_text = value

            # Si el usuario está borrando (el nuevo valor es menor que el anterior), solo actualizamos prev_text y salimos
            if len(value) < len(instance.prev_text):
                instance.prev_text = value
                return

            # Extraer solo dígitos y limitar a 8
            digits = ''.join(filter(str.isdigit, value))[:8]
            # Formatear de acuerdo a la cantidad de dígitos
            if len(digits) <= 2:
                formatted = digits + ('/' if len(digits) == 2 else '')
            elif len(digits) <= 4:
                formatted = digits[:2] + '/' + digits[2:]
            else:
                formatted = digits[:2] + '/' + digits[2:4] + '/' + digits[4:]
            
            # Solo actualiza si el texto no coincide ya con el formateado
            if value != formatted:
                instance.text = formatted
                # Reubicar el cursor al final en el siguiente frame para evitar retrocesos
                Clock.schedule_once(lambda dt: setattr(instance, 'cursor', (len(formatted), 0)), 0)
            instance.prev_text = instance.text

        self.date_input.bind(text=on_date_text)
        self.date_input_visible = False

        # --- Preparar labels fecha de pago adicional y monto de pago adicional, sin agregarlos aún ---
        self.label_F_P_Adicional = Label(text="fecha de pago adicional", color=self.color_texto, size_hint=(None, None), size=(150, 30))
        self.label_M_P_Adicional = Label(text="monto de pago adicional", color=self.color_texto, size_hint=(None, None), size=(150, 30))

        # **NUEVA PARTE**: Crear TextInput para monto (inicialmente oculto) con las mismas características que el TextInput de cuota
        self.monto_input = TextInput(
            text="",
            size_hint=(None, None),
            input_filter=lambda substring, from_undo: ''.join(filter(str.isdigit, substring))
        )
        # Definimos un tamaño inicial similar a cuota
        self.monto_input_initial_size = (150, 27)
        self.monto_input_visible = False

        # Bind al toggle para mostrar u ocultar el date_input y el monto_input
        def on_toggle(instance, value):
            # Actualiza el símbolo según el estado
            instance.text = '☑' if value == 'down' else '☐'

            if value == 'down':
                escala_x = 1 if Window.width == ANCHO_INICIAL else Window.width / ANCHO_INICIAL
                escala_y = 1 if Window.height == ALTO_INICIAL else Window.height / ALTO_INICIAL

                # Posicionar el label de fecha de pago adicional
                self.label_F_P_Adicional.pos = (
                    self.toggle_fecha.x - 60 * escala_x,
                    self.toggle_fecha.y - self.label_F_P_Adicional.height + 5 * escala_y
                )
                self.add_widget(self.label_F_P_Adicional)

                # Posicionar y mostrar el date_input
                self.date_input.pos = (
                    self.label_F_P_Adicional.x + 15 * escala_x,
                    self.label_F_P_Adicional.y - self.date_input.height - 5 * escala_y
                )
                if not self.date_input_visible:
                    self.add_widget(self.date_input)
                    self.date_input_visible = True

                # Posicionar el label del monto de pago adicional
                self.label_M_P_Adicional.pos = (
                    self.label_F_P_Adicional.x,
                    self.date_input.y - self.label_M_P_Adicional.height - 5 * escala_y
                )
                self.add_widget(self.label_M_P_Adicional)

                # **NUEVA PARTE**: Agregar y posicionar el monto_input justo debajo del label_M_P_Adicional, con 5px de separación
                if not self.monto_input_visible:
                    self.monto_input.pos = (
                        self.label_M_P_Adicional.x,
                        self.label_M_P_Adicional.y - self.monto_input_initial_size[1] * escala_y - 5 * escala_y
                    )
                    self.monto_input.size = (self.monto_input_initial_size[0] * escala_x, self.monto_input_initial_size[1] * escala_y)
                    self.monto_input.font_size = int(self.font_size_inicial * min(escala_x, escala_y))  # Ajuste de fuente similar a cuota
                    self.add_widget(self.monto_input)
                    self.monto_input_visible = True

                self.actualizar_distribucion(None, Window.width, Window.height)
            else:
                # Oculta los widgets adicionales
                if self.date_input_visible:
                    self.remove_widget(self.date_input)
                    self.date_input_visible = False
                if self.monto_input_visible:
                    self.remove_widget(self.monto_input)
                    self.monto_input_visible = False
                for w in (self.label_F_P_Adicional, self.label_M_P_Adicional):
                    if w.parent:
                        self.remove_widget(w)

        self.toggle_fecha.bind(state=on_toggle)

        def _actualizar_font_toggle(self, instance, new_size):
            # new_size es (width, height)
            w, h = new_size
            # Ajusta font_size al 80% de la altura (o prueba otro factor)
            instance.font_size = min(w, h) * 0.8

        # --- Fin: Agregar TextInput para fecha de pago ---

        # Ahora llamamos a actualizar_distribucion sabiendo que los atributos de fecha ya existen
        self.actualizar_distribucion(None, Window.width, Window.height)
        Window.bind(on_resize=self.actualizar_distribucion)

        # ----------------------- TextInput y label cuota ------------------------
        self.text_input = TextInput(text="", size_hint=(None, None), input_filter=lambda substring, from_undo: ''.join(filter(str.isdigit, substring)))
        initial_posicion = (635, 350)
        initial_size = (150, 27)
        self.text_input.pos = initial_posicion
        self.add_widget(self.text_input)

        altura_base = 22
        padding_vertical = 2
        altura_total = altura_base + padding_vertical * 2

        separacion = 6

        self.label_cuota = Label(
            text='Cuota Inicial',
            color=self.color_texto,
            size_hint=(None, None),
            size=(self.text_input.width, altura_total),
            padding=(0, padding_vertical)
        )
        self.add_widget(self.label_cuota)

        def update_label_cuota(*args):
            self.label_cuota.center_x = self.text_input.center_x
            self.label_cuota.y = self.text_input.top + separacion
            self.label_cuota.font_size = self.text_input.height * 0.6
            self.text_input.font_size = int(self.text_input.height * 0.6)

        self.text_input.bind(pos=update_label_cuota, size=update_label_cuota)
        update_label_cuota()

        self.dynamic_textinput = DynamicTextInput(
            text_input=self.text_input,
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
            Clock.schedule_once(do_update, 0.1)

        # Realizar los bindings correspondientes
        self.frame.bind(pos=update_buttons_pos, size=update_buttons_pos)
        update_buttons_pos()
        Window.bind(on_resize=actualizar_btns)

        self.btn_plus.bind(on_release=self.agregar_par)
        self.btn_minus.bind(on_release=self.eliminar_par)
        
        # --------------------- Botón de Configuración adaptable ---------------------
        self.btn_config = Button(size_hint=(None, None), size=(50, 50), background_normal=cargar_archivo('configuracion.png'))
        self.add_widget(self.btn_config)
        Window.bind(on_resize=self.actualizar_config_btn)
        self.actualizar_config_btn(Window, Window.width, Window.height)

    def actualizar_config_btn(self, instance, width, height):
        scale_x = width / ANCHO_INICIAL
        scale_y = height / ALTO_INICIAL
        new_width = 50 * scale_x
        new_height = 50 * scale_y
        margin_x = 10 * scale_x
        margin_y = 10 * scale_y
        self.btn_config.size = (new_width, new_height)
        self.btn_config.pos = (margin_x, margin_y)

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
        toggle_y = new_pos_label[1] - new_toggle_size[1] + 5
        self.toggle_fecha.pos = (toggle_x, toggle_y)

        # Actualizar tamaño y posición del date_input si está visible
        if self.date_input_visible:
            # Primero: Actualizar label_F_P_Adicional
            self.label_F_P_Adicional.size = (150 * escala_x, 30 * escala_y)
            self.label_F_P_Adicional.font_size = int(14 * min(escala_x, escala_y))
            self.label_F_P_Adicional.pos = (self.toggle_fecha.x - 60 * escala_x, self.toggle_fecha.y - self.label_F_P_Adicional.height + 5 * escala_y)

            # Segundo: Actualizar date_input en función de la posición de label_F_P_Adicional
            new_date_input_width = self.date_input_initial_size[0] * escala_x
            new_date_input_height = self.date_input_initial_size[1] * escala_y
            self.date_input.size = (new_date_input_width, new_date_input_height)
            self.date_input.pos = (self.label_F_P_Adicional.x + 15 * escala_x, self.label_F_P_Adicional.y - new_date_input_height - 5 * escala_y)
            nuevo_font_date = int(self.font_size_inicial * min(escala_x, escala_y) * 1.2)
            self.date_input.font_size = nuevo_font_date

            # Tercero: Actualizar label_M_P_Adicional en función de date_input
            self.label_M_P_Adicional.size = (150 * escala_x, 30 * escala_y)
            self.label_M_P_Adicional.font_size = int(14 * min(escala_x, escala_y))
            self.label_M_P_Adicional.pos = (self.label_F_P_Adicional.x, self.date_input.y - self.label_M_P_Adicional.height - 5 * escala_y)

            # **NUEVA PARTE**: Actualizar monto_input si está visible
            if self.monto_input_visible:
                new_monto_input_width = self.monto_input_initial_size[0] * escala_x
                new_monto_input_height = self.monto_input_initial_size[1] * escala_y
                self.monto_input.size = (new_monto_input_width, new_monto_input_height)
                self.monto_input.pos = (self.label_M_P_Adicional.x, self.label_M_P_Adicional.y - new_monto_input_height - 5 * escala_y)
                self.monto_input.font_size = int(self.text_input.font_size)
    
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

class MiApp(App):
    def build(self):
        Window.size = (ANCHO_INICIAL, ALTO_INICIAL)
        Window.borderless = False
        return MiWidget()

if __name__ == "__main__":
    MiApp().run()
