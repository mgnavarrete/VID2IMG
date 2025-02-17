from tkinter import filedialog, Tk, Button, Label
import os
import re
import json  
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import time  # Importar el módulo time
from tqdm import tqdm
from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
import time
from PIL import Image  # Importar la biblioteca Pillow
import imageio
import sys
from PyQt5.QtGui import QImage  # Asegúrate de importar QImage
from PIL import ImageQt  # Importar ImageQt para la conversión
from PIL import ImageDraw
import shutil
from cvat_sdk import make_client, models
from cvat_sdk.core.proxies.tasks import ResourceType, Task
import zipfile


class SelectFrames(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.labels_data= {
                            "Aislador-Quebrado": 14,
                            "Aislador-Contaminado": 15,
                            "Aislador-Corrosión": 16,
                            "Aislador-Excremento": 17,
                            "Aislador-Daño recubrimiento": 36,
                            "Aislador-Desalineado": 37,
                            "Aislador-Chaveta desplazada": 38,
                            "Amortiguador-Doblado": 39,
                            "Amortiguador-Roto": 40,
                            "Amortiguador-Corrosión": 41,
                            "Baliza-Abrazadera rota": 42,
                            "Baliza-Corrosión": 43,
                            "Baliza-Pintura": 44,
                            "Cable puente-Corrosión": 45,
                            "Cable puente-Hebra cortada": 46,
                            "Conductor-Corrosión": 52,
                            "Conductor-Elemento extraño": 53,
                            "Conductor-Hebra cortada": 54,
                            "Cruceta-Corrosión en placa de anclaje": 55,
                            "Cruceta-Corrosión": 56,
                            "Cruceta-Deformación": 57,
                            "Estructura-Contaminación": 58,
                            "Estructura-Corrosión": 59,
                            "Estructura-Torcida": 60,
                            "Estructura-Elemento extraño": 61,
                            "Fundación-Problema en fundación": 62,
                            "Peldaños escalada-Corrosión": 63,
                            "Abrazadera de suspensión-Corrosión": 64,
                            "Herrajes de suspensión-Corrosión": 65,
                            "Grillete/eslabón-Corrosión": 66,
                            "Tensores/Soportes-Doblados": 67,
                            "Herrajes de tensión-Corrosión": 68,
                            "Pernos y tuercas-Corrosión": 69,
                            "Cable guardia-Corrosión en anclaje": 70,
                            "Dispositivo anti aves-Problemas": 71,
                            "Señalización-Corrosión": 72,
                            "Señalización-Inexistente": 73
                        }
        self.initUI()
        self.frames = []  # Lista para almacenar los frames
        self.data_frame = None
        self.current_frame_index = 0  # Índice del frame actual
        self.pause = True
        self.timer = QTimer(self)  # Crear un temporizador
        self.timer.timeout.connect(self.next_frame)  # Conectar el temporizador a la función next_frame
        self.bbox = []  # Lista para almacenar las coordenadas del bbox
        self.drawing = False  # Bandera para saber si se está dibujando
        self.start_point = None  # Punto inicial del bbox
        self.end_point = None  # Punto final del bbox
        self.frames_saved = 0
        

    def initUI(self):
        self.setWindowTitle("Seleccion de hallazgos")
        self.setMinimumWidth(1600)
        # layout
        layout = QtWidgets.QVBoxLayout()

        # Visualizador de frames
        self.frame_layout = QtWidgets.QHBoxLayout()
        self.frame_label = QtWidgets.QLabel(self)
        self.frame_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.frame_label.setMinimumSize(1500, 800)  # Establecer un tamaño mínimo para el QLabel
        self.frame_label.setAlignment(QtCore.Qt.AlignCenter)  # Centrar el QLabel
        self.frame_layout.addWidget(self.frame_label, alignment=QtCore.Qt.AlignCenter)  # Asegurar que el QLabel esté centrado
        layout.addLayout(self.frame_layout)

        self.select_label = QtWidgets.QLabel("Selecciona el tipo de hallazgo:", self)
        layout.addWidget(self.select_label)
        
        self.select_layout = QtWidgets.QHBoxLayout()
        self.select_dropdown = QtWidgets.QComboBox(self)
        self.select_dropdown.setMaxVisibleItems(10)  # Limitar el número de elementos visibles
        self.select_dropdown.setView(QtWidgets.QListView())  # Establecer un QListView para permitir el desplazamiento
        for key, value in self.labels_data.items():
            self.select_dropdown.addItem(key)
        self.select_layout.addWidget(self.select_dropdown)


        self.save_button = QtWidgets.QPushButton("Guardar Hallazgo", self)
        self.save_button.clicked.connect(self.save_hallazgo)
        self.select_layout.addWidget(self.save_button)
        
        layout.addLayout(self.select_layout)



        # Botones de control
        control_layout = QtWidgets.QHBoxLayout()
        self.prev_button = QtWidgets.QPushButton("Anterior", self)
        self.pause_button = QtWidgets.QPushButton("Iniciar Video", self)
        self.pause_button.clicked.connect(self.pause_frame)
        self.next_button = QtWidgets.QPushButton("Siguiente", self)
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.next_button)
        layout.addLayout(control_layout)

        self.cerrar_button = QtWidgets.QPushButton("Terminar", self)
        self.cerrar_button.clicked.connect(self.close)
        layout.addWidget(self.cerrar_button)
        
        self.info_layout = QtWidgets.QHBoxLayout()
        self.info_label = QtWidgets.QLabel(f"")
        self.info_layout.addWidget(self.info_label)
        layout.addLayout(self.info_layout)

    
        self.frame_label.mousePressEvent = self.start_drawing
        self.frame_label.mouseReleaseEvent = self.end_drawing
        self.frame_label.mouseMoveEvent = self.update_drawing
        
        # Conectar botones a funciones
        self.prev_button.clicked.connect(self.show_previous_frame)
        self.next_button.clicked.connect(self.show_next_frame)

        self.setLayout(layout)
        
                

    def start_drawing(self, event):
        self.drawing = True
        self.start_point = event.pos()

    def update_drawing(self, event):
        if self.drawing:
            self.end_point = event.pos()
            self.update()

    def end_drawing(self, event):
        self.drawing = False
        self.end_point = event.pos()
        
        # Calcular la relación de escala entre el QLabel y la imagen original
        label_width = self.frame_label.width()
        label_height = self.frame_label.height()
        image_width = self.data_frame.width
        image_height = self.data_frame.height
        
        scale_x = image_width / label_width
        scale_y = image_height / label_height
        
        # Determinar cual es el punto mas alto y mas bajo
        if self.start_point.y() > self.end_point.y():
            y1 = self.end_point.y()
            y2 = self.start_point.y()
        else:
            y1 = self.start_point.y()
            y2 = self.end_point.y()
        
        if self.start_point.x() > self.end_point.x():
            x1 = self.end_point.x()
            x2 = self.start_point.x()
        else:
            x1 = self.start_point.x()
            x2 = self.end_point.x()
        

        # Ajustar las coordenadas del bbox para que sean relativas a la imagen original
        self.bbox = [
            int(x1 * scale_x),
            int(y1 * scale_y),
            int(x2 * scale_x),
            int(y2 * scale_y)
        ]
        
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.start_point and self.end_point:
            # Crear un nuevo QPixmap basado en el pixmap escalado actual
            pixmap = self.scaled_pixmap.copy()
            
            # Dibujar el rectángulo en el nuevo pixmap
            painter = QtGui.QPainter(pixmap)
            pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(QtCore.QRect(self.start_point, self.end_point))
            painter.end()

            # Establecer el pixmap en el QLabel
            self.frame_label.setPixmap(pixmap)

    def save_hallazgo(self):
        if self.bbox == []:
            self.info_label.setText(f"No se ha seleccionado ningún hallazgo")
            return
        x1, y1, x2, y2 = self.bbox
        width, height = self.data_frame.size
        if x2 > width or y2 > height or x1 < 0 or y1 < 0:
            self.info_label.setText("El bbox está fuera de los límites de la imagen o es inválido. Por favor, marque nuevamente.")
            return
        else:
            self.frames_saved += 1
            # Aquí puedes agregar lógica para guardar el bbox en un archivo o base de datos
            frame_path = self.frames[self.current_frame_index]
            base_name = os.path.basename(frame_path).replace(".jpg", "")
            base_name = base_name.split("_")[:-1]
            base_name = "_".join(base_name)
            dir_path = os.path.dirname(frame_path).split("/")[:-1]
            dir_path = "/".join(dir_path)
            base_name = f"{base_name}_{str(self.frames_saved).zfill(3)}"
            
            labels_path = os.path.join(dir_path, "labels")
            frames_path = os.path.join(dir_path, "frames")
            draw_path = os.path.join(dir_path, "draw")
            print(frame_path)
            print(dir_path)
            os.makedirs(labels_path, exist_ok=True)
            os.makedirs(frames_path, exist_ok=True)
            os.makedirs(draw_path, exist_ok=True)
            shutil.copy(frame_path, os.path.join(frames_path, f"{base_name}.jpg"))
            
            frame = Image.open(frame_path)
            draw = ImageDraw.Draw(frame)
            x1, y1, x2, y2 = self.bbox
            width, height = frame.size
            # Calcular x_center, y_center, width, height para el formato YOLO 1.1
            x_center = ((x1 + x2) / 2) / width
            y_center = ((y1 + y2) / 2) / height
            bbox_width = (x2 - x1) / width
            bbox_height = (y2 - y1) / height
            
            with open(os.path.join(labels_path, f"{base_name}.txt"), "w") as f:
                f.write(f"{self.labels_data[self.select_dropdown.currentText()]} {x_center} {y_center} {bbox_width} {bbox_height}")
            
            draw.rectangle((x1, y1, x2, y2), outline="red", width=2)
            frame.save(os.path.join(draw_path, f"{base_name}.jpg"))
            self.info_label.setText(f"Hallazgo Guardado Correctamente. \nHallazgos guardados: {self.frames_saved}.")
            print(f"BBox guardado: {self.bbox}")



    def pause_frame(self):
        self.info_label.setText(f"Hallazgos guardados: {self.frames_saved}.")
        if self.pause:
            self.pause = False
            self.pause_button.setText("Pausa")
            self.timer.start(1)  # Cambiar el intervalo a 500 ms para ralentizar el avance
        else:
            self.pause = True
            self.pause_button.setText("Reanudar")
            self.timer.stop()  # Detener el temporizador
        
        self.show_frame(self.current_frame_index)
    
    def load_frames(self, frames):
        self.info_label.setText(f"Hallazgos guardados: {self.frames_saved}.")
        """Carga una lista de frames."""
        self.frames = frames
        if self.frames:
            self.show_frame(0)

    def show_frame(self, index):
        self.info_label.setText(f"Hallazgos guardados: {self.frames_saved}.")
        """Muestra el frame en el índice dado."""
        if 0 <= index < len(self.frames):
            self.current_frame_index = index
            frame = self.frames[index]
            self.data_frame = Image.open(frame)
            # Convertir Pillow Image a QImage usando un método alternativo
            q_image = QtGui.QImage(self.data_frame.tobytes(), self.data_frame.width, self.data_frame.height, self.data_frame.width*3, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(q_image)
            
            # Escalar el pixmap para que se ajuste al tamaño de la etiqueta
            self.scaled_pixmap = pixmap.scaled(self.frame_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.frame_label.setPixmap(self.scaled_pixmap)
            
            # Ajustar el tamaño de la ventana al tamaño de la imagen
            self.resize(self.scaled_pixmap.size())

    def show_previous_frame(self):
        self.info_label.setText(f"Hallazgos guardados: {self.frames_saved}.")
        """Muestra el frame anterior."""
        if self.current_frame_index > 0:
            self.show_frame(self.current_frame_index - 1)

    def show_next_frame(self):
        self.info_label.setText(f"Hallazgos guardados: {self.frames_saved}.")
        """Muestra el siguiente frame."""
        if self.current_frame_index < len(self.frames) - 1:
            self.show_frame(self.current_frame_index + 1)

    def next_frame(self):
        self.info_label.setText(f"Hallazgos guardados: {self.frames_saved}.")
        """Avanza al siguiente frame automáticamente."""
        if self.current_frame_index < len(self.frames) - 1:
            self.show_frame(self.current_frame_index + 1)
        else:
            self.timer.stop()  # Detener el temporizador si se llega al final de los frames

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.close_event_handled = False
        self.video_path = None

    def initUI(self):
        self.setWindowTitle("Inspección de Conductores de alta tensión")
        self.setMinimumWidth(700)
        main_layout = QtWidgets.QVBoxLayout()

        # Agregar un QLabel para instrucciones
        instruction_layout = QtWidgets.QHBoxLayout()
        self.instruction_label = QtWidgets.QLabel("Selecciona un video para comenzar con la inspección.", self)
        instruction_layout.addWidget(self.instruction_label)  # Añadir la etiqueta al layout principal
    
        main_layout.addLayout(instruction_layout)
        
        folder_layout = QtWidgets.QHBoxLayout()
        self.file_path_line_edit = QtWidgets.QLineEdit(self)
        self.file_path_line_edit.setReadOnly(True)  # Hacer que el QLineEdit sea de solo lectura
        folder_layout.addWidget(self.file_path_line_edit)

        btn_fldr_layout = QtWidgets.QVBoxLayout()
        self.select_folder_button = QtWidgets.QPushButton("Seleccionar Video", self)
        self.select_folder_button.setFixedSize(120, 25)  # Establecer un tamaño fijo para el botón
        self.select_folder_button.clicked.connect(self.select_folder)
        btn_fldr_layout.addWidget(self.select_folder_button)

        folder_layout.addLayout(btn_fldr_layout)

        main_layout.addLayout(folder_layout)

        

        btn_layout = QtWidgets.QHBoxLayout()
        
        self.pre_proceso_button = QtWidgets.QPushButton("Pre-proceso", self)
        self.pre_proceso_button.setEnabled(False)  # Desactivar inicialmente
        self.pre_proceso_button.clicked.connect(self.capture_frames)  # Conectar a la función correspondiente
        btn_layout.addWidget(self.pre_proceso_button)
        
        self.detect_frames_button = QtWidgets.QPushButton("Detectar Hallazgos", self)
        self.detect_frames_button.setEnabled(False)  # Desactivar inicialmente
        self.detect_frames_button.clicked.connect(self.select_frames)  # Conectar a la función correspondiente
        btn_layout.addWidget(self.detect_frames_button)

        # self.upload_cvat_button = QtWidgets.QPushButton("Subir a CVAT", self)
        # self.upload_cvat_button.setEnabled(False)  # Desactivar inicialmente
        # self.upload_cvat_button.clicked.connect(self.call_cvat)  # Conectar a la función correspondiente
        # btn_layout.addWidget(self.upload_cvat_button)
        
        main_layout.addLayout(btn_layout)
        
        log_layout = QtWidgets.QHBoxLayout()
        self.log_text_edit = QtWidgets.QTextEdit(self)  # Agregar un QTextEdit para la terminal
        self.log_text_edit.setReadOnly(True)  # Hacer que el QTextEdit sea de solo lectura
        self.log_text_edit.setStyleSheet("color: white; background-color: black;")  # Establecer el color del texto a negro
        log_layout.addWidget(self.log_text_edit)  # Añadir el QTextEdit al layout de log
        main_layout.addLayout(log_layout)  # Añadir el layout de log al layout principal

        self.progress_label = QtWidgets.QLabel("", self)
        self.progress_label.hide()
        self.progress_label.setAlignment(QtCore.Qt.AlignCenter)  # Centrar la etiqueta
        main_layout.addWidget(self.progress_label)
        
        self.progress_bar = QtWidgets.QProgressBar(self)  # Crear una barra de progreso
        self.progress_bar.hide()  # Ocultar la barra de progreso inicialmente
        main_layout.addWidget(self.progress_bar)  # Añadir la barra de progreso al layout principal
        
        
        
        info_layout = QtWidgets.QHBoxLayout()
        info_layout.addStretch()  # Agregar un espaciador para empujar el botón a la derecha
        self.btn_vermas = QtWidgets.QPushButton("Más Información", self)
        self.btn_vermas.setFixedSize(120, 25)  # Establecer un tamaño fijo para el botón
        self.btn_vermas.clicked.connect(self.ver_mas)
        info_layout.addWidget(self.btn_vermas)
        main_layout.addLayout(info_layout)
        
        self.setLayout(main_layout)
        self.show()
   
    def select_folder(self):
        # reiniciar el log y los botones
        self.file_path_line_edit.clear()
        self.log_text_edit.clear()

        # Crear una instancia de Tk y ocultarla
        root = Tk()
        root.withdraw()

        options = filedialog.askopenfilename()
        
        # Cerrar la ventana de Tk
        root.destroy()

        if options:
            self.video_path = options
            self.file_path_line_edit.setText(self.video_path)  # Mostrar la ruta en el QLineEdit
            self.log_text_edit.append(f"Video seleccionado: {os.path.basename(self.video_path)}")
            self.pre_proceso_button.setEnabled(True)  # Activar botón de pre-proceso
            self.detect_frames_button.setEnabled(True)  # Activar botón de detectar hallazgos
            # self.upload_cvat_button.setEnabled(True)
            

    def ver_mas(self):
        # Crear una ventana de diálogo para mostrar información
        info_dialog = QtWidgets.QDialog(self)
        info_dialog.setWindowTitle("Información del programa")
        info_dialog.setMinimumWidth(400)

        # Crear un layout vertical para el diálogo
        layout = QtWidgets.QVBoxLayout()
        # Agregar un QLabel con la información
        info_text = (
            "Este programa permite generar los frames con los hallazgos encontrados en los videos de los conductores\n\n"
            "Instrucciones de uso:\n\n"
            "1. Selecciona un video de un conductor.\n"
            "2. Haz clic en 'Pre-proceso' para extraer los frames del video.\n"
            "3. Una vez finalizado el pre-proceso, haz clic en 'Detectar Hallazgos' para iniciar la detección.\n"
            "4. Se abrirá una ventana donde se visualizará el video en frames.\n"
            "5. Usa los siguientes botones para controlar la reproducción del video:\n"
            "       -> 'Anterior' para retroceder al frame anterior.\n"
            "       -> 'Iniciar Video' para reproducir el video automáticamente.\n"
            "       -> 'Pausa/Reanudar' para detener la reproducción en el frame actual.\n"
            "       -> 'Siguiente' para avanzar al siguiente frame.\n"
            "6. Para registrar un hallazgo:\n"
            "       -> Haz clic en la imagen para dibujar un cuadro (bounding box) alrededor del hallazgo.\n"
            "       -> Selecciona el tipo de hallazgo desde el menú desplegable.\n"
            "       -> Haz clic en 'Guardar Hallazgo' para almacenarlo.\n"
            "7. Una vez guardados los hallazgos, puedes continuar la inspección del video o seleccionar otro.\n"    
            "8. Para salir del programa, cierra la ventana de información o usa el botón 'Cerrar'.\n"
            "\n"
        )

        info_label = QtWidgets.QLabel(info_text)
        layout.addWidget(info_label)


        info_dialog.setLayout(layout)
        info_dialog.exec_()  # Mostrar el diálogo

    def capture_frames(self):
        
        print(f"Se capturan frames de {self.video_path}")
        self.log_text_edit.append(f"Comenzando pre-proceso.")
        # Desactivar todos los botones
        self.btn_vermas.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        self.pre_proceso_button.setEnabled(False)
        self.detect_frames_button.setEnabled(False)
        self.get_frames()
        self.detect_frames_button.setEnabled(True)  # Activar botón de detectar hallazgos
        self.pre_proceso_button.setEnabled(True)  # Desactivar botón de pre-proceso
        self.btn_vermas.setEnabled(True)
        self.select_folder_button.setEnabled(True)
        
    def create_zip(self):
        self.log_text_edit.append(f"Creando zip para subir a CVAT...")
        frame_path = self.video_path
        base_name = os.path.basename(frame_path)
      
        dir_path = os.path.dirname(frame_path)
        labels_path = os.path.join(dir_path, "labels")
        frames_path = os.path.join(dir_path, "frames")
        zipPath = os.path.join(dir_path, "zip_cvat")
        os.makedirs(zipPath, exist_ok=True)
        # Directorio de salida para las etiquetas
        output_dir = os.path.join(zipPath, "obj_train_data")
        os.makedirs(output_dir, exist_ok=True)
        
        # Crear archivo obj.names y obj.data
        objData = "classes = 37\ntrain = data/train.txt\nnames = data/obj.names\nbackup = backup/\n"
        objNames = "Aislador-Quebrado\nAislador-Contaminado\nAislador-Corrosión\nAislador-Excremento\nAislador-Daño recubrimiento\nAislador-Desalineado\nAislador-Chaveta desplazada\nAmortiguador-Doblado\nAmortiguador-Roto\nAmortiguador-Corrosión\nBaliza-Abrazadera rota\nBaliza-Corrosión\nBaliza-Pintura\nCable puente-Corrosión\nCable puente-Hebra cortada\nConductor-Corrosión\nConductor-Elemento extraño\nConductor-Hebra cortada\nCruceta-Corrosión en placa de anclaje\nCruceta-Corrosión\nCruceta-Deformación\nEstructura-Contaminación\nEstructura-Corrosión\nEstructura-Torcida\nEstructura-Elemento extraño\nFundación-Problema en fundación\nPeldaños escalada-Corrosión\nAbrazadera de suspensión-Corrosión\nHerrajes de suspensión-Corrosión\nGrillete/eslabón-Corrosión\nTensores/Soportes-Doblados\nHerrajes de tensión-Corrosión\nPernos y tuercas-Corrosión\nCable guardia-Corrosión en anclaje\nDispositivo anti aves-Problemas\nSeñalización-Corrosión\nSeñalización-Inexistente\n"

        with open(os.path.join(zipPath, "obj.data"), "w") as f:
            f.write(objData)
        with open(os.path.join(zipPath, "obj.names"), "w") as f:
            f.write(objNames)

        # Crear archivo train.txt
        with open(os.path.join(zipPath, "train.txt"), "w") as f:
            for img_name in os.listdir(frames_path):
                f.write(f"data/obj_train_data/{img_name}\n")

        # Crear archivo ZIP con la estructura especificada
        zip_filename = os.path.join(zipPath, "deteccionesCond.zip")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            # Agregar archivos a la carpeta obj_train_data/
            for img_name in os.listdir(labels_path):
                img_path = os.path.join(labels_path, img_name)
                zipf.write(img_path, os.path.join("obj_train_data", img_name))

            # Agregar archivos obj.data, obj.names y train.txt
            zipf.write(os.path.join(zipPath, "obj.data"), "obj.data")
            zipf.write(os.path.join(zipPath, "obj.names"), "obj.names")
            zipf.write(os.path.join(zipPath, "train.txt"), "train.txt")
        self.log_text_edit.append(f"Zip creado: {zip_filename}")
        return zip_filename
        
    def call_cvat(self):
        self.log_text_edit.append(f"Subiendo a CVAT...")
        zip_filename = self.create_zip()
        CVAT_HOST = "http://3.225.205.173:8080/"
        CVAT_USERNAME = "adentu"
        CVAT_PASSWORD = "gary2025"

        file_dir = os.path.dirname(self.video_path)
        folder_name = file_dir.split("/")[-1]
        base_name = os.path.basename(self.video_path)
        base_name = base_name.replace(".MP4", "")
        frames_dir = os.path.join(file_dir, "frames")

        image_files = [
            os.path.join(frames_dir, file) for file in os.listdir(frames_dir)
        ]
        print("Creando task y subiendo imagenes y etiquetas a CVAT...")
        with make_client(
            host=CVAT_HOST, credentials=(CVAT_USERNAME, CVAT_PASSWORD)
        ) as client:
            # Crear especificación de la tarea
            self.log_text_edit.append(f"Conexión establecida con CVAT...")
            # Crear la tarea en el servidor
            task_spec = {
                "name": folder_name,
                "project_id": 3,
            }

            task = client.tasks.create_from_data(
                spec=task_spec,
                resource_type=ResourceType.LOCAL,
                resources=image_files,
                annotation_format="YOLO 1.1",
                annotation_path=zip_filename,
            )
            print(f"Tarea {task.id} creada")
        
        
        

    def haversine(self, lat1, lon1, lat2, lon2):
        """ Calcula la distancia entre dos coordenadas geográficas usando la fórmula de Haversine """
        R = 6371.0  # Radio de la Tierra en kilómetros
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c  # Distancia en km


    def get_frames(self):
        cap = imageio.get_reader(self.video_path)  # Usar imageio para leer el video
        path_dir = os.path.dirname(self.video_path)
        base_name = os.path.basename(self.video_path)
        base_name = base_name.replace(".MP4", "")
        path_dir = os.path.join(path_dir, base_name)
        frame_dir = os.path.join(path_dir, "temp")
        os.makedirs(frame_dir, exist_ok=True)

        # Obtener el número total de frames
        num_frames = cap.count_frames()
        
        self.progress_label.setText(f"Capturando frames de {os.path.basename(self.video_path)}")  # Actualizar el texto de la barra de progreso
        self.progress_bar.setRange(0, num_frames)  # Establecer el rango de la barra de progreso
        self.progress_label.show()  # Mostrar la barra de progreso al iniciar el proceso
        self.progress_bar.show()  # Mostrar la barra de progreso al iniciar el proceso

        frame_count = 0
        for frame_index in range(num_frames):
            frame = cap.get_data(frame_index)  # Obtener el frame

            if frame is not None:
                frame_filename = os.path.join(frame_dir, f"{base_name}_{frame_count:04d}.jpg")
                imageio.imwrite(frame_filename, frame)  # Guardar el frame
                frame_count += 1

            self.progress_bar.setValue(frame_index + 1)  # Actualizar la barra de progreso

        cap.close()  # Cerrar el lector de video
        self.log_text_edit.append(f"Captura de frames completada")
        self.progress_label.hide()
        self.progress_bar.hide()
    
    
    
    def select_frames(self):
        # revisar si exite la capeta temp_dir
        file_dir = os.path.dirname(self.video_path)
        base_name = os.path.basename(self.video_path)
        base_name = base_name.replace(".MP4", "")
        file_dir = os.path.join(file_dir, base_name)
        temp_dir = os.path.join(file_dir, "temp")
        if not os.path.exists(temp_dir):
            self.log_text_edit.append(f"Se necesita ejecutar el pre-proceso para detectar hallazgos")
            return
       
        else:

            frames_dir = os.path.join(file_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)
            temp_frames = os.listdir(temp_dir)
            self.log_text_edit.append(f"Comenzando selección de hallazgos")
            
            temp_frames = [os.path.join(temp_dir, frame) for frame in temp_frames]
            self.btn_vermas.setEnabled(False)
            self.select_folder_button.setEnabled(False)
            self.pre_proceso_button.setEnabled(False)
            self.detect_frames_button.setEnabled(False)
            
            self.select_frames_window = SelectFrames()
            self.select_frames_window.load_frames(temp_frames)
            self.select_frames_window.show()

            self.log_text_edit.append(f"Seleccion de hallazgos completado")
            
            self.detect_frames_button.setEnabled(True)  # Activar botón de detectar hallazgos
            self.pre_proceso_button.setEnabled(True)  # Desactivar botón de pre-proceso
            self.btn_vermas.setEnabled(True)
            self.select_folder_button.setEnabled(True)

    
    
    
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Confirmar Cierre',
            '¿Estás seguro de que quieres cerrar el programa? Se perderán todos los avances.',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()  # Aceptar el cierre
        else:
            event.ignore()  # Ignorar el cierre


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    main_window = MainWindow()
    app.exec_()