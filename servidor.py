import socket
import sys
import threading

from utils import enviar_json, recibir_json

HOST = "localhost"
PUERTO = 5000
WORKERS = [(HOST, 6001), (HOST, 6002)]
TIMEOUT_WORKER = 10  

# Indice global de turno para recorrer los workers
_turno = 0
# Lock segura que solo un hilo pueda modificar _turno a la vez.
_lock = threading.Lock()

# 3.A) Calcula el índice del siguiente worker por turnos y actualiza _turno.
def siguiente_indice():
    global _turno
    with _lock:
        #_turno % len(WORKERS) ejemplo: si hay 3 workers y _turno=4, devuelve 1 (el segundo worker).
        indice = _turno % len(WORKERS)
        _turno += 1
    return indice

# 3.B) Envía la tarea a un worker y devuelve la respuesta
def enviar_a_worker(worker, tarea):
    with socket.create_connection(worker, timeout=TIMEOUT_WORKER) as s:
        enviar_json(s, tarea)
        respuesta, _ = recibir_json(s)
    if respuesta is None:
        raise ConnectionError("El worker cerró la conexión sin responder")
    return respuesta


# 3) Distribuye la tarea a los workers por turnos hasta encontrar uno que responda. Devuelve la respuesta del worker o un dict de error si ningún worker respondió.
def distribuir(tarea):
    inicio = siguiente_indice()
    for i in range(len(WORKERS)):
        worker = WORKERS[(inicio + i) % len(WORKERS)]
        try:
            print(f"[servidor] tarea {tarea} -> worker {worker[0]}:{worker[1]}")
            return enviar_a_worker(worker, tarea)
        except (OSError, ValueError) as e:
            print(f"[servidor] worker {worker} falló: {e}. Probando el siguiente...")
    return {"estado": "error", "error": "Ningún worker disponible"}

# 2) Maneja la conexión con un cliente: recibe tareas, las distribuye a los workers y devuelve las respuestas. Se ejecuta en un hilo por cada cliente.
def manejar_cliente(cliente, direccion):
    print(f"[servidor] conexión desde {direccion}")
    with cliente:
        buffer = b""
        while True:
            try:
                tarea, buffer = recibir_json(cliente, buffer)
            except (ValueError, OSError):
                try:
                    enviar_json(cliente, {"estado": "error", "error": "Mensaje inválido"})
                except OSError:
                    pass
                break
            if tarea is None:
                break
            try:
                enviar_json(cliente, distribuir(tarea))
            except OSError:
                break
    print(f"[servidor] {direccion} desconectado")

# 1) Parsea los argumentos de la línea de comandos
def parsear_args():
    global PUERTO, WORKERS
    if len(sys.argv) > 1:
        PUERTO = int(sys.argv[1])
    if len(sys.argv) > 2:
        WORKERS = []
        for arg in sys.argv[2:]:
            host, puerto = arg.split(":")
            WORKERS.append((host, int(puerto)))

def main():
    parsear_args()
    # Crea un socket TCP, lo enlaza a la dirección y puerto, y escucha conexiones entrantes. Por cada conexión, crea un hilo que maneja al cliente.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(20)
        print(f"[servidor] escuchando en {HOST}:{PUERTO} | workers: {WORKERS}")
        try:
            while True:
                cliente, direccion = servidor.accept()
                threading.Thread(
                    target=manejar_cliente, args=(cliente, direccion), daemon=True
                ).start()
        except KeyboardInterrupt:
            print("\n[servidor] cerrando...")

if __name__ == "__main__":
    main()
