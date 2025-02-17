import tkinter as tk
from tkinter import filedialog
import subprocess

def select_image():
    # Abre un cuadro de diálogo para seleccionar un archivo de imagen
    file_path = filedialog.askopenfilename(
        title="Selecciona una imagen",
        filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png *.tiff *.bmp")]
    )
    
    if file_path:
        # Usa exiftool para obtener los metadatos de la imagen
        try:
            result = subprocess.run(
                ["exiftool", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error al obtener metadatos: {e}")

# Configuración de la ventana principal de tkinter
root = tk.Tk()
root.title("Visor de Metadatos de Imagen")

# Botón para seleccionar la imagen
select_button = tk.Button(root, text="Seleccionar Imagen", command=select_image)
select_button.pack(pady=20)

# Ejecuta el bucle principal de la aplicación
root.mainloop()
