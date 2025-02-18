import tkinter as tk
from tkinter import filedialog
import subprocess
import json
import os

def select_image():
    
    file_path = filedialog.askopenfilename(
        title="Selecciona una imagen",)
    base_name = os.path.basename(file_path)
    metadata_folder = os.path.join(os.path.dirname(file_path), "metadata")
    os.makedirs(metadata_folder, exist_ok=True)
    metadata_file_path = os.path.join(metadata_folder, base_name.replace(".JPG", ".txt"))
    
    if file_path:
        # Usa exiftool para obtener los metadatos de la imagen
        try:
            result = subprocess.run(
                ["exiftool", "-j", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Convierte la salida JSON a un diccionario de Python
            metadata = json.loads(result.stdout)
            
            # Guarda los metadatos en un archivo JSON con el mismo nombre que la imagen
            with open(metadata_file_path, 'w') as metadata_file:
                json.dump(metadata[0], metadata_file, ensure_ascii=False, indent=4)
                
        except subprocess.CalledProcessError as e:
            print(f"Error al obtener metadatos: {e}")
            
def select_folder():
    folder_path = filedialog.askdirectory(
        title="Selecciona una carpeta"
    )
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        base_name = os.path.basename(file_path)
        metadata_folder = os.path.join(os.path.dirname(file_path), "metadata")
        os.makedirs(metadata_folder, exist_ok=True)
        metadata_file_path = os.path.join(metadata_folder, base_name.replace(".jpg", ".txt"))
        
        if file_path:
            # Usa exiftool para obtener los metadatos de la imagen
            try:
                result = subprocess.run(
                    ["exiftool", "-j", file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Convierte la salida JSON a un diccionario de Python
                metadata = json.loads(result.stdout)
                
                # Guarda los metadatos en un archivo JSON con el mismo nombre que la imagen
                with open(metadata_file_path, 'w') as metadata_file:
                    json.dump(metadata[0], metadata_file, ensure_ascii=False, indent=4)
                    
            except subprocess.CalledProcessError as e:
                print(f"Error al obtener metadatos: {e}")




if __name__ == "__main__":
  
    # Configuración de la ventana principal de tkinter
    root = tk.Tk()
    root.title("Visor de Metadatos de Imagen")

    # Botón para seleccionar la imagen
    select_button = tk.Button(root, text="Seleccionar Imagen", command=select_image)
    select_button.pack(pady=20)
    
    select_folder_button = tk.Button(root, text="Seleccionar Carpeta", command=select_folder)
    select_folder_button.pack(pady=20)


    # Ejecuta el bucle principal de la aplicación
    root.mainloop()
