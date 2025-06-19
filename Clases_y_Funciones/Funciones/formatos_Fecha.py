from kivy.clock import Clock

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