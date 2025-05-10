from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import base64
# Imports para fuentes personalizadas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

# Registrar fuentes Montserrat (asumiendo que los archivos .ttf están en la carpeta 'fonts')
try:
    montserrat_regular_path = os.path.join('fonts', 'Montserrat-Regular.ttf')
    montserrat_bold_path = os.path.join('fonts', 'Montserrat-Bold.ttf')
    pdfmetrics.registerFont(TTFont('Montserrat', montserrat_regular_path))
    pdfmetrics.registerFont(TTFont('Montserrat-Bold', montserrat_bold_path))
except Exception as e:
    print(f"Error al registrar fuentes Montserrat: {e}")
    print("Asegúrate de que los archivos Montserrat-Regular.ttf y Montserrat-Bold.ttf estén en la carpeta 'fonts'.")
    # Usar fuentes predeterminadas como fallback
    FONT_REGULAR = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
else:
    FONT_REGULAR = 'Montserrat'
    FONT_BOLD = 'Montserrat-Bold'

# Configuración de precios y reglas
PRECIOS = {
    'DJ': {
        'Boda': 12000,
        'Bautizo': 12000,
        'Quince años': 12000,
        'Cumpleaños': 1000  # por hora
    },
    'Sonido': {
        'Boda': {
            '150': 8000,
            '151+': 16000
        },
        'Otros': {
            '70': 4000,
            '150': 8000,
            '250': 12000,
            '350': 16000
        }
    },
    'Iluminación': {
        'Boda': {
           # '150': 4500,
            #'151+': 18000,
            '70': 4500, #6 par + 2 cabezas
            '150': 6500, #6 par + 4 cabezas
            '250': 12500, #12 par + 6 cabezas, si se pueden colgar se cuelgan
            '350': 19500 #22 par + 10 cabezas, si se pueden colgar se cuelgan
        },
        'Otros': {
            '70': 2500, #6 par o 2 cabezas
            '150': 4500, #6 par + 2 cabezas
            '250': 12500, #12 par + 6 cabezas, si se pueden colgar se cuelgan
            '350': 19500  #22 par + 10 cabezas, si se pueden colgar se cuelgan
        }
    },
    'Pista de baile': {
        '70': 6600,
        '150': 8800,
        '250': 11000,
        '350': 13200
    },
    'Planta de luz': 9000,
    'Chisperos': 350,  # precio por unidad
    'Lluvia de papeles': 3000,
    'Barra de bebidas': 8000,
    'Back pintado a mano': 4500
}

# Horas base por tipo de evento
HORAS_BASE = {
    'Cumpleaños': {
        '70': 6,
        '71+': 7
    },
    'Bautizo': {
        '70': 7,
        '71+': 8
    },
    'Quince años': {
        '70': 7,
        '71+': 8
    },
    'Boda': {
        '150': 8,
        '151+': 'ilimitado'
    }
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar_cotizacion', methods=['POST'])
def generar_cotizacion():
    data = request.json
    
    tipo_evento = data['tipo_evento']
    num_invitados = int(data['num_invitados'])
    horas = int(data['duracion'])
    servicios = data['servicios']
    
    # Calcular horas base según el tipo de evento y número de invitados
    if tipo_evento == 'Cumpleaños':
        horas_base = HORAS_BASE['Cumpleaños']['70'] if num_invitados <= 70 else HORAS_BASE['Cumpleaños']['71+']
    elif tipo_evento == 'Bautizo' or tipo_evento == 'Quince años':
        horas_base = HORAS_BASE[tipo_evento]['70'] if num_invitados <= 70 else HORAS_BASE[tipo_evento]['71+']
    else:  # Boda
        horas_base = HORAS_BASE['Boda']['150'] if num_invitados <= 150 else HORAS_BASE['Boda']['151+']
    
    # Inicializar cotización
    cotizacion = []
    total = 0
    
    # Calcular precios de servicios seleccionados
    for servicio in servicios:
        precio = 0
        if servicio == 'DJ':
            if tipo_evento in ['Boda', 'Bautizo', 'Quince años']:
                precio = PRECIOS['DJ'][tipo_evento]
            else:  # Cumpleaños
                # Verificar el tipo de precio seleccionado por el usuario
                tipo_precio_dj = data.get('tipo_precio_dj', 'por_hora')  # Por defecto, usar precio por hora
                
                if tipo_precio_dj == 'por_hora':
                    # Si seleccionó precio por hora: $1000 por hora con mínimo 6 horas
                    if horas < 6:
                        precio = 6000  # Mínimo 6 horas (6 * 1000)
                    else:
                        precio = PRECIOS['DJ']['Cumpleaños'] * horas
                else:  # precio fijo
                    # Si seleccionó precio fijo: $12000
                    precio = 12000
                    
                    # Establecer horas base según número de invitados
                    dj_horas_base = 6 if num_invitados <= 70 else 7
                    
                    # Calcular horas extras si aplica
                    if horas > dj_horas_base:
                        horas_extras = horas - dj_horas_base
                        # Usar la tarifa por hora de cumpleaños para las horas extras del DJ fijo
                        precio_hora_extra_dj = PRECIOS['DJ']['Cumpleaños'] 
                        precio += precio_hora_extra_dj * horas_extras
        
        elif servicio == 'Sonido':
            if tipo_evento == 'Boda':
                if num_invitados <= 150:
                    precio = PRECIOS['Sonido']['Boda']['150']
                else:
                    precio = PRECIOS['Sonido']['Boda']['151+']
            else:  # Otros eventos
                if num_invitados <= 70:
                    precio = PRECIOS['Sonido']['Otros']['70']
                elif num_invitados <= 150:
                    precio = PRECIOS['Sonido']['Otros']['150']
                elif num_invitados <= 250:
                    precio = PRECIOS['Sonido']['Otros']['250']
                elif num_invitados <= 350:
                    precio = PRECIOS['Sonido']['Otros']['350']
                else:
                    precio = "Contactar para calcular precio"
                    continue  # Skip adding to total
            
            # Calcular horas extras si aplica
            if horas_base != 'ilimitado' and horas > horas_base:
                horas_extras = horas - horas_base
                # El precio base del servicio ya está en 'precio'
                # Calculamos el costo por hora extra basado en el precio base del servicio y las horas base
                costo_por_hora_extra_servicio = precio / horas_base
                adicional_por_horas_extras = costo_por_hora_extra_servicio * horas_extras
                precio += round(adicional_por_horas_extras) # Redondear el costo adicional de las horas extras
        
        elif servicio == 'Iluminación':
            if tipo_evento == 'Boda':
                if num_invitados <= 70:
                    precio = PRECIOS['Iluminación']['Boda']['70']
                elif num_invitados <= 150:
                    precio = PRECIOS['Iluminación']['Boda']['150']
                elif num_invitados <= 250:
                    precio = PRECIOS['Iluminación']['Boda']['250']
                elif num_invitados <= 350:
                    precio = PRECIOS['Iluminación']['Boda']['350']
                else:
                    precio = "Contactar para calcular precio"
                    continue  # Skip adding to total
            else:  # Otros eventos
                if num_invitados <= 70:
                    precio = PRECIOS['Iluminación']['Otros']['70']
                elif num_invitados <= 150:
                    precio = PRECIOS['Iluminación']['Otros']['150']
                elif num_invitados <= 250:
                    precio = PRECIOS['Iluminación']['Otros']['250']
                elif num_invitados <= 350:
                    precio = PRECIOS['Iluminación']['Otros']['350']
                else:
                    precio = "Contactar para calcular precio"
                    continue  # Skip adding to total
            
            # Calcular horas extras si aplica
            if horas_base != 'ilimitado' and horas > horas_base:
                horas_extras = horas - horas_base
                # El precio base del servicio ya está en 'precio'
                # Calculamos el costo por hora extra basado en el precio base del servicio y las horas base
                costo_por_hora_extra_servicio = precio / horas_base
                adicional_por_horas_extras = costo_por_hora_extra_servicio * horas_extras
                precio += round(adicional_por_horas_extras) # Redondear el costo adicional de las horas extras
        
        elif servicio == 'Pista de baile':
            if num_invitados <= 70:
                precio = PRECIOS['Pista de baile']['70']
            elif num_invitados <= 150:
                precio = PRECIOS['Pista de baile']['150']
            elif num_invitados <= 250:
                precio = PRECIOS['Pista de baile']['250']
            elif num_invitados <= 350:
                precio = PRECIOS['Pista de baile']['350']
            else:
                precio = "Contactar para calcular precio"
                continue  # Skip adding to total
            
            # Calcular horas extras si aplica
            if horas_base != 'ilimitado' and horas > horas_base:
                horas_extras = horas - horas_base
                # El precio base del servicio ya está en 'precio'
                # Calculamos el costo por hora extra basado en el precio base del servicio y las horas base
                costo_por_hora_extra_servicio = precio / horas_base
                adicional_por_horas_extras = costo_por_hora_extra_servicio * horas_extras
                precio += round(adicional_por_horas_extras) # Redondear el costo adicional de las horas extras
        
        # Calcular precio planta de luz
        elif servicio == 'Planta de luz':
            if horas_base != 'ilimitado' and (horas_base + 1) > 9:
                precio = (horas_base + 1) * 1000
            else:
                precio = PRECIOS['Planta de luz']
        
        elif servicio == 'Chisperos':
            cantidad = int(data.get('cantidad_chisperos', 1))
            precio = PRECIOS['Chisperos'] * cantidad
        
        elif servicio == 'Lluvia de papeles':
            precio = PRECIOS['Lluvia de papeles']
        
        cotizacion.append({
            'servicio': servicio,
            'precio': precio
        })
        
        if isinstance(precio, (int, float)):
            total += precio
    
    # Servicios incluidos automáticamente
    servicios_automaticos = []
    
    # Para Bodas, incluir Barra de bebidas
    if tipo_evento == 'Boda':
        servicios_automaticos.append({
            'servicio': 'Barra de bebidas',
            'precio': PRECIOS['Barra de bebidas'],
            'incluido': True
        })
        total += PRECIOS['Barra de bebidas']
        
        # Si se seleccionó Sonido y DJ, incluir Cabina de DJ sin costo
        if 'Sonido' in servicios and 'DJ' in servicios:
            servicios_automaticos.append({
                'servicio': 'Cabina de DJ',
                'precio': 0,
                'incluido': True
            })
    
    # Para Bodas y Bautizos con más de 150 invitados, incluir Back pintado a mano
    if (tipo_evento == 'Boda'):
        servicios_automaticos.append({
            'servicio': 'Back pintado a mano',
            'precio': PRECIOS['Back pintado a mano'],
            'incluido': True
        })
        total += PRECIOS['Back pintado a mano']
        
    if (tipo_evento == 'Bautizo') and num_invitados >= 100:
        servicios_automaticos.append({
            'servicio': 'Back pintado a mano',
            'precio': PRECIOS['Back pintado a mano'],
            'incluido': True
        })
        total += PRECIOS['Back pintado a mano']
    
    # Agregar descuentos y viáticos si se proporcionaron
    descuentos = data.get('descuentos', [])
    viaticos = data.get('viaticos', [])
    extras = data.get('extras', [])
    
    for descuento in descuentos:
        total -= descuento['monto']
    
    for viatico in viaticos:
        total += viatico['monto']
    
    for extra in extras:
        total += extra['monto']
    
    resultado = {
        'cotizacion': cotizacion,
        'servicios_automaticos': servicios_automaticos,
        'descuentos': descuentos,
        'viaticos': viaticos,
        'extras': extras,
        'total': total
    }
    
    return jsonify(resultado)

# --- Eliminar la ruta y función innecesaria de plantilla original ---
@app.route('/descargar_plantilla', methods=['POST'])
def descargar_plantilla():
    try:
        data = request.json
        num_invitados = int(data.get('num_invitados', 0))  # Extraer num_invitados de los datos recibidos
        # --- Inicio: Debugging --- 
        print("----- Datos recibidos en /descargar_plantilla -----") 
        import json 
        print(json.dumps(data, indent=2))
        print("--------------------------------------------------")
        # Verificar si la clave 'cotizacion' existe
        if 'cotizacion' not in data:
             print("ERROR: La clave 'cotizacion' no se encontró en los datos recibididos.")
             # Devolver un error claro al frontend
             return jsonify({"error": "Datos de cotización incompletos: falta la clave 'cotizacion'"}), 400
        # --- Fin: Debugging ---
        
        personalizacion = data.get('personalizacion', {})
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF con la plantilla original
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        elements = []
        
        # Colores predeterminados
        color_principal = colors.HexColor('#1a237e')  # Azul oscuro
        color_secundario = colors.HexColor('#3949ab')  # Azul medio
        color_acento = colors.HexColor('#ff9800')  # Naranja
        color_fondo = colors.HexColor('#f5f5f5')  # Gris muy claro
        color_texto = colors.HexColor('#212121')  # Casi negro
        
        # --- PORTADA DE INTRODUCCIÓN ---
        portada_personalizacion = personalizacion.get('portada', {})
        # Obtener datos de la cotización principal
        portada_lugar = data.get('lugar', '')
        portada_nombres = data.get('nombre', '') # Usar 'nombre' de cotizacionData
        portada_fecha = data.get('fecha', '')
        portada_num_personas = data.get('num_personas', '')
        # Obtener datos de personalización de la portada
        portada_tipo_evento = portada_personalizacion.get('tipo_evento', '')
        portada_titulo_tipo_evento = portada_personalizacion.get('titulo_tipo_evento', '')
        
        # Página de portada: usaremos la imagen tono y carla.jpg como fondo
        from reportlab.platypus import Frame
        from reportlab.lib.utils import ImageReader
        import os
        def portada_canvas(canvas, doc):
            # Imagen de fondo
            img_path = os.path.join('static', 'img', 'tono y carla.jpg')
            abs_img_path = os.path.abspath(img_path)
            page_width, page_height = letter
            try:
                img_reader = ImageReader(abs_img_path)
                canvas.saveState()
                # Dibujar imagen de fondo
                canvas.drawImage(img_reader, 0, 0, width=page_width, height=page_height, mask='auto')
                # Dibujar capa semitransparente negra encima
                canvas.setFillColor(colors.Color(0, 0, 0, alpha=0.5))
                canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
                canvas.restoreState()
            except Exception as e:
                print(f"Error al dibujar fondo de portada: {e}")
        
        portada_elements = []
        # Espaciado superior
        portada_elements.append(Spacer(1, 1.5*inch))
        # Título principal (tipo de evento personalizado)
        portada_titulo_style = ParagraphStyle(
            'PortadaTituloStyle',
            parent=styles['Heading1'],
            alignment=1,
            fontName=FONT_BOLD,
            fontSize=32,
            textColor=colors.white,
            leading=36,
            spaceAfter=20
            # backColor=colors.Color(0, 0, 0, alpha=0.5) # Eliminado nuevamente
        )
        titulo_portada = portada_titulo_tipo_evento if portada_titulo_tipo_evento else (portada_tipo_evento or 'Evento')
        portada_elements.append(Paragraph(titulo_portada, portada_titulo_style))
        portada_elements.append(Spacer(1, 0.2*inch))
        # Nombres de festejados
        if portada_nombres:
            portada_elements.append(Paragraph(f"<b>Festejado(s):</b> {portada_nombres}", ParagraphStyle('PortadaNombres', parent=styles['Normal'], alignment=1, fontSize=18, textColor=colors.white, leading=22))) # backColor eliminado
            portada_elements.append(Spacer(1, 0.1*inch))
        # Lugar
        if portada_lugar:
            portada_elements.append(Paragraph(f"<b>Lugar:</b> {portada_lugar}", ParagraphStyle('PortadaLugar', parent=styles['Normal'], alignment=1, fontSize=16, textColor=colors.white, leading=20))) # backColor eliminado
            portada_elements.append(Spacer(1, 0.1*inch))
        # Fecha
        if portada_fecha:
            portada_elements.append(Paragraph(f"<b>Fecha:</b> {portada_fecha}", ParagraphStyle('PortadaFecha', parent=styles['Normal'], alignment=1, fontSize=16, textColor=colors.white, leading=20))) # backColor eliminado
            portada_elements.append(Spacer(1, 0.1*inch))
        # Número de personas
        if portada_num_personas:
            # Asegurarse de que num_personas sea una cadena para la concatenación
            num_personas_str = str(portada_num_personas) if portada_num_personas is not None else ''
            portada_elements.append(Paragraph(f"<b>Número de personas:</b> {num_personas_str}", ParagraphStyle('PortadaNumPersonas', parent=styles['Normal'], alignment=1, fontSize=16, textColor=colors.white, leading=20))) # backColor eliminado
            portada_elements.append(Spacer(1, 0.1*inch))
        # Tipo de evento (de la personalización)
        if portada_tipo_evento:
            portada_elements.append(Paragraph(f"<b>Tipo de evento:</b> {portada_tipo_evento}", ParagraphStyle('PortadaTipoEvento', parent=styles['Normal'], alignment=1, fontSize=16, textColor=colors.white, leading=20))) # backColor eliminado
            portada_elements.append(Spacer(1, 0.1*inch))
        # Espaciado inferior
        portada_elements.append(Spacer(1, 2*inch))
        # Pie de página
        portada_elements.append(Paragraph("Cotización personalizada", ParagraphStyle('PortadaPie', parent=styles['Normal'], alignment=1, fontSize=12, textColor=colors.white, leading=16))) # backColor eliminado
        
        # Crear un documento temporal solo para la portada
        portada_buffer = BytesIO()
        portada_doc = SimpleDocTemplate(portada_buffer, pagesize=letter, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
        portada_doc.build(portada_elements, onFirstPage=portada_canvas)
        portada_buffer.seek(0)
        # Leer la portada como PDF y agregarla como primera página
        from PyPDF2 import PdfReader, PdfWriter
        portada_pdf = PdfReader(portada_buffer)
        # Ahora generamos el resto del PDF como antes
        
        # Título principal con estilo predeterminado
        titulo_style = ParagraphStyle(
            'TituloStyle',
            parent=styles['Heading1'],
            alignment=1,  # Centrado
            spaceAfter=20,
            fontName=FONT_BOLD,
            fontSize=24,
            textColor=colors.white, # Descripciones en blanco según solicitud
            # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
            leading=30
        )
        # Obtener título personalizado o usar el predeterminado
        titulo_personalizado = personalizacion.get('titulo', 'COTIZACIÓN')
        elements.append(Paragraph(titulo_personalizado, titulo_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Agregar texto adicional si existe
        texto_adicional = personalizacion.get('texto_adicional')
        if texto_adicional:
            texto_adicional_style = ParagraphStyle(
                'TextoAdicionalStyle',
                parent=styles['Normal'],
                alignment=1,  # Centrado
                fontName=FONT_REGULAR,
                fontSize=12,
                textColor=colors.white, # Mantenido blanco
                # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
                leading=14,
                spaceBefore=5,
                spaceAfter=15
            )
            elements.append(Paragraph(texto_adicional, texto_adicional_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Estilos para los elementos del PDF
        servicio_style = ParagraphStyle(
            'ServicioStyle',
            parent=styles['Normal'],
            alignment=0,  # Izquierda
            fontName=FONT_BOLD,
            fontSize=14,
            textColor=colors.HexColor('#FFD700'), # Color dorado para títulos de servicio
            # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
            leading=16,
            spaceBefore=10,
            spaceAfter=2
        )
        
        descripcion_style = ParagraphStyle(
            'DescripcionStyle',
            parent=styles['Normal'],
            alignment=0,  # Izquierda
            fontName=FONT_REGULAR,
            fontSize=10,
            textColor=colors.white, # Color de descripción establecido a blanco según solicitud
            # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
            leading=12,
            leftIndent=30  # Aumentar sangría para viñetas
        )
        
        precio_style = ParagraphStyle(
            'PrecioStyle',
            parent=styles['Normal'],
            alignment=2,  # Derecha
            fontName=FONT_BOLD,
            fontSize=14,
            textColor=colors.white, # Descripciones en blanco según solicitud
            # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
            leading=16
        )

        item_precio_style_for_extras = ParagraphStyle(
            'ItemPrecioStyleForExtras',
            parent=styles['Normal'],
            alignment=2,  # Derecha
            fontName=FONT_REGULAR,
            fontSize=10,
            textColor=colors.white,
            leading=12
        )
        
        # Crear filas para cada servicio (sin iconos)
        tabla_servicios = []
        for servicio in data['cotizacion']:
            nombre_servicio = servicio['servicio']
            precio = servicio['precio']
            descripcion = ""
            if nombre_servicio == 'Sonido':
                # num_invitados ya está definido y es un entero desde el inicio de la función generar_cotizacion
                if num_invitados <= 70:
                    descripcion = "2 bocinas HK 115 FA"
                elif num_invitados <= 150: # Asumido 150 para la segunda condición del usuario
                    descripcion = "• Bocinas HK 115 FA<br/>• 2 Bajos Audio Center 18"
                elif num_invitados <= 250:
                    descripcion = "• 2 Bocinas HK 115 FA<br/>• 2 Bajos dobles Warfade 218"
                else:
                    # Fallback para más de 250 personas
                    descripcion = "AUDIO PROFESIONAL<br/>• TÉCNICO DE AUDIO" # Descripción original como fallback
            elif nombre_servicio == 'DJ':
                descripcion = f"DJ PROFESIONAL<br/>• REPERTORIO PERSONALIZADO<br/>• CITA DE LOGÍSTICA MUSICAL PREVIA AL EVENTO"
            elif nombre_servicio == 'Iluminación':
                # Obtener el número de invitados de la solicitud principal
                num_invitados_val = 0
                try:
                    # 'data' es el JSON de nivel superior recibido por /descargar_plantilla
                    # Asegurarse de que 'num_invitados' esté presente y no sea una cadena vacía antes de convertir
                    num_invitados_str = str(data.get('num_invitados', '0')).strip() # Default to '0' string if not found
                    if num_invitados_str: # Si no está vacío después de strip
                        num_invitados_val = int(num_invitados_str)
                except (ValueError, TypeError):
                    # Si la conversión falla o el tipo es incorrecto, num_invitados_val permanece 0.
                    pass # num_invitados_val sigue siendo 0

                if num_invitados_val > 0 and num_invitados_val <= 70:
                    descripcion = "A elegir:<br/>• 2 cabezas robóticas 7r o 6 ParLed"
                elif num_invitados_val <= 150: # Implica > 70
                    descripcion = "• 2 cabezas robóticas 7r<br/>• 6 ParLed"
                elif num_invitados_val <= 250: # Implica > 150
                    descripcion = "• 6 cabezas robóticas 7r<br/>• 12 ParLed"
                elif num_invitados_val <= 350: # Implica > 250
                    descripcion = "• 10 cabezas robóticas 7r<br/>• 20 ParLed"
                elif num_invitados_val > 350:
                    descripcion = "Equipamiento de iluminación para más de 350 personas (contactar para cotización)"
                else: # num_invitados_val es 0 o negativo (inválido porque no entró en >0)
                    descripcion = "ILUMINACIÓN PARA LA PISTA<br/>• ILUMINACIÓN ROBÓTICA BEAM/SPOT (Cantidad de invitados no especificada o inválida)"
            elif nombre_servicio == 'Pista de baile':
                # Determinar el tamaño de la pista según el número de invitados
                num_invitados_val = int(data.get('num_invitados', 0))
                descripcion_base = ""
                if num_invitados_val <= 70:
                    descripcion_base = "•Pista de baile proporcional a 70 personas"
                elif num_invitados_val <= 150:
                    descripcion_base = "•Pista de baile proporcional a 150 personas"
                elif num_invitados_val <= 250:
                    descripcion_base = "•Pista de baile proporcional a 250 personas"
                elif num_invitados_val <= 350:
                    descripcion_base = "•Pista de baile proporcional a 350 personas"
                else:
                    descripcion_base = "Pista de baile (tamaño a cotizar)"
                descripcion = f"{descripcion_base}<br/>• Pintada a mano con diseño (dos colores)"
            if isinstance(precio, (int, float)):
                precio_str = f"$ {precio:,.2f}"
            elif isinstance(precio, str):
                precio_str = precio
            else:
                precio_str = "Consultar"
            # Fila: servicio (con descripción si existe) y precio
            texto_servicio = nombre_servicio
            if descripcion:
                texto_servicio += f"<br/><span fontSize=10>{descripcion}</span>"
            tabla_servicios.append([
                Paragraph(texto_servicio, servicio_style),
                Paragraph(precio_str, precio_style)
            ])
        # Agregar servicios automáticos si existen
        if 'servicios_automaticos' in data and data['servicios_automaticos']:
            for servicio in data['servicios_automaticos']:
                nombre_servicio = servicio['servicio']
                precio = servicio['precio']
                incluido = servicio.get('incluido', False)
                descripcion = ""
                if nombre_servicio == 'Barra de bebidas':
                    descripcion = "•Pintada a mano con diseño (dos colores)"
                elif nombre_servicio == 'Cabina de DJ':
                    descripcion = "•Pintada a mano con diseño (dos colores)"
                elif nombre_servicio == 'Back pintado a mano':
                    descripcion = "•Pintada a mano con diseño (dos colores)"
                if isinstance(precio, (int, float)):
                    precio_str = f"$ {precio:,.2f}"
                elif isinstance(precio, str):
                    precio_str = precio
                else:
                    precio_str = "Incluido"
                nombre_con_etiqueta = f"{nombre_servicio} {'(Incluido)' if incluido else ''}"
                texto_servicio = nombre_con_etiqueta
                if descripcion:
                    texto_servicio += f"<br/><span fontSize=10>{descripcion}</span>"
                tabla_servicios.append([
                    Paragraph(texto_servicio, servicio_style),
                    Paragraph(precio_str, precio_style)
                ])
        # Agregar descuentos si existen
        descuentos_data = data.get('descuentos', [])
        if descuentos_data:
            tabla_servicios.append([
                Paragraph("Descuentos", servicio_style),
                Paragraph("", servicio_style)  # Celda vacía para la segunda columna del título
            ])
            for descuento in descuentos_data:
                desc = descuento.get('descripcion', '')
                try:
                    monto = float(descuento['monto'])
                    precio_str = f"- $ {monto:,.2f}"
                except (ValueError, TypeError):
                    precio_str = f"- $ {descuento['monto']}"
                tabla_servicios.append([
                    Paragraph(desc, descripcion_style),  # Usar descripcion_style para el ítem
                    Paragraph(precio_str, item_precio_style_for_extras) # Usar nuevo estilo para el precio del ítem
                ])
        # Agregar viáticos desglosados si existen
        viaticos_data = data.get('viaticos', [])
        if viaticos_data:
            tabla_servicios.append([
                Paragraph("Viáticos", servicio_style),
                Paragraph("", servicio_style)
            ])
            for viatico in viaticos_data:
                desc = viatico.get('descripcion', '')
                try:
                    monto = float(viatico['monto'])
                    precio_str = f"$ {monto:,.2f}"
                except (ValueError, TypeError):
                    precio_str = f"$ {viatico['monto']}"
                tabla_servicios.append([
                    Paragraph(desc, descripcion_style),
                    Paragraph(precio_str, item_precio_style_for_extras)
                ])
        # Agregar extras si existen
        extras_data = data.get('extras', [])
        if extras_data:
            tabla_servicios.append([
                Paragraph("Extras", servicio_style),
                Paragraph("", servicio_style)
            ])
            for extra in extras_data:
                desc = extra.get('descripcion', 'Adicional')
                try:
                    monto = float(extra['monto'])
                    precio_str = f"$ {monto:,.2f}"
                except (ValueError, TypeError):
                    precio_str = f"$ {extra['monto']}"
                tabla_servicios.append([
                    Paragraph(desc, descripcion_style),
                    Paragraph(precio_str, item_precio_style_for_extras)
                ])
        # Insertar tabla de servicios y precios
        from reportlab.platypus import Table, TableStyle
        tabla = Table(tabla_servicios, colWidths=[340, 100])
        tabla.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
            ('FONTNAME', (0,0), (-1,-1), FONT_REGULAR),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(tabla)
        elements.append(Spacer(1, 0.2*inch))

        # Eliminar duplicación: NO volver a agregar servicios automáticos, descuentos, viáticos ni extras aquí
        # Ya están incluidos en la tabla_servicios

        # Calcular el total igual que en la previsualización
        total = 0
        # Sumar servicios
        for servicio in data.get('cotizacion', []):
            try:
                total += float(servicio['precio'])
            except (ValueError, TypeError, KeyError):
                pass
        # Sumar servicios automáticos
        for servicio in data.get('servicios_automaticos', []):
            try:
                total += float(servicio['precio'])
            except (ValueError, TypeError, KeyError):
                pass
        # Restar descuentos
        for descuento in data.get('descuentos', []):
            try:
                total -= float(descuento['monto'])
            except (ValueError, TypeError, KeyError):
                pass
        # Sumar viáticos
        for viatico in data.get('viaticos', []):
            try:
                total += float(viatico['monto'])
            except (ValueError, TypeError, KeyError):
                pass
        # Sumar extras
        for extra in data.get('extras', []):
            try:
                total += float(extra['monto'])
            except (ValueError, TypeError, KeyError):
                pass

        # Agregar línea separadora antes del total
        elements.append(Spacer(1, 0.5*inch))

        # Agregar el total con un estilo destacado
        total_style = ParagraphStyle(
            'TotalStyle',
            parent=styles['Heading1'],
            alignment=1,  # Centrado
            fontName=FONT_BOLD,
            fontSize=24,  # Aumentado de 20 a 24
            textColor=colors.white, # Descripciones en blanco según solicitud
            # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
            leading=28, # Ajustado el leading
            spaceBefore=10,
            spaceAfter=10
        )
        total_formateado = f"<u>TOTAL:   $ {total:,.2f}</u>" # Añadido subrayado
        elements.append(Paragraph(total_formateado, total_style))
        
        # Verificar si se deben incluir términos y condiciones
        incluir_terminos = personalizacion.get('incluir_terminos', True)
        
        if incluir_terminos:
            # Agregar página de términos y condiciones
            elements.append(PageBreak())
            
            # Título de términos y condiciones
            terminos_titulo_style = ParagraphStyle(
                'TerminosTituloStyle',
                parent=styles['Heading1'],
                alignment=1,  # Centrado
                spaceAfter=15,
                fontName=FONT_BOLD,
                fontSize=18,
                textColor=colors.white, # Mantenido blanco
                # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
                leading=22
            )
            
            # Título personalizado para términos y condiciones
            terminos_titulo = personalizacion.get('terminos_titulo', "TÉRMINOS Y CONDICIONES")
            elements.append(Paragraph(terminos_titulo, terminos_titulo_style))
            
            # Contenido de términos y condiciones
            terminos_style = ParagraphStyle(
                'TerminosStyle',
                parent=styles['Normal'],
                alignment=0,  # Izquierda
                fontName=FONT_REGULAR,
                fontSize=10,
                textColor=colors.white, # Mantenido blanco
                # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            
            # Texto de términos y condiciones
            terminos_texto = [
                "1. <b>Validez de la cotización:</b> Esta cotización tiene una validez de 15 días a partir de la fecha de emisión.",
                "2. <b>Reserva del servicio:</b> Para confirmar la reserva del servicio se requiere un anticipo del 50% del valor total.",
                "3. <b>Cancelaciones:</b> En caso de cancelación, el anticipo no será reembolsable si se realiza con menos de 30 días de anticipación al evento.",
                "4. <b>Cambios de fecha:</b> Los cambios de fecha están sujetos a disponibilidad y deberán solicitarse con al menos 15 días de anticipación.",
                "5. <b>Horas adicionales:</b> Las horas adicionales no contempladas en esta cotización tendrán un costo extra según las tarifas vigentes.",
                "6. <b>Condiciones del lugar:</b> El cliente debe garantizar las condiciones adecuadas para la instalación y operación de los equipos (acceso, espacio, energía eléctrica, etc.).",
                "7. <b>Daños al equipo:</b> Cualquier daño causado a los equipos por mal uso, negligencia o causas ajenas al proveedor será responsabilidad del cliente.",
                "8. <b>Fuerza mayor:</b> En caso de situaciones de fuerza mayor que impidan la realización del servicio, se acordará una nueva fecha sin costo adicional.",
                "9. <b>Pago final:</b> El pago del saldo restante deberá realizarse 7 días antes del evento.",
                "10. <b>Servicios adicionales:</b> Cualquier servicio adicional no incluido en esta cotización deberá ser acordado previamente y tendrá un costo extra."
            ]
            
            for parrafo in terminos_texto:
                elements.append(Paragraph(parrafo, terminos_style))
            
            # Nota final personalizada o predeterminada
            nota_final = personalizacion.get('nota_final', "Al aceptar esta cotización, el cliente acepta todos los términos y condiciones aquí establecidos.")
            
            nota_style = ParagraphStyle(
                'NotaStyle',
                parent=styles['Normal'],
                alignment=1,  # Centrado
                fontName=FONT_REGULAR,
                fontSize=9,
                textColor=colors.white, # Mantenido blanco
                # backColor=colors.Color(0, 0, 0, alpha=0.5), # Eliminado nuevamente
                leading=12,
                spaceBefore=20
            )
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(nota_final, nota_style))
        
        # Construir el PDF, aplicando la función de fondo/logo a cada página
        # --- NUEVA LÓGICA DE FONDOS POR SECCIÓN ---
        def cotizacion_canvas(canvas, doc):
            img_path = os.path.join('static', 'img', 'fondo 2 cabina.jpg')
            abs_img_path = os.path.abspath(img_path)
            page_width, page_height = letter
            try:
                img_reader = ImageReader(abs_img_path)
                canvas.saveState()
                # Dibujar imagen de fondo
                canvas.drawImage(img_reader, 0, 0, width=page_width, height=page_height, mask='auto')
                # Dibujar capa semitransparente negra encima
                canvas.setFillColor(colors.Color(0, 0, 0, alpha=0.5))
                canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
                canvas.restoreState()
            except Exception as e:
                print(f"Error al dibujar fondo de cotización: {e}")
        def terminos_canvas(canvas, doc):
            img_path = os.path.join('static', 'img', 'terminod y condiciones fondo.png')
            abs_img_path = os.path.abspath(img_path)
            page_width, page_height = letter
            try:
                img_reader = ImageReader(abs_img_path)
                canvas.saveState()
                # Obtener tamaño real de la imagen
                img_width, img_height = img_reader.getSize()
                # Calcular escala para cubrir toda la página (cover)
                scale = max(page_width / img_width, page_height / img_height)
                draw_width = img_width * scale
                draw_height = img_height * scale
                # Centrar la imagen
                x = (page_width - draw_width) / 2
                y = (page_height - draw_height) / 2
                canvas.drawImage(img_reader, x, y, width=draw_width, height=draw_height, mask='auto')
                # Dibujar capa semitransparente negra encima
                canvas.setFillColor(colors.Color(0, 0, 0, alpha=0.5))
                canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)
                canvas.restoreState()
            except Exception as e:
                print(f"Error al dibujar fondo de términos: {e}")
        # --- FIN NUEVA LÓGICA ---
        # Construcción de PDF por secciones
        # 1. Portada
        portada_buffer = BytesIO()
        portada_doc = SimpleDocTemplate(portada_buffer, pagesize=letter, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
        portada_doc.build(portada_elements, onFirstPage=portada_canvas)
        portada_buffer.seek(0)
        from PyPDF2 import PdfReader, PdfWriter
        portada_pdf = PdfReader(portada_buffer)
        # 2. Cotización y total
        cotizacion_buffer = BytesIO()
        cotizacion_doc = SimpleDocTemplate(cotizacion_buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        # Extraer solo los elementos de cotización (sin portada ni términos)
        cotizacion_elements = []
        for el in elements:
            if not (isinstance(el, Paragraph) and ("TÉRMINOS Y CONDICIONES" in el.getPlainText() or "TerminosTituloStyle" in str(el.style))):
                cotizacion_elements.append(el)
            else:
                break
        cotizacion_doc.build(cotizacion_elements, onFirstPage=cotizacion_canvas, onLaterPages=cotizacion_canvas)
        cotizacion_buffer.seek(0)
        cotizacion_pdf = PdfReader(cotizacion_buffer)
        # 3. Términos y condiciones (si existen)
        terminos_pdf = None
        if incluir_terminos:
            terminos_buffer = BytesIO()
            terminos_doc = SimpleDocTemplate(terminos_buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
            # Extraer solo los elementos de términos
            terminos_start = False
            terminos_elements = []
            for el in elements:
                if isinstance(el, Paragraph) and ("TÉRMINOS Y CONDICIONES" in el.getPlainText() or "TerminosTituloStyle" in str(el.style)):
                    terminos_start = True
                if terminos_start:
                    terminos_elements.append(el)
            if terminos_elements:
                terminos_doc.build(terminos_elements, onFirstPage=terminos_canvas, onLaterPages=terminos_canvas)
                terminos_buffer.seek(0)
                terminos_pdf = PdfReader(terminos_buffer)
        # Unir todas las secciones en un solo PDF
        writer = PdfWriter()
        # Portada
        for page in portada_pdf.pages:
            writer.add_page(page)
        # Cotización
        for page in cotizacion_pdf.pages:
            writer.add_page(page)
        # Términos
        if terminos_pdf:
            for page in terminos_pdf.pages:
                writer.add_page(page)
        # Guardar el PDF final en el buffer principal
        buffer.seek(0)
        buffer.truncate(0)
        writer.write(buffer)
        buffer.seek(0)

        # Asegurar que el buffer tenga contenido antes de enviarlo
        if buffer.getbuffer().nbytes > 0:
            # Obtener nombre y tipo de evento con manejo de errores
            # Usar datos de la cotización principal para el nombre del archivo
            tipo_evento_archivo = data.get('tipo_evento', 'Evento') # Podría ser el personalizado o el original
            nombre_archivo = data.get('nombre', 'Cliente')
            fecha_archivo = data.get('fecha', 'SinFecha').replace('/', '-')
            
            response = send_file(
                buffer,
                as_attachment=True,
                download_name=f"Cotizacion_{tipo_evento_archivo}_{nombre_archivo}_{fecha_archivo}.pdf",
                mimetype='application/pdf'
            )
            
            # Agregar encabezados para evitar problemas de caché
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
            return response
        else:
            return jsonify({"error": "No se pudo generar el PDF"}), 500
    except Exception as e:
        print(f"Error al generar el PDF: {e}")
        return jsonify({"error": f"Error al generar el PDF: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
            