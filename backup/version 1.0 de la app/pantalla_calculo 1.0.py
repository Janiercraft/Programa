import customtkinter as ctk
from tkinter import ttk
from pymongo import MongoClient
import json
import os

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pantalla Principal")
        self.geometry("800x400")

        self.db_file = "productos_local.json"

        # Cargar datos según la configuración de actualizaciones
        self.productos = self.cargar_datos()
        self.codigos = [p["CODIGO"] for p in self.productos]
        self.descripciones = [p["DESCRIPCION DEL PRODUCTO"] for p in self.productos]

        # Contenedor principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill='both', expand=True)

        # Frame con barra lateral
        self.scrollable_frame = ctk.CTkScrollableFrame(main_frame, width=500, height=250)
        self.scrollable_frame.pack(side="left", fill='y', expand=False)

        # Lista para almacenar los pares de entradas
        self.entries = []
        self.add_entry()

        # Frame para cuota inicial
        cuota_frame = ctk.CTkFrame(main_frame)
        cuota_frame.pack(side="top", anchor="ne", padx=40, pady=3)
        
        self.cuota_label = ctk.CTkLabel(cuota_frame, text="Cuota Inicial")
        self.cuota_label.pack()
        
        self.cuota_entry = ctk.CTkEntry(cuota_frame)
        self.cuota_entry.pack()

        # Frame para botones
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(side="top", pady=70)

        self.add_button = ctk.CTkButton(btn_frame, text="+", command=self.add_entry)
        self.add_button.pack(side="left", padx=5)

        self.remove_button = ctk.CTkButton(btn_frame, text="-", command=self.remove_entry)
        self.remove_button.pack(side="left", padx=5)

        # Botón Procesar fuera del frame
        self.bottom_button = ctk.CTkButton(self, text="Procesar", command=self.placeholder_function)
        self.bottom_button.pack(pady=20)

    def cargar_datos(self):
        """Carga los datos de MongoDB si es necesario, sino usa el archivo local."""
        # Si el archivo local existe, cargarlo como respaldo
        if os.path.exists(self.db_file):
            with open(self.db_file, "r", encoding="utf-8") as f:
                productos_locales = json.load(f)
        else:
            productos_locales = []
        
        try:
            client = MongoClient("mongodb+srv://Janiercraft:Soy.Janiercraft.aDmin@royal-colombia.2a7ox.mongodb.net/?retryWrites=true&w=majority&appName=Royal-Colombia", serverSelectionTimeoutMS=5000)
            db = client["Royal"]
            
            # Verificar si el usuario tiene activadas las actualizaciones
            usuario = db["usuarios"].find_one({"email": "janier@email.com"})
            if usuario and usuario.get("actualizaciones", True):
                productos = list(db["productos"].find({}, {"CODIGO": 1, "DESCRIPCION DEL PRODUCTO": 1, "_id": 0}))
                
                # Guardar los datos en local
                with open(self.db_file, "w", encoding="utf-8") as f:
                    json.dump(productos, f, ensure_ascii=False, indent=4)
                return productos
            else:
                return productos_locales
        except:
            return productos_locales

    def add_entry(self):
        """Agrega un nuevo par de Combobox (Código - Descripción)"""
        frame = ctk.CTkFrame(self.scrollable_frame)
        frame.pack(fill='x', pady=5)

        code_frame = ctk.CTkFrame(frame)
        code_frame.pack(side="left", padx=5, expand=True, fill='x')

        code_label = ctk.CTkLabel(code_frame, text="Código")
        code_label.pack()
        
        code_entry = ttk.Combobox(code_frame, values=self.codigos)
        code_entry.pack(fill='x')
        code_entry.bind("<KeyRelease>", lambda event, entry=code_entry: self.dynamic_autocomplete(event, entry, self.codigos))
        code_entry.bind("<<ComboboxSelected>>", lambda event, entry=code_entry: self.fill_description(entry))

        desc_frame = ctk.CTkFrame(frame)
        desc_frame.pack(side="left", padx=5, expand=True, fill='x')

        desc_label = ctk.CTkLabel(desc_frame, text="Descripción del Producto")
        desc_label.pack()
        
        desc_entry = ttk.Combobox(desc_frame, values=self.descripciones)
        desc_entry.pack(fill='x')
        desc_entry.bind("<KeyRelease>", lambda event, entry=desc_entry: self.dynamic_autocomplete(event, entry, self.descripciones))
        desc_entry.bind("<<ComboboxSelected>>", lambda event, entry=desc_entry: self.fill_code(entry))
        
        self.entries.append((frame, code_entry, desc_entry))

    def dynamic_autocomplete(self, event, entry, values):
        """Filtra las opciones en la combobox según lo que el usuario escriba."""
        typed = entry.get()
        if typed == "":
            entry["values"] = values
        else:
            entry["values"] = [v for v in values if typed.lower() in v.lower()]

    def fill_description(self, code_entry):
        """Llena la descripción cuando se selecciona un código."""
        selected_code = code_entry.get()
        for p in self.productos:
            if p["CODIGO"] == selected_code:
                desc_entry = next((desc for frame, code, desc in self.entries if code is code_entry), None)
                if desc_entry:
                    desc_entry.delete(0, "end")
                    desc_entry.insert(0, p["DESCRIPCION DEL PRODUCTO"])
                break

    def fill_code(self, desc_entry):  
        """Llena el código cuando se selecciona una descripción."""
        selected_desc = desc_entry.get()
        for p in self.productos:
            if p["DESCRIPCION DEL PRODUCTO"] == selected_desc:
                code_entry = next((code for frame, code, desc in self.entries if desc is desc_entry), None)
                if code_entry:
                    code_entry.delete(0, "end")
                    code_entry.insert(0, p["CODIGO"])
                break

    def remove_entry(self):
        """Elimina el último par de Combobox."""
        if self.entries:
            entry = self.entries.pop()
            entry[0].destroy()

    def placeholder_function(self):
        """Función vacía para programar después."""
        pass

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
