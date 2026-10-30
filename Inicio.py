import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="SkyFlow | Weather Intelligence",
    page_icon="⛅",
    layout="wide"
)

# Estilos CSS avanzados para una interfaz totalmente nueva y limpia
st.markdown("""
    <style>
    .main {
        background-color: #090d16;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        padding: 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.3);
    }
    .control-card {
        background-color: #111827;
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #1f2937;
    }
    .metric-container {
        background-color: #111827;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #1f2937;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = "Nunca"

def fetch_mqtt_telemetry(broker, port, topic, client_id):
    """Función de captura MQTT optimizada"""
    msg_container = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            raw = message.payload.decode()
            msg_container["payload"] = json.loads(raw)
            msg_container["received"] = True
        except:
            msg_container["payload"] = message.payload.decode()
            msg_container["received"] = True
            
    try:
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        timeout = time.time() + 5
        while not msg_container["received"] and time.time() < timeout:
            time.sleep(0.1)
            
        client.loop_stop()
        client.disconnect()
        return msg_container["payload"]
    except Exception as e:
        return {"error": str(e)}

# --- HERO BANNER PRINCIPAL ---
st.markdown("""
    <div class="hero-banner">
        <h1 style="margin: 0; font-size: 2.2rem;">⛅ SkyFlow Weather Hub</h1>
        <p style="margin: 5px 0 0 0; font-size: 1.1rem; opacity: 0.9;">Plataforma de visualización atmosférica en tiempo real conectada a microcontroladores IoT.</p>
    </div>
""", unsafe_allow_html=True)

# --- DISTRIBUCIÓN COMPLETAMENTE NUEVA (DOS COLUMNAS PRINCIPALES) ---
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.markdown("### 🎛️ Centro de Operaciones")
    with st.container():
        st.markdown('<div class="control-card">', unsafe_allow_html=True)
        st.write("Configura el enlace con tu dispositivo IoT:")
        
        broker_input = st.text_input('Broker MQTT', value='broker.mqttdashboard.com')
        port_input = st.number_input('Puerto', value=1883, min_value=1, max_value=65535)
        topic_input = st.text_input('Tópico de Lectura', value='Sensor/THP2')
        id_input = st.text_input('ID de Cliente Web', value='skyflow_web_client_09')
        
        st.markdown("<hr style='border-color: #374151;'>", unsafe_allow_html=True)
        
        if st.button('📡 Capturar Telemetría Ahora', use_container_width=True):
            with st.spinner('Escuchando al broker...'):
                res = fetch_mqtt_telemetry(broker_input, int(port_input), topic_input, id_input)
                st.session_state.sensor_data = res
                st.session_state.last_sync = time.strftime("%H:%M:%S")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"🕒 Última sincronización: **{st.session_state.last_sync}**")

with col_right:
    st.markdown("### 📊 Panel de Control Atmosférico en Vivo")
    
    data = st.session_state.sensor_data
    
    if data is None:
        st.warning("⚠️ Sin datos recientes. Haz clic en **'Capturar Telemetría Ahora'** manteniendo tu simulación de Wokwi activa.")
    elif isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Error al conectar con el broker: {data['error']}")
    else:
        st.success("✅ ¡Datos del sensor recibidos correctamente!")
        
        if isinstance(data, dict):
            temp_val = data.get('Temp', data.get('Temperatura', '--'))
            hum_val = data.get('Hum', data.get('Humedad', '--'))
            
            # Sub-columnas para las tarjetas métricas
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f"""
                    <div class="metric-container">
                        <h4 style="color: #38bdf8; margin-bottom: 5px;">🌡️ TEMPERATURA</h4>
                        <h2 style="margin: 0; font-size: 2.5rem;">{temp_val} °C</h2>
                        <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 5px;">Sensor DHT22 (Wokwi)</p>
                    </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                    <div class="metric-container">
                        <h4 style="color: #38bdf8; margin-bottom: 5px;">💧 HUMEDAD</h4>
                        <h2 style="margin: 0; font-size: 2.5rem;">{hum_val} %</h2>
                        <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 5px;">Sensor DHT22 (Wokwi)</p>
                    </div>
                """, unsafe_allow_html=True)
                
            with st.expander("🔍 Inspeccionar Estructura JSON del Paquete"):
                st.json(data)
        else:
            st.code(data)

# Pie de página moderno
st.divider()
st.markdown("<p style='text-align: center; color: #6b7280; font-size: 0.8rem;'>SkyFlow Weather Intelligence System • Arquitectura IoT Cloud</p>", unsafe_allow_html=True)
