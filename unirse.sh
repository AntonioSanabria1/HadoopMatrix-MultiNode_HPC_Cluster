#!/usr/bin/env bash
# Script para unirse al Clúster de Hadoop como Nodo Trabajador (Worker).
# Uso: ./unirse.sh [IP_DEL_MAESTRO]

set -e

MASTER_IP=$1

# Si no se pasó la IP como argumento, solicitarla de forma interactiva
if [ -z "$MASTER_IP" ]; then
    echo "========================================================"
    echo "       UNIRSE AL CLÚSTER DE HADOOP (TRABAJADOR)"
    echo "========================================================"
    read -p "Ingresa la IP del Maestro (ej. 192.168.1.50): " MASTER_IP
fi

if [ -z "$MASTER_IP" ]; then
    echo "ERROR: Se requiere la IP del Maestro para poder unirse al clúster."
    exit 1
fi

# Detectar la IP física local de esta máquina en la subred LAN
MY_PHYSICAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "Conectando al Maestro en la IP: ${MASTER_IP}..."
echo "Mi IP física local detectada: ${MY_PHYSICAL_IP}"

# Remover contenedor trabajador anterior incondicionalmente
echo "Removiendo contenedor trabajador anterior si existe..."
docker rm -f hadoop-worker >/dev/null 2>&1 || true

echo "Desplegando contenedor trabajador (Worker)..."
docker run -d --net=host --name hadoop-worker \
  -e HADOOP_ROLE=worker \
  -e HADOOP_MASTER_IP="${MASTER_IP}" \
  -e MY_IP="${MY_PHYSICAL_IP}" \
  -e YARN_MEMORY_MB=4096 \
  -e YARN_VCORES=2 \
  antoniosanabria/hadoop-cluster-hpc

echo ""
echo "========================================================"
echo "      ¡TE HAS UNIDO AL CLÚSTER EXITOSAMENTE!"
echo "========================================================"
echo "Tu nodo trabajador ya está reportando recursos al Maestro."
echo "Puedes revisar los logs en vivo ejecutando:"
echo "  docker logs -f hadoop-worker"
echo "========================================================"
