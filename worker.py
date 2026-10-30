import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from utils import enviar_json, recibir_json

HOST = "localhost"

def tarea_sumar(datos):
    return sum(datos)

def tarea_invertir(datos):
    # Al estar vacio inicio y fin y pasos en negativo, python entiende que debe recorrer la cadena de atras hacia adelante y devolverla invertida.
    return str(datos)[::-1]

def tarea_contar_palabras(datos):
    return len(str(datos).split())

def tarea_dormir(datos):
    # útil para ver el pool de hilos en acción
    time.sleep(float(datos))
    return f"dormí {datos}s"


TAREAS = {
    "sumar": tarea_sumar,
    "invertir": tarea_invertir,
    "contar_palabras": tarea_contar_palabras,
    "dormir": tarea_dormir,
}

# 7) Procesa un mensaje recibido del cliente y devuelve la respuesta correspondiente. Se ejecuta en un hilo por cada tarea.
def procesar(mensaje, id_worker):
    nombre = mensaje.get("tarea")

    funcion = TAREAS.get(nombre)
    
    if funcion is None:
        return {"estado": "error", "error": f"Tarea desconocida: {nombre}", "worker": id_worker}
    try:
        resultado = funcion(mensaje.get("datos"))
        return {"estado": "ok", "resultado": resultado, "worker": id_worker}
    except Exception as e:  
        return {"estado": "error", "error": str(e), "worker": id_worker}

# 6) Atiende la conexión con un cliente: recibe tareas, las procesa y devuelve las respuestas. Se ejecuta en un hilo por cada cliente.
def atender_conexion(conexion, direccion, id_worker):
    with conexion:
        buffer = b""
        while True:
            try:
                mensaje, buffer = recibir_json(conexion, buffer)
            except (ValueError, OSError):
                break
            if mensaje is None:
                break
            hilo = threading.current_thread().name
            print(f"[worker {id_worker}] ({hilo}) tarea de {direccion} recibida: {mensaje}")
            enviar_json(conexion, procesar(mensaje, id_worker))


def main():
    if len(sys.argv) < 2:
        print("Uso: python worker.py <puerto> [hilos]")
        sys.exit(1)
    puerto = int(sys.argv[1])
    hilos = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    id_worker = puerto  # identificador simple

    pool = ThreadPoolExecutor(max_workers=hilos, thread_name_prefix=f"w{id_worker}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, puerto))
        srv.listen(10)
        print(f"[worker {id_worker}] escuchando en {HOST}:{puerto} con pool de {hilos} hilos")
        try:
            while True:
                conexion, direccion = srv.accept()
                pool.submit(atender_conexion, conexion, direccion, id_worker)
        except KeyboardInterrupt:
            print(f"\n[worker {id_worker}] cerrando...")
        finally:
            pool.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
