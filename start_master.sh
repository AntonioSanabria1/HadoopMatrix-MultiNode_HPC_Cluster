#!/usr/bin/env bash
# Script para iniciar el nodo Maestro de Hadoop automáticamente.
# Detecta la IP física de la red local y levanta el contenedor.

set -e

# Detectar la IP física local de la máquina (omitiendo interfaces virtuales de docker)
MASTER_IP=$(hostname -I | awk '{print $1}')

if [ -z "$MASTER_IP" ]; then
    echo "ERROR: No se pudo detectar la IP de esta computadora. Verifica tu conexión de red."
    exit 1
fi

echo "========================================================"
echo "         INICIANDO NODO MAESTRO DE HADOOP"
echo "========================================================"
echo "IP física detectada para el Maestro: ${MASTER_IP}"
echo ""

# Crear la carpeta local de Matrices si no existe
mkdir -p "$(pwd)/Matrices"

# Remover contenedor maestro anterior de forma robusta si existe
if docker ps -a --format '{{.Names}}' | grep -q "^hadoop-master$"; then
    echo "Removiendo contenedor maestro anterior..."
    docker rm -f hadoop-master >/dev/null 2>&1 || sudo docker rm -f hadoop-master >/dev/null 2>&1 || true
fi

echo "Desplegando contenedor maestro con Docker..."
docker run -d --net=host --name hadoop-master \
  -e HADOOP_ROLE=master \
  -e HADOOP_MASTER_IP="${MASTER_IP}" \
  -e YARN_MEMORY_MB=4096 \
  -e YARN_VCORES=2 \
  -v "/run/media/sanabria/Disco Local 2/Matrices:/opt/hadoop/Matrices" \
  -v "/run/media/sanabria/Disco Local 2/HadoopProject/tmp:/tmp/hadoop-root" \
  -v "/run/media/sanabria/Disco Local 2/HadoopProject/data:/opt/hadoop/data" \
  -v "$(pwd)/mapreduce:/opt/hadoop/mapreduce" \
  -v "$(pwd)/scripts:/opt/hadoop/scripts" \
  antoniosanabria/hadoop-cluster-hpc

echo ""
echo "========================================================"
echo "          ¡MAESTRO INICIADO EXITOSAMENTE!"
echo "========================================================"
echo "Diles a tus compañeros que se conecten a la misma red"
echo "y ejecuten el siguiente comando en su terminal:"
echo ""
echo "  ./unirse.sh ${MASTER_IP}"
echo ""
echo "========================================================"
