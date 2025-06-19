from kivy.clock import Clock
from kivy.uix.textinput import TextInput

class ThousandSeparatorTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self._updating_text = False  # Bandera para evitar llamadas recursivas
        self.bind(text=self._format_text)

    def _format_text(self, instance, value):
        if self._updating_text:
            return  # Evitar reentradas
        self._updating_text = True

        # Extraer dígitos de la entrada
        digits = ''.join(filter(str.isdigit, value))
        # Limitar a 9 dígitos
        if len(digits) > 9:
            digits = digits[:9]

        if digits:
            try:
                formatted = "{:,}".format(int(digits)).replace(",", ".")
            except ValueError:
                formatted = digits
        else:
            formatted = ""
            
        # Solo actualizamos si hay diferencia para evitar bucles
        if formatted != value:
            self.text = formatted
            # Reposicionar el cursor al final después de actualizar el texto
            Clock.schedule_once(lambda dt: setattr(self, 'cursor', (len(formatted), 0)), 0)

        self._updating_text = False