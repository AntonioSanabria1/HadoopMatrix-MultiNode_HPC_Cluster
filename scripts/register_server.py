#!/usr/bin/env python3
"""
Servidor HTTP de Registro de Trabajadores (Hadoop Workers).
Se ejecuta en el nodo maestro y expone un endpoint para que los trabajadores
registren su dirección IP física dinámicamente al arrancar.
Actualiza automáticamente el archivo $HADOOP_HOME/etc/hadoop/workers.
"""

import os
import subprocess
from flask import Flask, request

app = Flask(__name__)

# Definir la ruta del archivo workers de Hadoop
HADOOP_HOME = os.environ.get('HADOOP_HOME', '/opt/hadoop')
WORKERS_FILE = os.path.join(HADOOP_HOME, 'etc/hadoop/workers')

@app.route('/register', methods=['GET'])
def register_worker():
    ip = request.args.get('ip')
    if not ip:
        return "Error: Falta parametro 'ip'", 400
    
    ip = ip.strip()
    
    # Leer IPs de trabajadores existentes
    existing_workers = set()
    if os.path.exists(WORKERS_FILE):
        with open(WORKERS_FILE, 'r') as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#'):
                    existing_workers.add(line_stripped)
    else:
        # Crear directorio padre si no existe
        os.makedirs(os.path.dirname(WORKERS_FILE), exist_ok=True)
        
    if ip not in existing_workers:
        # Escribir la nueva IP en el archivo de trabajadores
        with open(WORKERS_FILE, 'a') as f:
            f.write(f"{ip}\n")
        print(f"[REGISTRO] Nuevo trabajador registrado: {ip}")
        
        # Opcionalmente, refrescar los nodos dinámicamente en HDFS y YARN si los servicios ya están activos
        try:
            subprocess.run([f"{HADOOP_HOME}/bin/hdfs", "dfsadmin", "-refreshNodes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([f"{HADOOP_HOME}/bin/yarn", "rmadmin", "-refreshNodes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[REGISTRO] Membresía de clúster actualizada dinámicamente en Hadoop.")
        except Exception as e:
            # Si Hadoop no se ha terminado de iniciar o da error, ignoramos el refresco
            pass
            
        return f"Trabajador {ip} registrado y clúster actualizado.", 200
    else:
        return f"Trabajador {ip} ya estaba registrado en el clúster.", 200

@app.route('/list', methods=['GET'])
def list_workers():
    """Endpoint de conveniencia para ver los trabajadores registrados."""
    if os.path.exists(WORKERS_FILE):
        with open(WORKERS_FILE, 'r') as f:
            content = f.read()
        return f"Trabajadores registrados:\n{content}", 200, {'Content-Type': 'text/plain'}
    return "No hay trabajadores registrados aún.", 200

if __name__ == '__main__':
    # Escucha en todas las interfaces físicas locales en el puerto 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
