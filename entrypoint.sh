#!/usr/bin/env bash
# Script de entrada para los contenedores de Hadoop.
# Levanta SSH, genera archivos de configuración dinámicos y arranca servicios según rol.

set -e

echo "Iniciando contenedor de Hadoop..."

# 1. Iniciar el servicio SSH interno en el puerto 2222
echo "Arrancando servidor SSH interno en el puerto 2222..."
/usr/sbin/sshd

# 2. Detectar la IP física local del nodo (si no viene explícita en MY_IP) y establecer la IP del Maestro
DEFAULT_DETECTED_IP=$(hostname -I | awk '{print $1}')
export MY_IP=${MY_IP:-$DEFAULT_DETECTED_IP}
export HADOOP_MASTER_IP=${HADOOP_MASTER_IP:-127.0.0.1}
export YARN_VCORES=${YARN_VCORES:-2}
export YARN_MEMORY_MB=${YARN_MEMORY_MB:-3072}

echo "IP local configurada (MY_IP): ${MY_IP}"
echo "IP del Maestro configurada en (HADOOP_MASTER_IP): ${HADOOP_MASTER_IP}"
echo "Recursos YARN asignados: ${YARN_VCORES} vCores / ${YARN_MEMORY_MB} MB RAM"

# Detectar la ruta real de JAVA_HOME para compatibilidad multi-arquitectura (amd64 vs arm64)
DETECTED_JAVA_HOME=$(find /usr/lib/jvm -maxdepth 1 -name "java-11-openjdk*" | head -n 1)
export JAVA_HOME=${DETECTED_JAVA_HOME:-/usr/lib/jvm/default-java}
echo "Ruta JAVA_HOME utilizada: ${JAVA_HOME}"

# 3. Generar los archivos XML finales reemplazando variables de entorno en las plantillas
echo "Procesando plantillas XML de configuración..."
for template in /opt/hadoop/templates/*.xml.template; do
    filename=$(basename "$template" .template)
    envsubst < "$template" > "$HADOOP_HOME/etc/hadoop/$filename"
    echo "  -> Generado: $HADOOP_HOME/etc/hadoop/$filename"
done

# 4. Configurar variables de entorno específicas en hadoop-env.sh
echo "Configurando variables de Java en hadoop-env.sh..."
echo "export JAVA_HOME=${JAVA_HOME}" >> "$HADOOP_HOME/etc/hadoop/hadoop-env.sh"
echo "export HADOOP_SSH_OPTS=\"-p 2222\"" >> "$HADOOP_HOME/etc/hadoop/hadoop-env.sh"

# Iniciar servicios según el rol
if [ "$HADOOP_ROLE" = "master" ]; then
    echo "Iniciando servicios en modo MAESTRO..."

    # Formatear el NameNode si es la primera ejecución
    if [ ! -d "/opt/hadoop/data/dfs/name/current" ]; then
        echo "Formateando NameNode..."
        "$HADOOP_HOME/bin/hdfs" namenode -format -force
    else
        echo "NameNode ya está formateado. Omitiendo formateo."
    fi

    # --- Servicios de GESTIÓN (NameNode + ResourceManager) ---
    echo "Arrancando HDFS NameNode..."
    "$HADOOP_HOME/bin/hdfs" --daemon start namenode

    echo "Arrancando YARN ResourceManager..."
    "$HADOOP_HOME/bin/yarn" --daemon start resourcemanager

    # --- Servicios de CÓMPUTO (DataNode + NodeManager) ---
    # El Maestro también contribuye almacenamiento y poder de cómputo al clúster.
    # Esto garantiza que los datos subidos localmente tengan bloques accesibles
    # y que las tareas MapReduce puedan ejecutarse con shuffle local (sin depender
    # de la red virtual de OrbStack/Docker Desktop en nodos Mac/Windows).
    echo "Arrancando HDFS DataNode (Maestro también almacena datos)..."
    "$HADOOP_HOME/bin/hdfs" --daemon start datanode

    echo "Arrancando YARN NodeManager (Maestro también ejecuta tareas)..."
    "$HADOOP_HOME/bin/yarn" --daemon start nodemanager

    # Iniciar el servidor HTTP de registro de trabajadores en segundo plano
    echo "Arrancando servidor HTTP de registro de trabajadores..."
    python3 /opt/hadoop/scripts/register_server.py &

    echo ""
    echo "=========================================="
    echo "  Maestro levantado con éxito."
    echo "  Servicios activos:"
    echo "    - HDFS NameNode + DataNode"
    echo "    - YARN ResourceManager + NodeManager"
    echo "    - Servidor de registro (puerto 5000)"
    echo "=========================================="

elif [ "$HADOOP_ROLE" = "worker" ]; then
    echo "Iniciando servicios en modo TRABAJADOR (WORKER)..."

    echo "Registrando IP con el maestro..."
    # Se reintenta 3 veces por si el maestro está iniciando
    for i in {1..3}; do
        curl -s -m 5 "http://${HADOOP_MASTER_IP}:5000/register?ip=${MY_IP}" && echo "Registro exitoso." && break || echo "Reintentando conexión con el maestro..."
        sleep 3
    done

    # Iniciar HDFS DataNode
    echo "Arrancando HDFS DataNode..."
    "$HADOOP_HOME/bin/hdfs" --daemon start datanode

    # Iniciar YARN NodeManager
    echo "Arrancando YARN NodeManager..."
    "$HADOOP_HOME/bin/yarn" --daemon start nodemanager

    echo "Trabajador levantado con éxito."

else
    echo "ADVERTENCIA: Rol '$HADOOP_ROLE' no reconocido o vacío. No se iniciarán servicios de Hadoop."
fi

# Mantener el contenedor activo (infalible en cualquier SO)
echo "Contenedor de Hadoop activo y en ejecución."
tail -f /dev/null
