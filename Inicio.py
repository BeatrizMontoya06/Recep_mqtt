import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Configuración inicial de la página
st.set_page_config(
    page_title="SkyPulse | Centro de Monitoreo Atmosférico",
    page_icon="🌤️",
    layout="wide"
)

# Estilos CSS avanzados para un diseño moderno tipo dashboard meteorológico
st.markdown("""
    <style>
    .main {
        background-color: #0b0f19;
    }
    .stMetric {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .weather-header {
        background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 100%);
        padding: 25px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.2);
    }
    .news-ticker {
        background-color: #1e293b;
        color: #38bdf8;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 500;
        margin-bottom: 20px;
        border-left: 4px solid #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Función optimizada para escuchar el broker MQTT"""
    message_received = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            raw_payload = message.payload.decode()
            payload = json.loads(raw_payload)
            message_received["payload"] = payload
            message_received["received"] = True
        except Exception:
            message_received["payload"] = message.payload.decode()
            message_received["received"] = True
    
    try:
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    except Exception as e:
        return {"error": str(e)}

# --- BARRA LATERAL (CONFIGURACIÓN TÉCNICA) ---
with st.sidebar:
    st.markdown("### 🎛️ Panel de Control IoT")
    st.markdown("Ajusta los parámetros de conexión de red para enlazar con tu hardware virtual o físico.")
    
    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com')
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535)
    topic = st.text_input('Tópico', value='Sensor/THP2')
    client_id = st.text_input('ID del Cliente Web', value='skypulse_client_live_01')
    
    st.divider()
    st.markdown("### 📡 Estado del Nodo")
    st.success("Canal MQTT Activo y Sintonizado")

# --- CABECERA ESTILO NOTICIERO DEL CLIMA ---
st.markdown("""
    <div class="weather-header">
        <h1>🌤️ SkyPulse: Centro Meteorológico Global</h1>
        <p style="font-size: 1.1rem; margin-bottom: 0;">Transmisión en vivo de telemetría ambiental impulsada por ESP32 y sensores IoT.</p>
    </div>
""", unsafe_allow_html=True)

# Ticker de noticias / estado rápido
st.markdown("""
    <div class="news-ticker">
        🔴 <b>BOLETÍN EN VIVO:</b> Monitoreo atmosférico automatizado en proceso. Haga clic en el botón de sincronización para actualizar los registros de campo.
    </div>
""", unsafe_allow_html=True)

# Layout principal en columnas (Sección de control e información descriptiva)
col_info, col_action = st.columns([2, 1], gap="large")

with col_info:
    st.subheader("📰 Resumen de Condiciones del Día")
    st.write(
        "Bienvenido al portal de telemetría de **SkyPulse**. Esta estación procesa variables "
        "meteorológicas críticas en tiempo real mediante microcontroladores IoT. Utilice los paneles "
        "inferiores para auditar la temperatura ambiente y la humedad relativa capturadas directamente "
        "desde el dispositivo simulado."
    )

with col_action:
    st.subheader("⚡ Sincronización")
    st.markdown("Actualice el flujo de datos instantáneo:")
    sync_btn = st.button('🔄 Suncionar Datos en Vivo', use_container_width=True)

if sync_btn:
    with st.spinner('📡 Conectando con el broker y extrayendo paquetes atmosféricos...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

st.divider()

# --- SECCIÓN DE RESULTADOS VISUALES ---
st.subheader("📊 Panel de Métricas Atmosféricas")

if st.session_state.sensor_data is not None:
    data = st.session_state.sensor_data
    
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Error crítico de enlace MQTT: {data['error']}")
    else:
        st.success('✅ Paquete de datos recibido y decodificado exitosamente desde la estación.')
        
        if isinstance(data, dict):
            # Extraer claves tolerando variaciones (Temp / Temperatura, Hum / Humedad)
            temp = data.get('Temp', data.get('Temperatura', 'N/D'))
            hum = data.get('Hum', data.get('Humedad', 'N/D'))
            
            # Desplegar métricas en un formato visual limpio tipo estación meteorológica
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric(label="🌡️ Temperatura Actual", value=f"{temp} °C" if temp != 'N/D' else 'N/D', delta="Estable")
            with metric_col2:
                st.metric(label="💧 Humedad Relativa", value=f"{hum} %" if hum != 'N/D' else 'N/D', delta="Normal")
            with metric_col3:
                st.metric(label="🛰️ Estado del Enlace", value="Conectado", delta="OK")
            
            with st.expander('🔍 Inspeccionar Trama JSON Cruda'):
                st.json(data)
        else:
            st.warning("⚠️ Se recibió una cadena de texto plano en lugar de un objeto estructurado:")
            st.code(data)
else:
    st.info("ℹ️ El panel se encuentra en espera. Haga clic en el botón de sincronización superior para capturar la transmisión actual.")

# Pie de página informativo
st.divider()
st.markdown(
    "<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "SkyPulse Weather Network • Powered by Streamlit & MQTT Protocol"
    "</p>", 
    unsafe_allow_html=True
)
