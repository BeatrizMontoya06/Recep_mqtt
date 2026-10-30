import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Configuración de la página con temática de estación meteorológica
st.set_page_config(
    page_title="Estación Meteorológica IoT",
    page_icon="🌡️",
    layout="wide"
)

# Estilos CSS personalizados para darle un toque moderno/cyber-retro limpio
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Función robusta para escuchar el broker MQTT"""
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
        # Forzar protocolo MQTT v3.1.1 para máxima compatibilidad en la nube
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        # Ventana de escucha de 5 segundos
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    
    except Exception as e:
        return {"error": str(e)}

# Sidebar - Configuración de Red
with st.sidebar:
    st.subheader('⚙️ Configuración del Broker')
    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com')
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535)
    topic = st.text_input('Tópico', value='Sensor/THP2')
    client_id = st.text_input('ID del Cliente Web', value='streamlit_weather_client_99')
    
    st.divider()
    st.markdown("### 🛠️ Estado del Sistema")
    st.info("Asegúrate de que Wokwi esté ejecutándose (Play) y publicando en el tópico exacto.")

# Interfaz Principal de la Estación Meteorológica
st.title('🌡️ Estación Meteorológica en Vivo (Wokwi IoT)')
st.markdown("Monitoreo en tiempo real de temperatura y humedad ambiental mediante ESP32 y MQTT.")

st.divider()

# Botón principal de actualización
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    obtener_datos = st.button('🔄 Sincronizar Datos con Wokwi', use_container_width=True)

if obtener_datos:
    with st.spinner('Conectando al broker y escuchando al sensor...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# Panel de Visualización de Resultados
if st.session_state.sensor_data is not None:
    data = st.session_state.sensor_data
    
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Error de conexión MQTT: {data['error']}")
    else:
        st.success('✅ ¡Conexión exitosa con Wokwi!')
        
        # Contenedor especial para el clima
        st.subheader('📊 Lecturas Actuales del Sensor DHT22')
        
        # Si Wokwi envía Temp y Hum, los mapeamos visualmente de forma limpia
        if isinstance(data, dict):
            # Extraer valores tolerando variaciones de nombres (Temp/Temperatura, Hum/Humedad)
            temp = data.get('Temp', data.get('Temperatura', 'N/D'))
            hum = data.get('Hum', data.get('Humedad', 'N/D'))
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric(label="🌡️ Temperatura", value=f"{temp} °C" if temp != 'N/D' else 'N/D')
            with c2:
                st.metric(label="💧 Humedad Relativa", value=f"{hum} %" if hum != 'N/D' else 'N/D')
                
            with st.expander('🔍 Ver trama JSON completa recibida'):
                st.json(data)
        else:
            st.warning("⚠️ Se recibió información pero no tiene formato JSON válido:")
            st.code(data)
else:
    st.info("ℹ️ Haz clic en **'Sincronizar Datos con Wokwi'** para capturar el paquete más reciente del sensor.")
