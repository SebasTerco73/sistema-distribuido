import socket
import sys
import time
from utils import enviar_json, recibir_json

HOST = "localhost"
PUERTO = 5000

# 4) Envía una tarea al servidor y devuelve la respuesta
def enviar_tarea(tarea, intentos=3, espera=2):
    for intento in range(1, intentos + 1):
        try:
            with socket.create_connection((HOST, PUERTO), timeout=15) as s:
                enviar_json(s, tarea)
                respuesta, _ = recibir_json(s)
            if respuesta is None:
                raise ConnectionError("El servidor cerró la conexión sin responder")
            
            # Respuesta recibida correctamente, devolverla
            return respuesta
        
        except (OSError, ValueError) as e:
            print(f"Error de conexión (intento {intento}/{intentos}): {e}")
            if intento < intentos:
                time.sleep(espera)

    # Si no se pudo contactar al servidor después de los intentos, devolver un error
    return {"estado": "error", "error": "No se pudo contactar al servidor"}

# 5) Muestra la respuesta del servidor y del worker de manera legible para el usuario.
def mostrar(respuesta):
    if respuesta.get("estado") == "ok":
        print(f"  ✔ Resultado: {respuesta['resultado']}  (procesado por worker {respuesta['worker']})")
    else:
        print(f"  ✘ Error: {respuesta.get('error')}")

# python cliente.py --demo ejecuta una serie de tareas de ejemplo automáticamente, sin interacción del usuario.
def demo():
    tareas = [
        {"tarea": "sumar", "datos": [1, 2, 3, 4]},
        {"tarea": "invertir", "datos": "sistemas distribuidos - pfo número 3"},
        {"tarea": "contar_palabras", "datos": "Programación de redes y sistemas distribuidos"},
        {"tarea": "sumar", "datos": [10, 20, 30]},
        {"tarea": "inexistente", "datos": None},
        {"tarea": "dormir", "datos": 3}
    ]

    for t in tareas:
        print(f"Enviando: {t}")
        mostrar(enviar_tarea(t))

def menu():
    while True:
        op = input(
            "\n1) Sumar números\n2) Invertir texto\n3) Contar palabras\n"
            "4) Tarea lenta (dormir)\n5) Demo\n6) Salir\n> "
        ).strip()
        if op == "1":
            try:
                nums = [float(x) for x in input("Números separados por espacio: ").split()]
            except ValueError:
                print("Entrada inválida")
                continue
            mostrar(enviar_tarea({"tarea": "sumar", "datos": nums}))
        elif op == "2":
            mostrar(enviar_tarea({"tarea": "invertir", "datos": input("Texto: ")}))
        elif op == "3":
            mostrar(enviar_tarea({"tarea": "contar_palabras", "datos": input("Texto: ")}))
        elif op == "4":
            mostrar(enviar_tarea({"tarea": "dormir", "datos": input("Segundos: ")}))
        elif op == "5":
            demo()
        elif op == "6":
            break

if __name__ == "__main__":
    # Pruebas automáticas
    if "--demo" in sys.argv:
        demo()
    else:
        menu()
