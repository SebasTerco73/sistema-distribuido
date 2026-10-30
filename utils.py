import json

# 2) Envía y recibe objetos JSON por un socket. Se usa en servidor.py y worker.py.

def enviar_json(sock, obj):
    # Envía un objeto JSON por el socket, con un salto de línea al final para que el receptor sepa dónde termina el mensaje.
    sock.sendall((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))

def recibir_json(sock, buffer=b""):
    # Lee del socket hasta encontrar '\n'. Devuelve (dict | None, buffer_restante).
    # Devuelve None si el otro extremo cerró la conexión antes de enviar un mensaje completo.
    while b"\n" not in buffer:
        datos = sock.recv(4096)
        if not datos:
            return None, b""
        buffer += datos
    linea, _, resto = buffer.partition(b"\n")
    return json.loads(linea.decode("utf-8")), resto
