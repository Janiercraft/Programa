import customtkinter as ctk
from pymongo import MongoClient
from PIL import Image
from tkinter import messagebox
import subprocess  # Importar módulo para ejecutar archivos externos

# ----------------- CONFIGURACIÓN DE LA BASE DE DATOS -----------------
# Conéctate a tu base de datos MongoDB
client = MongoClient("mongodb+srv://Janiercraft:Soy.Janiercraft.aDmin@royal-colombia.2a7ox.mongodb.net/?retryWrites=true&w=majority&appName=Royal-Colombia")
db = client["Royal"]  # Nombre de la base de datos
usuarios_collection = db["usuarios"]  # Nombre de la colección

# ----------------- FUNCIÓN PARA CENTRAR LA VENTANA -----------------
def centrar_ventana(ventana, ancho, alto):
    ventana.update_idletasks()  # Asegurar que la ventana se ha creado antes de obtener tamaño
    screen_width = ventana.winfo_screenwidth()
    screen_height = ventana.winfo_screenheight()

    x = (screen_width - ancho) // 2
    y = (screen_height - alto) // 2

    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")  # Establecer posición

# ----------------- CONFIGURACIÓN DE LA INTERFAZ -----------------
ctk.set_default_color_theme("blue")

# Detectar el modo del sistema
modo_sistema = ctk.get_appearance_mode()  # "Light" o "Dark"
print(f"Modo detectado: {modo_sistema}")

# Asignar imagen de fondo y color del texto
imagen_clara = "blanco.jpg"  # Imagen para modo claro
imagen_oscura = "blanco.jpg"   # Imagen para modo oscuro

imagen_seleccionada = imagen_clara if modo_sistema == "Light" else imagen_oscura
color_texto = "black" if modo_sistema == "Light" else "white"

# Configurar el modo de apariencia
ctk.set_appearance_mode(modo_sistema)

# Crear ventana principal
root = ctk.CTk()
root.geometry("400x170")
root.title("Login")
root.resizable(False, False)

# Centrar la ventana principal
centrar_ventana(root, 400, 170)

# Cargar y aplicar imagen de fondo
fondo = ctk.CTkImage(light_image=Image.open(imagen_seleccionada), size=(400, 170))
fondo_label = ctk.CTkLabel(root, image=fondo, text="")
fondo_label.place(x=0, y=0, relwidth=1, relheight=1)

# Hacer que el label tenga el mismo color de fondo que la ventana
label = ctk.CTkLabel(root, text="Login", font=("Arial", 14), text_color=color_texto, fg_color=root.cget("fg_color"))
label.place(x=180, y=4)

# Crear cajas de texto
textbox_usuario = ctk.CTkEntry(root, placeholder_text="Ingresar Correo")
textbox_usuario.place(x=130, y=40)

textbox_contraseña = ctk.CTkEntry(root, placeholder_text="Ingresar Contraseña", show="*")
textbox_contraseña.place(x=130, y=80)

# ----------------- FUNCIÓN PARA EJECUTAR pantalla_calculo.py -----------------
def abrir_ventana_principal():
    root.destroy()  # Oculta la ventana de login
    subprocess.run(["python", "pantalla_calculo.py"])  # Ejecuta pantalla_calculo.py

# ----------------- FUNCIÓN DE AUTENTICACIÓN -----------------
def on_button_click():
    correo = textbox_usuario.get()
    contraseña = textbox_contraseña.get()

    usuario = usuarios_collection.find_one({"email": correo})

    if not usuario:
        messagebox.showerror("Error", "Usuario no encontrado.")
        return

    if usuario["contraseña"] != contraseña:
        messagebox.showerror("Error", "Contraseña incorrecta.")
        return

    if "plan" not in usuario or not usuario["plan"]:
        messagebox.showerror("Error", "No está registrado en un plan.")
        return

    abrir_ventana_principal()

# Crear botón de login
boton = ctk.CTkButton(root, text="Ingresar", command=on_button_click)
boton.place(x=130, y=120)

# Ejecutar la aplicación
root.mainloop()
