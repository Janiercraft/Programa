from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch','kivy', 'input_exclude', 'wm_pen')
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Rectangle
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty
from Clases_y_Funciones.Clases.botonToggleCustomizado import CustomToggleButton
from Clases_y_Funciones.Clases.gestion_recursos import Recursos
from Clases_y_Funciones.Clases.GestionTasas import GestionTasas

class ResultadosWidget(FloatLayout):
    precio_compra = NumericProperty(0)
    precio_total = NumericProperty(0)
    deposito_pagado = NumericProperty(0)
    saldo_a_financiar   = NumericProperty(0)  
    fecha_pago_adicional = StringProperty("")
    deposito_adicional = NumericProperty(0)
    estado_deposito = StringProperty("normal")
    estado_pago_total = StringProperty("normal")
    meses_plazo         = NumericProperty(0)
    pago_minimo_mensual = NumericProperty(0)

    def __init__(self, precio_compra=0, precio_total=0,
                 deposito_pagado=0, fecha_pago_adicional="", saldo_a_financiar=0,
                 deposito_adicional=0, estado_deposito="normal",
                 estado_pago_total="normal", meses_plazo=0, pago_minimo_mensual=0, **kwargs):
        super().__init__(**kwargs)
        # Fondo escalable
        with self.canvas.before:
            self.rect = Rectangle(source=Recursos.ruta('calculos.jpg'), pos=self.pos, size=self.size)
        self.bind(pos=self._update_fondo, size=self._update_fondo)
        self.bind(size=self._on_window_resize)
        Window.bind(on_resize=lambda *_: self._on_window_resize(self, self.size))

        # Crear Labels y Toggles
        self._create_widgets()

        # Bind properties a actualizaciones
        self._bind_properties()

        # Servicio de tasas y valores iniciales
        self._tasas_service = GestionTasas(db_name='Royal', collection_name='tasas de interes')
        self._aplicar_tasas()
        self.precio_compra = precio_compra
        self.precio_total = precio_total
        self.deposito_pagado = deposito_pagado
        self.deposito_adicional = deposito_adicional
        self.fecha_pago_adicional = fecha_pago_adicional
        self.saldo_a_financiar   = saldo_a_financiar
        self.estado_deposito = estado_deposito
        self.estado_pago_total = estado_pago_total
        self.meses_plazo = meses_plazo
        self.pago_minimo_mensual  = pago_minimo_mensual

    def _create_widgets(self):
        # Definición con hints
        hints = [
            ('precio_compra_lbl', '', (0.2,0.125), {'x':0.76,'y':0.885}),
            ('costo_envio_lbl', '0', (0.2,0.125), {'x':0.76,'y':0.81}),
            ('iva_lbl', 'IVA', (0.2,0.125), {'x':0.76,'y':0.74}),
            ('precio_total_lbl', '', (0.2,0.125), {'x':0.76,'y':0.67}),
            ('deposito_hoy_lbl', '', (0.2,0.125), {'x':0.76,'y':0.60}),
            ('deposito_add_lbl', '', (0.2,0.125), {'x':0.76,'y':0.49}),
            ('fecha_pago_lbl', '', (0.3,0.125), {'x':0.15,'y':0.49}),
            ('saldo_financiar_lbl', '', (0.2,0.125), {'x':0.76,'y':0.375}),
            ('tasa_ea_lbl', 'T.', (0.2,0.125), {'x':0.76,'y':0.30}),
            ('interes_vigente_lbl', '', (0.2,0.125), {'x':0.76,'y':0.225}),
            ('cuotas_mensuales_lbl', '', (0.2,0.125), {'x':0.76,'y':0.15}),
            ('pago_minimo_lbl', '', (0.2,0.125), {'x':0.76,'y':0.075}),
        ]
        for name, text, size_hint, pos_hint in hints:
            lbl = Label(text=text, size_hint=size_hint, pos_hint=pos_hint, color=(0,0,0,1))
            setattr(self, name, lbl)
            self.add_widget(lbl)

        # Toggles
        self.toggle_deposito = CustomToggleButton(size_hint=(0.025,0.05), pos_hint={'x':0.73,'y':0.025}, readonly=True)
        self.add_widget(self.toggle_deposito)
        self.label_toggle_deposito = Label(text='DEPÓSITO', size_hint=(0.1,0.06), pos_hint={'x':0.75,'y':0.02}, color=(0, 0, 0, 1))
        self.add_widget(self.label_toggle_deposito)
        self.toggle_pago = CustomToggleButton(size_hint=(0.025,0.05), pos_hint={'x':0.85,'y':0.025}, readonly=True)
        self.add_widget(self.toggle_pago)
        self.label_toggle_pago = Label(text='PAGO TOTAL', size_hint=(0.15,0.06), pos_hint={'x':0.855,'y':0.02}, color=(0, 0, 0, 1))
        self.add_widget(self.label_toggle_pago)

    def _bind_properties(self):
        self.bind(precio_compra=self._on_precio_compra,
                  precio_total=self._on_precio_total,
                  deposito_pagado=self._on_deposito_pagado,
                  fecha_pago_adicional=self._on_fecha_pago,
                  saldo_a_financiar=self._on_saldo_financiar,
                  deposito_adicional=self._on_deposito_add,
                  estado_deposito=self._update_toggle_deposito,
                  estado_pago_total=self._update_toggle_pago,
                  meses_plazo=self._on_meses_plazo,
                  pago_minimo_mensual=self._on_pago_minimo)

    def _update_fondo(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _on_window_resize(self, instance, size):
        # Calcular escala basada en ancho o alto
        scale = min(size)
        # Ajustar font_size dinámicamente
        for lbl in [
            self.precio_compra_lbl, self.costo_envio_lbl, self.iva_lbl,
            self.precio_total_lbl, self.deposito_hoy_lbl, self.deposito_add_lbl,
            self.fecha_pago_lbl, self.saldo_financiar_lbl, self.tasa_ea_lbl,
            self.interes_vigente_lbl, self.cuotas_mensuales_lbl, self.pago_minimo_lbl,
            self.label_toggle_deposito, self.label_toggle_pago
        ]:
            lbl.font_size = f"{max(12, int(scale * 0.03))}sp"

    def _aplicar_tasas(self):
        tasas = self._tasas_service.obtener_tasas()
        self.iva_lbl.text = f"{int(tasas['iva'])}%"
        self.tasa_ea_lbl.text = f"{tasas['anual']}%"
        self.interes_vigente_lbl.text = f"{tasas['mensual']}%"

    def _on_precio_compra(self, instance, value):
        self.precio_compra_lbl.text = f"{value:,.0f}".replace(',', '.')

    def _on_precio_total(self, instance, value):
        self.precio_total_lbl.text = f"{value:,.0f}".replace(',', '.')

    def _on_deposito_pagado(self, instance, value):
        self.deposito_hoy_lbl.text = f"{value:,.0f}".replace(',', '.')

    def _on_deposito_add(self, instance, value):
        text = f"{value:,.0f}".replace(',', '.')
        self.deposito_add_lbl.text = text if value else ''

    def _on_fecha_pago(self, instance, value):
        self.fecha_pago_lbl.text = value

    def _on_saldo_financiar(self, instance, value):
        self.saldo_financiar_lbl.text = f"{value:,.0f}".replace(',', '.')

    def _on_meses_plazo(self, instance, value):
        self.cuotas_mensuales_lbl.text = str(value)
    
    def _on_pago_minimo(self, instance, value):
        """
        Actualiza el Label 'pago_minimo_lbl' con el valor formateado.
        """
        # Formateamos sin decimales y con separador de miles
        texto = f"{value:,.0f}".replace(',', '.')
        self.pago_minimo_lbl.text = texto

    def _update_toggle_deposito(self, instance, state):
        self.toggle_deposito.state = state

    def _update_toggle_pago(self, instance, state):
        self.toggle_pago.state = state
