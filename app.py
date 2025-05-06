import streamlit as st

st.set_page_config(page_title="Juego Emprendimiento y Contabilidad", layout="wide")

# --- Petición de nombres de los 4 jugadores ---
if 'player_names' not in st.session_state:
    st.title("🎲 Juego de Emprendimiento y Contabilidad")
    st.subheader("👥 Ingrese los nombres de los 4 jugadores:")
    with st.form("nombre_jugadores_form"):
        names = [st.text_input(f"Nombre del Jugador {i+1}:", key=f"name_{i}") for i in range(4)]
        submitted = st.form_submit_button("Iniciar juego")
        if submitted:
            if all(name.strip() for name in names):
                st.session_state.player_names = names
                #st.experimental_rerun()
            else:
                st.error("Por favor, ingrese todos los nombres.")
    st.stop()
#Funciones aux

# --- Clases Empresa y Jugador ---
class Empresa:
    def __init__(self, margen_ganancias, costo_produccion, gasto_operacional, ingresos_netos):
        self.margen_ganancias = margen_ganancias
        self.costo_produccion = costo_produccion
        self.gasto_operacional = gasto_operacional
        self.ingresos_netos = ingresos_netos
    def actualizar_ingresos(self, cantidad):
        self.ingresos_netos += cantidad

class Jugador:
    def __init__(self, nombre):
        self.nombre = nombre
        self.empresa = Empresa(0.30, 5000, 2000, 100000)
        self.posicion = 0
        self.turnos_perdidos = 0
        self.seguro = 0
        self.avance_extra = 0
        self.ingresos_dobles_rondas = 0
        self.ventas_extra_pct = 0
        self.ventas_extra_duration = 0
        self.last_roll = 0
    def estado(self):
        tramo = (
            "IVA 5%" if 1 <= self.posicion <= 16 else
            "IVA 10%" if 17 <= self.posicion <= 32 else
            "IVA 15%" if 33 <= self.posicion <= 48 else
            "IVA 30%"
        )
        return {
            "Posición": self.posicion,
            "Tramo": tramo,
            "Ingresos Netos": self.empresa.ingresos_netos,
            "Costo Producción": self.empresa.costo_produccion,
            "Gasto Operacional": self.empresa.gasto_operacional
        }
    

def preguntar_si_no(pregunta):
    respuesta = st.radio(pregunta, ['Sí', 'No'])
    return respuesta == 'Sí'


def pedir_valor_dado(jugador):
    valor = st.number_input(f"{jugador.nombre}, ¿qué número sacaste en tu dado real? (1-6):", min_value=1, max_value=6, step=1)
    return valor

# --- Inicializar jugadores y turno ---
if 'jugadores' not in st.session_state:
    st.session_state.jugadores = [Jugador(n) for n in st.session_state.player_names]
    st.session_state.turno = 1

# --- Definición del Tablero ---
esquinas = {0: "💥 Inicio", 16: "💰 IVA 5%", 32: "💎 IVA 10%", 48: "🚀 IVA 15%"}
casillas_oportunidad = {1,4,7,10,13,17,20,23,26,29,33,36,39,42,45,49,52,55,58,61}
casillas_amenaza = {3,6,9,12,15,19,22,25,28,31,35,38,41,44,47,51,54,57,60,63}
tablero = {}
for i in range(65):
    if i in esquinas:
        tablero[i] = esquinas[i]
    elif i in casillas_oportunidad:
        tablero[i] = "🎁 Oportunidad"
    elif i in casillas_amenaza:
        tablero[i] = "⚠️ Amenaza"
    elif 1 <= i <= 16:
        tablero[i] = "⬜ Blanca (IVA 5%)"
    elif 17 <= i <= 32:
        tablero[i] = "⬜ Blanca (IVA 10%)"
    elif 33 <= i <= 48:
        tablero[i] = "⬜ Blanca (IVA 15%)"
    else:
        tablero[i] = "⬜ Blanca (IVA 30%)"

# --- Auxiliar para ingreso de dado físico ---
def input_dado(label, key):
    return st.number_input(label, min_value=1, max_value=6, step=1, key=key)

# --- Lógica de movimiento ---
def avanzar(jugador, pasos):
    needed = 64 - jugador.posicion
    avance = min(pasos, needed)
    jugador.posicion += avance
    jugador.last_roll = pasos
    ingreso_base = 10000 * avance
    # IVA según casilla
    if 1 <= jugador.posicion <= 16:
        tasa = 0.95
    elif 17 <= jugador.posicion <= 32:
        tasa = 0.90
    elif 33 <= jugador.posicion <= 48:
        tasa = 0.85
    else:
        tasa = 0.70
    ingreso = int(ingreso_base * tasa)
    if jugador.ventas_extra_pct > 0 and jugador.ventas_extra_duration > 0:
        extra = int(ingreso * jugador.ventas_extra_pct)
        ingreso += extra
        st.write(f"📈 Bonificación ventas: +${extra}")
    if jugador.ingresos_dobles_rondas > 0:
        ingreso *= 2
        st.write("💸 Ingresos duplicados esta ronda!")
    jugador.empresa.actualizar_ingresos(ingreso)
    return avance, ingreso

# --- Eventos de Oportunidad ---
def oportunidad(jugador, casilla):
    st.write(f"🎁 {jugador.nombre} ha caído en Oportunidad {casilla}")
    if casilla == 1:
        st.markdown("### 📢 Oportunidad: Desarrollo de nuevo producto/servicio")
        st.markdown("**Tu equipo de innovación lanza un producto revolucionario.**")
        st.markdown("**Beneficio:** Avanzas automáticamente a la casilla 2.")

        avanzar(jugador, 1)  # Ya existe esta función en tu app
        st.success("¡Avanzas a la casilla 2 gracias a tu innovación!")

    elif casilla == 4:
        st.markdown("### 🚚 Oportunidad: Tercerización en la Distribución")
        st.markdown("📦 **Una transportadora te ofrece el servicio de distribución de tu producto a un precio más bajo.**")
        st.markdown("🛠️ **Condición:** Servicio ofrecido sin costo adicional.")
        st.markdown("📉 **Beneficio:** Disminuye tus **gastos operacionales** en un 2% de forma permanente.")

        # Aplicar reducción de gastos operacionales
        jugador.empresa.gasto_operacional = int(jugador.empresa.gasto_operacional * 0.98)
        st.success("✅ Has tercerizado la distribución. Tus gastos operacionales se reducen en un 2%.")
    
    elif casilla == 7:
        st.markdown("### 📢 Oportunidad: Publicidad en Redes Sociales")
        st.markdown("💼 **Tu empresa tiene la opción de invertir en una campaña publicitaria en redes sociales.**")
        st.markdown("💰 **Condición:** Inversión de $5,000")
        st.markdown("💸 **Beneficio:** Ganas $15,000 adicionales por nuevas ventas.")

        if jugador.empresa.ingresos_netos >= 5000:
            col1, col2 = st.columns(2)
            with col1:
                invertir = st.button("✅ Invertir $5,000", key=f"invertir_publi_{jugador.nombre}")
            with col2:
                no_invertir = st.button("❌ No invertir", key=f"no_invertir_publi_{jugador.nombre}")

            if invertir:
                jugador.empresa.actualizar_ingresos(-5000)
                jugador.empresa.actualizar_ingresos(15000)
                st.success("🎉 ¡Tu inversión en publicidad fue un éxito! Ganaste $15,000.")
                st.write(f"📈 Ingresos netos actuales: ${jugador.empresa.ingresos_netos:,.0f}")
            elif no_invertir:
                st.info("Decidiste no invertir en publicidad en esta ocasión.")
        else:
            st.error("❌ No tienes suficientes ingresos netos para invertir.")








    elif casilla == 10:
        st.markdown("### 📣 Oportunidad: Campaña de Marketing")
        st.markdown("📈 **Una de las mejores agencias de marketing te propone una campaña prometedora que aumentaría tu demanda.**")
        st.markdown("💰 **Condición:** Requiere invertir $7,000.")
        st.markdown("🎲 **Beneficio:** Lanzas dos veces el dado y eliges el número mayor para avanzar.")

        decision = st.radio("¿Deseas invertir $7,000 en la campaña de marketing?", ["Sí", "No"], key=f"opp10_{jugador.nombre}")
        if decision == "Sí":
            if jugador.capital >= 7000:
                jugador.empresa.actualizar_ingresos(-7000)
                # Pedir dos valores de dado al usuario
                d1 = input_dado("¿Qué número sacaste en el primer dado?", f"opp10_d1_{jugador.nombre}")
                d2 = input_dado("¿Qué número sacaste en el segundo dado?", f"opp10_d2_{jugador.nombre}")
                mejor = max(d1, d2)
                avanzar(jugador, mejor)
                st.success(f"Avanzaste {mejor} casillas gracias a tu estrategia de marketing.")
            else:
                st.error("No tienes suficiente capital para esta inversión.")
        else:
            st.info("Has decidido no invertir en la campaña de marketing.")
    elif casilla == 13:
        opt = st.radio("¿Participar en concurso?", ["Sí","No"], key=f"opp13_{jugador.nombre}")
        if opt == "Sí": jugador.turnos_perdidos += 1; jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 0.85)
    elif casilla == 17:
        opt = st.radio("¿Invertir $19,000 en I+D?", ["Sí","No"], key=f"opp17_{jugador.nombre}")
        if opt == "Sí":
            ult = 10000 * jugador.last_roll
            jugador.empresa.actualizar_ingresos(-19000)
            jugador.empresa.actualizar_ingresos(ult * 2)
    elif casilla == 20:
        opt = st.radio("¿Invertir $22,000 en IA?", ["Sí","No"], key=f"opp20_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-22000); jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 0.85)
    elif casilla == 23:
        jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 0.95)
    elif casilla == 26:
        opt = st.radio("¿Invertir $21,000 en feria?", ["Sí","No"], key=f"opp26_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-21000); jugador.avance_extra = 3
    elif casilla == 29:
        opt = st.radio("¿Pagar $6,000 por asesoría?", ["Sí","No"], key=f"opp29_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-6000); jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 0.90)
    elif casilla == 33:
        opt = st.radio("¿Invertir $45,000 en sustentabilidad?", ["Sí","No"], key=f"opp33_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-45000); inc = int(jugador.empresa.ingresos_netos * 0.10); jugador.empresa.actualizar_ingresos(inc)
    elif casilla == 36:
        opt = st.radio("¿Comprar local por $52,000?", ["Sí","No"], key=f"opp36_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-52000); jugador.empresa.gasto_operacional = int(jugador.empresa.gasto_operacional * 0.50)
    elif casilla == 39:
        jugador.empresa.gasto_operacional = int(jugador.empresa.gasto_operacional * 0.94)
    elif casilla == 42:
        opt = st.radio("¿Formar alianza?", ["Sí","No"], key=f"opp42_{jugador.nombre}")
        if opt == "Sí": jugador.turnos_perdidos += 1; jugador.ingresos_dobles_rondas = 1
    elif casilla == 45:
        opt = st.radio("¿Pagar $40,000 por seguro?", ["Sí","No"], key=f"opp45_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-40000); jugador.seguro = 3
    elif casilla == 49:
        dev = int(jugador.empresa.ingresos_netos * 0.10); jugador.empresa.actualizar_ingresos(dev)
    elif casilla == 52:
        opt = st.radio("¿Invertir 60% utilidades?", ["Sí","No"], key=f"opp52_{jugador.nombre}")
        if opt == "Sí": inv = int(jugador.empresa.ingresos_netos * 0.60); jugador.empresa.actualizar_ingresos(-inv); jugador.ingresos_dobles_rondas = 2
    elif casilla == 55:
        opt = st.radio("¿Invertir $60,000 en expansión?", ["Sí","No"], key=f"opp55_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-60000); jugador.avance_extra = 2; jugador.ventas_extra_pct = 0; jugador.ventas_extra_duration = 3
    elif casilla == 58:
        opt = st.radio("¿Registrar marca por $50,000?", ["Sí","No"], key=f"opp58_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-50000); jugador.ventas_extra_pct = 0.80; jugador.ventas_extra_duration = 1
    elif casilla == 61:
        opt = st.radio("¿Invertir $55,000 en fidelización?", ["Sí","No"], key=f"opp61_{jugador.nombre}")
        if opt == "Sí": jugador.empresa.actualizar_ingresos(-55000); jugador.ventas_extra_pct = 0.15; jugador.ventas_extra_duration = 3

def amenaza(jugador, casilla):
    st.write(f"⚠️ {jugador.nombre} se enfrenta a Amenaza {casilla}")
    if jugador.seguro > 0:
        st.write("🛡️ Seguro activo: evitas la amenaza")
        jugador.seguro -= 1
        return
    if casilla == 3:
        jugador.turnos_perdidos += 2
    elif casilla == 6:
        jugador.posicion = max(0, jugador.posicion - 1)
    elif casilla == 9:
        jugador.empresa.actualizar_ingresos(-10000)
        jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 1.05)
    elif casilla == 12:
        jugador.ventas_extra_pct -= 0.05
        jugador.ventas_extra_duration = max(jugador.ventas_extra_duration, 2)
    elif casilla == 15:
        jugador.avance_extra = -1
        jugador.ventas_extra_duration = max(jugador.ventas_extra_duration, 4)
    elif casilla == 19:
        pasos = input_dado("¿Qué número sacaste en dado normativas?", f"am19_{jugador.nombre}")
        pct = 0.05 * pasos
        jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * (1 + pct))
    elif casilla == 22:
        jugador.posicion = max(0, jugador.posicion - 2)
        jugador.turnos_perdidos += 2
    elif casilla == 25:
        jugador.empresa.margen_ganancias = getattr(jugador.empresa, 'margen_ganancias', 0) - 0.05
    elif casilla == 28:
        jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 1.05)
    elif casilla == 31:
        jugador.posicion = max(0, jugador.posicion - 2)
    elif casilla == 35:
        jugador.posicion = max(0, jugador.posicion - 3)
        jugador.turnos_perdidos += 3
    elif casilla == 38:
        jugador.empresa.actualizar_ingresos(-30000)
    elif casilla == 41:
        pasos = input_dado("¿Qué número sacaste en dado maquinaria?", f"am41_{jugador.nombre}")
        jugador.posicion = max(0, jugador.posicion - pasos)
        jugador.empresa.actualizar_ingresos(-10000 * pasos)
    elif casilla == 44:
        jugador.empresa.ingresos_netos = int(jugador.empresa.ingresos_netos * 0.90)
    elif casilla == 47:
        jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 1.15)
    elif casilla == 51:
        jugador.empresa.actualizar_ingresos(int(-0.15 * jugador.empresa.ingresos_netos))
        jugador.turnos_perdidos += 1
    elif casilla == 54:
        jugador.ventas_extra_pct -= 0.10
        jugador.ventas_extra_duration = max(jugador.ventas_extra_duration, 2)
    elif casilla == 57:
        jugador.empresa.costo_produccion = int(jugador.empresa.costo_produccion * 1.10)
    elif casilla == 60:
        jugador.turnos_perdidos += 2
        jugador.avance_extra = -64
    elif casilla == 63:
        jugador.turnos_perdidos += 1
        jugador.empresa.margen_ganancias *= 0.90

# --- Interfaz del Juego ---
st.title("Juego Educativo: Emprendimiento & Contabilidad")
st.subheader(f"Ronda {st.session_state.turno}")
for idx, jugador in enumerate(st.session_state.jugadores):
    st.markdown(f"---\n## {jugador.nombre}")
    cols = st.columns([2,2,1])
    with cols[0]:
        for k, v in jugador.estado().items(): st.write(f"**{k}:** {v}")
    with cols[1]:
        if jugador.turnos_perdidos > 0:
            st.write(f"Pierde turno: {jugador.turnos_perdidos}")
            jugador.turnos_perdidos -= 1
        else:
            pasos = input_dado("¿Qué número sacaste en el dado?", f"roll_{idx}")
            if st.button(f"Registrar {jugador.nombre}", key=f"btn_{idx}"):
                avance, ingreso = avanzar(jugador, pasos)
                st.write(f"Avanzaste {avance} casillas y ganaste ${ingreso}")
                cas = jugador.posicion
                st.write(f"Casilla {cas}: {tablero[cas]}")
                if cas in casillas_oportunidad: oportunidad(jugador, cas)
                if cas in casillas_amenaza: amenaza(jugador, cas)
                if jugador.ventas_extra_duration > 0: jugador.ventas_extra_duration -= 1
                if jugador.ingresos_dobles_rondas > 0: jugador.ingresos_dobles_rondas -= 1
                if jugador.avance_extra > 0:
                    extra, inc = avanzar(jugador, jugador.avance_extra)
                    st.write(f"Bonus avance: {extra} casillas (+${inc})")
                    jugador.avance_extra -= 1
    with cols[2]: pass

# Verificar ganador
ganadores = [j for j in st.session_state.jugadores if j.posicion == 64]
if ganadores:
    winner = max(st.session_state.jugadores, key=lambda j: j.empresa.ingresos_netos)
    st.balloons()
    st.success(f"🎉 ¡{winner.nombre} gana con ${winner.empresa.ingresos_netos} de ingresos netos! 🎉")
    st.stop()

if st.button("Siguiente Ronda"):
    st.session_state.turno += 1
    st.experimental_rerun()

