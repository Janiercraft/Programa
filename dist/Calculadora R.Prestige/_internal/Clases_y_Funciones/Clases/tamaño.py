#Ancho de ventana inicial
from kivy.config import Config

ANCHO_INICIAL = 800  
ALTO_INICIAL = 400 

Config.set('graphics', 'width', str(ANCHO_INICIAL))
Config.set('graphics', 'height', str(ALTO_INICIAL))
Config.set('graphics', 'resizable', True)

#cambiar tamaño del date input
date_input_size = (120, 30)
