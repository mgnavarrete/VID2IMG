# VID2IMG

## Descripción

El programa VID2IMG es una herramienta de inspección de conductores de alta tensión que permite extraer frames de un video, detectar hallazgos en esos frames y subir los resultados a CVAT para su posterior análisis. Utiliza PyQt5 para la interfaz gráfica y varias bibliotecas para el procesamiento de imágenes y videos. Esta herramienta es especialmente útil para la detección y análisis de defectos en infraestructuras eléctricas, facilitando la identificación de problemas como corrosión, deformaciones, y otros daños.

## Requisitos

- Python 3.x

## Instalación

1. Clona este repositorio en tu máquina local.
2. Navega al directorio del proyecto.
3. Instala las dependencias necesarias ejecutando:

   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta el script `main.py` para iniciar la aplicación:

   ```bash
   python main.py
   ```

2. Selecciona un video de un conductor para comenzar la inspección.
3. Haz clic en "Pre-proceso" para extraer los frames del video.
4. Una vez finalizado el pre-proceso, haz clic en "Detectar Hallazgos" para iniciar la detección.
5. Usa los controles de la interfaz para navegar por los frames y registrar hallazgos.
6. Guarda los hallazgos y, si es necesario, súbelos a CVAT para un análisis más detallado.

## Funcionalidades

- **Selección de Video**: Permite seleccionar un video para procesar.
- **Pre-proceso**: Extrae frames del video seleccionado.
- **Detección de Hallazgos**: Permite marcar y guardar hallazgos en los frames.
- **Subida a CVAT**: Crea un archivo ZIP con los resultados y lo sube a CVAT para su análisis.

## Nota Importante

La integración con CVAT está actualmente en proceso de desarrollo y no está completamente lista. Algunas funcionalidades pueden no estar disponibles o no funcionar como se espera. Agradecemos tu comprensión y paciencia mientras trabajamos para mejorar esta característica.

## Detalles Técnicos

- **Interfaz Gráfica**: Utiliza PyQt5 para crear una interfaz de usuario interactiva.
- **Procesamiento de Imágenes**: Usa Pillow para manipular imágenes y dibujar bounding boxes.
- **Manejo de Videos**: Utiliza imageio para leer y procesar videos.
- **Integración con CVAT**: Usa cvat_sdk para subir los resultados a CVAT.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para discutir cualquier cambio que desees realizar.
