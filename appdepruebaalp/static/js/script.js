document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let tipoEvento = '';
    let currentStep = 1;
    let cotizacionData = {};
    
    // Inicializar el selector de fecha
    flatpickr(".datepicker", {
        locale: "es",
        dateFormat: "d/m/Y",
        minDate: "today"
    });
    
    // Selección de tipo de evento (Paso 1)
    const eventTypes = document.querySelectorAll('.event-type');
    eventTypes.forEach(type => {
        type.addEventListener('click', function() {
            // Eliminar selección previa
            eventTypes.forEach(t => t.classList.remove('selected'));
            
            // Marcar como seleccionado
            this.classList.add('selected');
            
            // Guardar tipo de evento
            tipoEvento = this.getAttribute('data-type');
            
            // Actualizar etiqueta del nombre según el tipo de evento
            const nombreLabel = document.getElementById('nombre-label');
            if (tipoEvento === 'Boda') {
                nombreLabel.textContent = 'Nombre de los novios:';
            } else {
                nombreLabel.textContent = 'Nombre del festejado:';
            }
            
            // Avanzar al siguiente paso automáticamente
            setTimeout(() => {
                goToStep(2);
            }, 500);
        });
    });
    
    // Navegación entre pasos
    document.getElementById('prev-step2').addEventListener('click', () => goToStep(1));
    document.getElementById('next-step2').addEventListener('click', validateStep2);
    document.getElementById('prev-step3').addEventListener('click', () => goToStep(2));
    
    // Hacer que la barra de navegación sea seleccionable
    document.getElementById('step1').addEventListener('click', () => goToStep(1));
    document.getElementById('step2').addEventListener('click', () => goToStep(2));
    document.getElementById('step3').addEventListener('click', () => goToStep(3));
    
    // Hacer que las etiquetas de paso también sean seleccionables
    document.querySelectorAll('.step-label').forEach((label, index) => {
        label.addEventListener('click', () => goToStep(index + 1));
    });
    
    // Mostrar/ocultar campo de cantidad para chisperos
    const chisperosCheckbox = document.getElementById('chisperos');
    const cantidadContainer = document.querySelector('.cantidad-container');
    
    chisperosCheckbox.addEventListener('change', function() {
        cantidadContainer.style.display = this.checked ? 'flex' : 'none';
    });
    
    // Mostrar/ocultar selector de tipo de precio para DJ
    const djCheckbox = document.getElementById('dj');
    const tipoPrecioDjContainer = document.querySelector('.tipo-precio-dj-container');
    const tipoPrecioDjSelect = document.getElementById('tipo_precio_dj');
    
    djCheckbox.addEventListener('change', function() {
        // Solo mostrar el selector si el tipo de evento es Cumpleaños
        if (tipoEvento === 'Cumpleaños' && this.checked) {
            tipoPrecioDjContainer.style.display = 'flex';
        } else {
            tipoPrecioDjContainer.style.display = 'none';
        }
    });
    
    // Evitar que se cierre el selector al hacer clic en él
    tipoPrecioDjSelect.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    tipoPrecioDjContainer.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // Actualizar visibilidad del selector de DJ cuando cambia el tipo de evento
    eventTypes.forEach(type => {
        type.addEventListener('click', function() {
            // Si DJ está seleccionado y el nuevo tipo es Cumpleaños, mostrar el selector
            if (djCheckbox.checked) {
                const nuevoTipoEvento = this.getAttribute('data-type');
                tipoPrecioDjContainer.style.display = (nuevoTipoEvento === 'Cumpleaños') ? 'flex' : 'none';
            }
        });
    });
    
    // Hacer que las tarjetas de servicios sean seleccionables desde cualquier parte del recuadro
    const serviceItems = document.querySelectorAll('.service-item');
    serviceItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Evitar que se active cuando se hace clic en el contenedor de cantidad
            if (e.target.closest('.cantidad-container')) return;
            
            // Obtener el checkbox dentro de esta tarjeta
            const checkbox = this.querySelector('input[type="checkbox"]');
            
            // Cambiar el estado del checkbox (marcado/desmarcado)
            checkbox.checked = !checkbox.checked;
            
            // Disparar el evento change para activar otros listeners (como el de chisperos)
            const event = new Event('change');
            checkbox.dispatchEvent(event);
        });
    });

    // Generar cotización
    document.getElementById('generar-cotizacion').addEventListener('click', generarCotizacion);
    
    // Agregar elementos adicionales
    document.getElementById('agregar-descuento').addEventListener('click', () => agregarElemento('descuento'));
    document.getElementById('agregar-viatico').addEventListener('click', () => agregarElemento('viatico'));
    document.getElementById('agregar-extra').addEventListener('click', () => agregarElemento('extra'));
    
    // Descargar PDF
    document.getElementById('descargar-pdf').addEventListener('click', generarPDF);
    
    // Crear nueva cotización
    document.getElementById('nueva-cotizacion').addEventListener('click', reiniciarCotizacion);
    
    // Previsualización de imagen de fondo
    const imagenFondoInput = document.getElementById('imagen-fondo');
    const imagenPreview = document.getElementById('imagen-preview');
    
    imagenFondoInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                imagenPreview.style.backgroundImage = `url(${event.target.result})`;
                imagenPreview.textContent = '';
            };
            reader.readAsDataURL(file);
        } else {
            imagenPreview.style.backgroundImage = 'none';
            imagenPreview.textContent = 'Vista previa';
        }
    });

    // Inicializar color pickers
    function goToStep(step) {
        // Ocultar todos los pasos
        document.querySelectorAll('.step-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Mostrar el paso actual
        document.getElementById(`step${step}-content`).classList.add('active');
        
        // Actualizar barra de progreso
        updateProgressBar(step);
        
        // Actualizar paso actual
        currentStep = step;
    }
    
    // Función para actualizar la barra de progreso
    function updateProgressBar(step) {
        // Actualizar el progreso
        const progress = document.getElementById('progress');
        progress.style.width = ((step - 1) / 2 * 100) + '%';
        
        // Actualizar los pasos
        for (let i = 1; i <= 3; i++) {
            const stepElement = document.getElementById(`step${i}`);
            const stepLabel = document.querySelectorAll('.step-label')[i-1];
            
            if (i <= step) {
                stepElement.classList.add('active');
                stepLabel.classList.add('active');
            } else {
                stepElement.classList.remove('active');
                stepLabel.classList.remove('active');
            }
        }
    }
    
    // Función para validar el paso 2
    function validateStep2() {
        const lugar = document.getElementById('lugar').value;
        const nombre = document.getElementById('nombre').value;
        const numInvitados = document.getElementById('num_invitados').value;
        const fecha = document.getElementById('fecha').value;
        const duracion = document.getElementById('duracion').value;
        
        if (!numInvitados || !fecha || !duracion) {
            alert('Por favor, complete todos los campos obligatorios.');
            return;
        }
        
        goToStep(3);
    }
    
    // Función para generar la cotización
    function generarCotizacion() {
        // Recopilar datos del formulario
        const serviciosSeleccionados = [];
        document.querySelectorAll('input[name="servicios"]:checked').forEach(checkbox => {
            serviciosSeleccionados.push(checkbox.value);
        });
        
        if (serviciosSeleccionados.length === 0) {
            alert('Por favor, seleccione al menos un servicio.');
            return;
        }
        
        // Preparar datos para enviar al servidor
        const data = {
            tipo_evento: tipoEvento,
            lugar: document.getElementById('lugar').value,
            nombre: document.getElementById('nombre').value,
            num_invitados: document.getElementById('num_invitados').value,
            fecha: document.getElementById('fecha').value,
            duracion: document.getElementById('duracion').value,
            servicios: serviciosSeleccionados
        };
        
        // Si se seleccionaron chisperos, agregar la cantidad
        if (serviciosSeleccionados.includes('Chisperos')) {
            data.cantidad_chisperos = document.getElementById('cantidad_chisperos').value;
        }
        
        // Si se seleccionó DJ y es un evento de cumpleaños, agregar el tipo de precio
        if (serviciosSeleccionados.includes('DJ') && tipoEvento === 'Cumpleaños') {
            data.tipo_precio_dj = document.getElementById('tipo_precio_dj').value;
        }
        
        // Enviar datos al servidor
        fetch('/generar_cotizacion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            // Guardar datos de la cotización
            cotizacionData = {
                ...data,
                cotizacion: result.cotizacion || [],
                servicios_automaticos: result.servicios_automaticos || [],
                descuentos: [],
                viaticos: [],
                extras: [],
                total: result.total || 0
            };
            // Validar que la clave 'cotizacion' esté presente y no vacía
            if (!cotizacionData.cotizacion || cotizacionData.cotizacion.length === 0) {
                alert('Error: No se pudo generar la cotización. Por favor, revise los datos e intente nuevamente.');
                return;
            }
            
            // Mostrar el total
            document.getElementById('total-cotizacion').textContent = `$${result.total.toLocaleString('es-MX')}`;
            
            // Mostrar el resultado
            document.getElementById('resultado-cotizacion').style.display = 'block';
            
            // Mostrar servicios automáticos si existen
            if (result.servicios_automaticos && result.servicios_automaticos.length > 0) {
                console.log('Servicios automáticos incluidos:', result.servicios_automaticos);
            }
            
            // Scroll hacia el resultado
            document.getElementById('resultado-cotizacion').scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ocurrió un error al generar la cotización. Por favor, intente nuevamente.');
        });
    }
    
    // Función para agregar elementos adicionales (descuentos, viáticos, extras)
    function agregarElemento(tipo) {
        const template = document.getElementById(`${tipo}-template`);
        const container = document.getElementById(`${tipo}s-list`);
        
        const clone = document.importNode(template.content, true);
        const eliminarBtn = clone.querySelector('.eliminar-item');
        
        eliminarBtn.addEventListener('click', function() {
            this.closest(`.${tipo}-item`).remove();
            actualizarTotal();
        });
        
        // Agregar eventos para actualizar el total cuando se cambien los valores
        const montoInput = clone.querySelector(`.${tipo}-monto`);
        montoInput.addEventListener('input', actualizarTotal);
        
        container.appendChild(clone);
    }
    
    // Función para actualizar el total con los elementos adicionales
    function actualizarTotal() {
        // Recopilar descuentos
        const descuentos = [];
        document.querySelectorAll('.descuento-item').forEach(item => {
            const descripcion = item.querySelector('.descuento-descripcion').value;
            const monto = parseFloat(item.querySelector('.descuento-monto').value) || 0;
            
            if (descripcion && monto > 0) {
                descuentos.push({ descripcion, monto });
            }
        });
        
        // Recopilar viáticos
        const viaticos = [];
        document.querySelectorAll('.viatico-item').forEach(item => {
            const descripcion = item.querySelector('.viatico-descripcion').value;
            const monto = parseFloat(item.querySelector('.viatico-monto').value) || 0;
            
            if (descripcion && monto > 0) {
                viaticos.push({ descripcion, monto });
            }
        });
        
        // Recopilar extras
        const extras = [];
        document.querySelectorAll('.extra-servicio-item').forEach(item => {
            const descripcion = item.querySelector('.extra-descripcion').value;
            const monto = parseFloat(item.querySelector('.extra-monto').value) || 0;
            
            if (descripcion && monto > 0) {
                extras.push({ descripcion, monto });
            }
        });
        
        // Actualizar datos de la cotización
        cotizacionData.descuentos = descuentos;
        cotizacionData.viaticos = viaticos;
        cotizacionData.extras = extras;
        
        // Calcular nuevo total
        let nuevoTotal = cotizacionData.total;
        
        // Restar descuentos
        descuentos.forEach(descuento => {
            nuevoTotal -= descuento.monto;
        });
        
        // Sumar viáticos
        viaticos.forEach(viatico => {
            nuevoTotal += viatico.monto;
        });
        
        // Sumar extras
        extras.forEach(extra => {
            nuevoTotal += extra.monto;
        });
        
        // Actualizar el total mostrado
        document.getElementById('total-cotizacion').textContent = `$${nuevoTotal.toLocaleString('es-MX')}`;
    }
    
    // Función para generar el PDF
    function generarPDF() {
        // --- Inicio: Añadir comprobación para cotizacionData ---
        if (!cotizacionData || !cotizacionData.cotizacion) {
            alert('Por favor, genere una cotización primero o espere a que se complete.');
            // Restaurar el botón si es necesario (opcional, depende de la lógica exacta)
            const generarBtn = document.getElementById('descargar-pdf');
            if (generarBtn.disabled) {
                generarBtn.textContent = 'Descargar PDF Personalizado'; // O el texto original
                generarBtn.disabled = false;
            }
            return; // Detener la ejecución si no hay datos
        }
        // --- Fin: Añadir comprobación ---

        // Mostrar indicador de carga
        const generarBtn = document.getElementById('descargar-pdf');
        const textoOriginal = generarBtn.textContent;
        generarBtn.textContent = 'Generando PDF...';
        generarBtn.disabled = true;
        
        // Recopilar datos de personalización (solo los necesarios para la portada y estilos)
        recopilarDatosPersonalizacion().then(personalizacion => {
            // Preparar datos para el PDF
            // Incluir datos principales de cotizacionData y la personalización
            const pdfData = {
                ...cotizacionData, // Incluye nombre, fecha, lugar, num_personas, etc.
                personalizacion: personalizacion // Incluye colores, textos, portada(tipo_evento, titulo_tipo_evento)
            };
            
            // Enviar datos directamente
            enviarDatosParaPDF(pdfData, generarBtn, textoOriginal);
        }).catch(error => {
            alert('Error al recopilar datos de personalización: ' + error.message);
            generarBtn.textContent = textoOriginal;
            generarBtn.disabled = false;
        });
    }
    
    // Función para recopilar todos los datos de personalización
async function recopilarDatosPersonalizacion() {
    const personalizacion = {};
    
    // Helper function to safely get element value
    const getElementValue = (id, defaultValue = '') => {
        const element = document.getElementById(id);
        return element ? element.value : defaultValue;
    };

    // Helper function to safely get checkbox state
    const getCheckboxState = (id, defaultState = false) => {
        const element = document.getElementById(id);
        return element ? element.checked : defaultState;
    };

    // Recopilar datos de colores
    personalizacion.colores = {
        principal: getElementValue('color-principal', '#1a237e'), // Default blue
        secundario: getElementValue('color-secundario', '#3949ab'), // Default medium blue
        acento: getElementValue('color-acento', '#ff9800'), // Default orange
        texto: getElementValue('color-texto', '#212121'), // Default dark grey
        fondo: '#f5f5f5' // Valor fijo para el fondo
    };

    // Recopilar datos de texto
    const tituloPers = getElementValue('titulo-personalizado');
    personalizacion.titulo = tituloPers ? tituloPers : 'COTIZACIÓN'; // Usar predeterminado si está vacío
    personalizacion.texto_adicional = getElementValue('texto-adicional');

    // Recopilar datos de la portada (solo tipo de evento y título personalizado)
    personalizacion.portada = {
        tipo_evento: getElementValue('portada-tipo-evento'),
        titulo_tipo_evento: getElementValue('titulo-tipo-evento')
        // Ya no se recopilan lugar, nombres, fecha, num_personas aquí
    };

    // Recopilar datos de términos y condiciones
    personalizacion.terminos = {
        texto: getElementValue('terminos-texto'),
        mostrar_firma: getCheckboxState('terminos-firma')
    };

    return personalizacion;
}

// Función para enviar los datos al servidor para generar el PDF
function enviarDatosParaPDF(pdfData, generarBtn, textoOriginal) {
    fetch('/descargar_plantilla', { // <-- Corregir URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(pdfData)
    })
    .then(response => {
        if (!response.ok) {
            if (response.headers.get('content-type')?.includes('application/json')) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error al generar el PDF');
                });
            }
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        return response.blob();
    })
    .then(blob => {
        // Crear un enlace para descargar el archivo
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Generar nombre de archivo usando datos de cotizacionData
        const nombreArchivo = `Cotizacion_${pdfData.nombre || 'Evento'}_${pdfData.fecha ? pdfData.fecha.replace(/\//g, '-') : 'SinFecha'}.pdf`;
        a.download = nombreArchivo;
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        // Restaurar el botón
        generarBtn.textContent = textoOriginal;
        generarBtn.disabled = false;
    })
    .catch(error => {
        alert('Error al generar el PDF: ' + error.message);
        generarBtn.textContent = textoOriginal;
        generarBtn.disabled = false;
    });
}

// Función para reiniciar la cotización
function reiniciarCotizacion() {
    // Limpiar formulario
    const form = document.getElementById('cotizacion-form');
    if (form) form.reset();
    
    // Restablecer variables globales
    tipoEvento = '';
    currentStep = 1;
    cotizacionData = {};
    
    // Restablecer estado visual
    document.querySelectorAll('.event-type').forEach(t => t.classList.remove('selected'));
    document.getElementById('resultado-cotizacion').style.display = 'none';
    document.getElementById('total-cotizacion').textContent = '$0';
    document.getElementById('descuentos-list').innerHTML = '';
    document.getElementById('viaticos-list').innerHTML = '';
    document.getElementById('extras-list').innerHTML = '';
    
    // Desmarcar todos los servicios
    document.querySelectorAll('input[name="servicios"]').forEach(cb => { cb.checked = false; });
    
    // Restablecer campos de cantidad y selectores
    const cantidadContainer = document.querySelector('.cantidad-container');
    if (cantidadContainer) cantidadContainer.style.display = 'none';
    const tipoPrecioDjContainer = document.querySelector('.tipo-precio-dj-container');
    if (tipoPrecioDjContainer) tipoPrecioDjContainer.style.display = 'none';
    
    // Restablecer previsualización de imagen
    const imagenPreview = document.getElementById('imagen-preview');
    if (imagenPreview) {
        imagenPreview.style.backgroundImage = 'none';
        imagenPreview.textContent = 'Vista previa de la imagen';
    }
    const imagenFondoInput = document.getElementById('imagen-fondo');
    if (imagenFondoInput) imagenFondoInput.value = '';
    
    // Restablecer colores y textos personalizados si existen
    const colorPrincipal = document.getElementById('color-principal');
    if (colorPrincipal) colorPrincipal.value = '#1a237e';
    const colorSecundario = document.getElementById('color-secundario');
    if (colorSecundario) colorSecundario.value = '#3949ab';
    const colorAcento = document.getElementById('color-acento');
    if (colorAcento) colorAcento.value = '#ff9800';
    const colorTexto = document.getElementById('color-texto');
    if (colorTexto) colorTexto.value = '#212121';
    const tituloPersonalizado = document.getElementById('titulo-personalizado');
    if (tituloPersonalizado) tituloPersonalizado.value = '';
    
    // Volver al primer paso
    goToStep(1);
}

// Inicializar la aplicación
goToStep(1);

});