import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Lector de Sensor MQTT",
    page_icon="📡",
    layout="centered"
)

# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Función para obtener un mensaje MQTT de forma segura"""
    message_received = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except:
            message_received["payload"] = message.payload.decode()
            message_received["received"] = True
    
    try:
        # Configuración compatible con paho-mqtt v2.x y v1.x
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        # Esperar máximo 5 segundos a recibir un paquete
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    
    except Exception as e:
        return {"error": str(e)}

# Sidebar - Configuración
with st.sidebar:
    st.subheader('⚙️ Configuración de Conexión')
    broker = st.text_input('Broker MQTT', value='broker.mqttdashboard.com', help='Dirección del broker MQTT')
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535, help='Puerto del broker (1883)')
    topic = st.text_input('Tópico', value='Sensor/THP2', help='Tópico MQTT a suscribirse')
    client_id = st.text_input('ID del Cliente Streamlit', value='streamlit_client_cloud_99', help='Identificador único')

st.title('📡 Lector de Sensor MQTT (Wokwi Cloud Bridge)')

st.divider()

# Botón para obtener datos
if st.button('🔄 Obtener Datos del Sensor', use_container_width=True):
    with st.spinner('Conectando al broker público y escuchando a Wokwi...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# Mostrar resultados
if st.session_state.sensor_data:
    st.divider()
    st.subheader('📊 Datos Recibidos')
    
    data = st.session_state.sensor_data
    
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ Error de conexión: {data['error']}")
    elif data is None:
        st.warning("⚠️ No se recibió ningún mensaje en el tiempo límite. Asegúrate de que Wokwi esté ejecutándose y publicando en el mismo tópico.")
    else:
        st.success('✅ ¡Datos sincronizados desde Wokwi correctamente!')
        
        if isinstance(data, dict):
            cols = st.columns(len(data))
            for i, (key, value) in enumerate(data.items()):
                with cols[i]:
                    st.metric(label=key, value=value)
            
            with st.expander('Ver JSON completo'):
                st.json(data)
        else:
            st.code(data)
