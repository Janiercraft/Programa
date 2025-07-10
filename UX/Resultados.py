from kivy.config import Config
# Desactiva el provider de lápiz digital (wm_pen)
Config.set('kivy', 'input_exclude', 'wm_pen')
# Desactiva el multitouch simulado con el mouse
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.uix.floatlayout    import FloatLayout
from kivy.graphics            import Rectangle
from kivy.uix.label           import Label
from kivy.uix.button          import Button
from kivy.core.window         import Window
from kivy.properties          import NumericProperty, StringProperty
from kivy.uix.screenmanager   import Screen
from kivy.app                 import App

from Clases_y_Funciones.Clases.botonToggleCustomizado import CustomToggleButton
from Clases_y_Funciones.Clases.gestion_recursos        import Recursos
from Clases_y_Funciones.Clases.GestionTasas            import GestionTasas

class ResultadosWidget(FloatLayout):
    # Propiedades que enlazamos a los labels
    precio_compra        = NumericProperty(0)
    precio_total         = NumericProperty(0)
    deposito_pagado      = NumericProperty(0)
    saldo_a_financiar    = NumericProperty(0)
    fecha_pago_adicional = StringProperty("")
    deposito_adicional   = NumericProperty(0)
    estado_deposito      = StringProperty("normal")
    estado_pago_total    = StringProperty("normal")
    meses_plazo          = NumericProperty(0)
    pago_minimo_mensual  = NumericProperty(0)

    def __init__(self,
                 precio_compra=0,
                 precio_total=0,
                 deposito_pagado=0,
                 fecha_pago_adicional="",
                 saldo_a_financiar=0,
                 deposito_adicional=0,
                 estado_deposito="normal",
                 estado_pago_total="normal",
                 meses_plazo=0,
                 pago_minimo_mensual=0,
                 **kwargs):
        super().__init__(**kwargs)

        # Fondo fijo o escalable
        with self.canvas.before:
            self.rect = Rectangle(
                source=Recursos.ruta('calculos.jpg'),
                pos=self.pos, size=self.size
            )
        self.bind(pos=self._update_fondo, size=self._update_fondo)

        # Servicio de tasas
        self._tasas_service = GestionTasas(
            db_name='Royal',
            collection_name='tasas de interes'
        )

        # Construcción de widgets y bindings
        self._create_widgets()
        self._bind_properties()
        self._aplicar_tasas()

        # Inicializamos propiedades con los valores recibidos
        self.precio_compra        = precio_compra
        self.precio_total         = precio_total
        self.deposito_pagado      = deposito_pagado
        self.fecha_pago_adicional = fecha_pago_adicional
        self.saldo_a_financiar    = saldo_a_financiar
        self.deposito_adicional   = deposito_adicional
        self.estado_deposito      = estado_deposito
        self.estado_pago_total    = estado_pago_total
        self.meses_plazo          = meses_plazo
        self.pago_minimo_mensual  = pago_minimo_mensual

        # Adaptamos tamaño de letra al redimensionar
        Window.bind(on_resize=self._on_window_resize)
        self.bind(size=self._on_window_resize)

    def _update_fondo(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _create_widgets(self):
        # Definición con hints: (nombre atributo, texto inicial, size_hint, pos_hint)
        hints = [
            ('precio_compra_lbl',   '',     (0.2, 0.125), {'x':0.76, 'y':0.885}),
            ('costo_envio_lbl',     '0',    (0.2, 0.125), {'x':0.76, 'y':0.81}),
            ('iva_lbl',             'IVA',  (0.2, 0.125), {'x':0.76, 'y':0.74}),
            ('precio_total_lbl',    '',     (0.2, 0.125), {'x':0.76, 'y':0.67}),
            ('deposito_hoy_lbl',    '',     (0.2, 0.125), {'x':0.76, 'y':0.60}),
            ('deposito_add_lbl',    '',     (0.2, 0.125), {'x':0.76, 'y':0.49}),
            ('fecha_pago_lbl',      '',     (0.3, 0.125), {'x':0.15, 'y':0.49}),
            ('saldo_financiar_lbl', '',     (0.2, 0.125), {'x':0.76, 'y':0.375}),
            ('tasa_ea_lbl',         'T.',   (0.2, 0.125), {'x':0.76, 'y':0.30}),
            ('interes_vigente_lbl', '',     (0.2, 0.125), {'x':0.76, 'y':0.225}),
            ('cuotas_mensuales_lbl','',     (0.2, 0.125), {'x':0.76, 'y':0.15}),
            ('pago_minimo_lbl',     '',     (0.2, 0.125), {'x':0.76, 'y':0.075}),
        ]
        for name, text, size_hint, pos_hint in hints:
            lbl = Label(
                text=text,
                size_hint=size_hint,
                pos_hint=pos_hint,
                color=(0, 0, 0, 1)
            )
            setattr(self, name, lbl)
            self.add_widget(lbl)

        # Toggles y sus etiquetas
        self.toggle_deposito = CustomToggleButton(
            size_hint=(0.025, 0.05),
            pos_hint={'x':0.73, 'y':0.025},
            readonly=True
        )
        self.add_widget(self.toggle_deposito)
        self.label_toggle_deposito = Label(
            text='DEPÓSITO',
            size_hint=(0.1, 0.06),
            pos_hint={'x':0.75, 'y':0.02},
            color=(0, 0, 0, 1)
        )
        self.add_widget(self.label_toggle_deposito)

        self.toggle_pago = CustomToggleButton(
            size_hint=(0.025, 0.05),
            pos_hint={'x':0.85, 'y':0.025},
            readonly=True
        )
        self.add_widget(self.toggle_pago)
        self.label_toggle_pago = Label(
            text='PAGO TOTAL',
            size_hint=(0.15, 0.06),
            pos_hint={'x':0.855, 'y':0.02},
            color=(0, 0, 0, 1)
        )
        self.add_widget(self.label_toggle_pago)

        # ——— Botón “Volver” ———
        self.boton_volver = Button(
            text="Volver",
            size_hint=(0.08, 0.08),
            pos_hint={'center_x': 0.5, 'y': 0.02}
        )
        self.boton_volver.bind(on_release=self._volver)
        self.add_widget(self.boton_volver)

    def _bind_properties(self):
        self.bind(
            precio_compra        = self._on_precio_compra,
            precio_total         = self._on_precio_total,
            deposito_pagado      = self._on_deposito_pagado,
            fecha_pago_adicional = self._on_fecha_pago,
            saldo_a_financiar    = self._on_saldo_financiar,
            deposito_adicional   = self._on_deposito_add,
            estado_deposito      = self._update_toggle_deposito,
            estado_pago_total    = self._update_toggle_pago,
            meses_plazo          = self._on_meses_plazo,
            pago_minimo_mensual  = self._on_pago_minimo
        )

    def _aplicar_tasas(self):
        tasas = self._tasas_service.obtener_tasas()
        self.iva_lbl.text             = f"{int(tasas['iva'])}%"
        self.tasa_ea_lbl.text         = f"{tasas['anual']}%"
        self.interes_vigente_lbl.text = f"{tasas['mensual']}%"

    def _on_window_resize(self, instance, size):
        scale = min(size)
        font_sz = max(12, int(scale * 0.03))
        for lbl in [
            self.precio_compra_lbl, self.costo_envio_lbl, self.iva_lbl,
            self.precio_total_lbl, self.deposito_hoy_lbl, self.deposito_add_lbl,
            self.fecha_pago_lbl, self.saldo_financiar_lbl, self.tasa_ea_lbl,
            self.interes_vigente_lbl, self.cuotas_mensuales_lbl, self.pago_minimo_lbl,
            self.label_toggle_deposito, self.label_toggle_pago
        ]:
            lbl.font_size = f"{font_sz}sp"

    # Callbacks para actualizar texto de cada label
    def _on_precio_compra(self, inst, value):
        self.precio_compra_lbl.text = f"{value:,.0f}".replace(',', '.')
    def _on_precio_total(self, inst, value):
        self.precio_total_lbl.text  = f"{value:,.0f}".replace(',', '.')
    def _on_deposito_pagado(self, inst, value):
        self.deposito_hoy_lbl.text  = f"{value:,.0f}".replace(',', '.')
    def _on_deposito_add(self, inst, value):
        self.deposito_add_lbl.text  = f"{value:,.0f}".replace(',', '.') if value else ''
    def _on_fecha_pago(self, inst, value):
        self.fecha_pago_lbl.text    = value
    def _on_saldo_financiar(self, inst, value):
        self.saldo_financiar_lbl.text = f"{value:,.0f}".replace(',', '.')
    def _on_meses_plazo(self, inst, value):
        self.cuotas_mensuales_lbl.text = str(value)
    def _on_pago_minimo(self, inst, value):
        self.pago_minimo_lbl.text   = f"{value:,.0f}".replace(',', '.')
    def _update_toggle_deposito(self, inst, state):
        self.toggle_deposito.state = state
    def _update_toggle_pago(self, inst, state):
        self.toggle_pago.state = state

    def _volver(self, instance):
        """
        Cambia la pantalla de 'resultados' de vuelta a 'calculo'.
        """
        App.get_running_app().root.current = 'calculo'


class ResultadosScreen(Screen):
    """
    Pantalla que contiene dinámicamente el ResultadosWidget.
    """
    def __init__(self, **kwargs):
        super().__init__(name='resultados', **kwargs)

    def display_results(self, resultados: dict):
        """
        Limpia la pantalla y muestra un nuevo ResultadosWidget
        inicializado con el dict de resultados.
        """
        print("🔔 [Resultados] display_results recibió:", resultados)
        self.clear_widgets()
        widget = ResultadosWidget(
            precio_compra        = resultados["precio_compra"],
            precio_total         = resultados["precio_total"],
            deposito_pagado      = resultados["deposito_pagado"],
            saldo_a_financiar    = resultados["saldo_a_financiar"],
            fecha_pago_adicional = resultados["fecha_pago_adicional"],
            deposito_adicional   = resultados["deposito_adicional"],
            estado_deposito      = resultados["estado_deposito"],
            estado_pago_total    = resultados["estado_pago_total"],
            meses_plazo          = resultados["meses_plazo"],
            pago_minimo_mensual  = resultados["pago_minimo_mensual"]
        )
        self.add_widget(widget)