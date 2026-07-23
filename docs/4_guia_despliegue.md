# 4. Guía de Despliegue y Ejecución Paso a Paso

Este documento contiene la guía operativa detallada para desplegar el clúster de Hadoop en Docker utilizando la imagen multi-arquitectura publicada en Docker Hub (`antoniosanabria/hadoop-cluster-hpc`) y los scripts automatizados `start_master.sh` y `unirse.sh`.

---

## 1. Requisitos Previos
1. **Docker Instalado:** Todos los estudiantes del aula deben tener Docker instalado y ejecutándose en su sistema host.
2. **Conexión a la misma LAN:** Todas las laptops deben estar conectadas a la misma red física del salón (ej. Wi-Fi del aula o un switch Ethernet portátil).
3. **Comprobar Conectividad (Ping):** Se recomienda verificar conectividad entre el maestro y los trabajadores:
   ```bash
   ping <IP_DEL_MAESTRO>
   ```

---

## 2. Despliegue del Nodo Maestro (Coordinador + Cómputo/Almacenamiento Local)

El estudiante a cargo de coordinar el clúster (Maestro) realizará los siguientes pasos:

1. Abrir la terminal en la raíz del proyecto.
2. Asegurar permisos de ejecución e iniciar el script del Maestro:
   ```bash
   chmod +x start_master.sh unirse.sh
   ./start_master.sh
   ```

### ¿Qué hace `start_master.sh` automáticamente?
* Detecta la IP física activa de la laptop en la red local (`hostname -I`).
* Remueve cualquier contenedor maestro previo si existía.
* Levanta el contenedor `hadoop-master` arrancando los servicios de **NameNode, ResourceManager, DataNode y NodeManager**.
* Muestra en pantalla la IP física detectada y el comando que deben correr sus compañeros.

---

## 3. Despliegue de los Nodos Trabajadores (Compañeros de clase)

Cada estudiante que participe aportando recursos (RAM/CPU) al clúster debe realizar lo siguiente:

### Opción Universal (Mac, Windows, Linux - ¡No necesitas descargar nada!):
```bash
docker pull antoniosanabria/hadoop-cluster-hpc
docker rm -f hadoop-worker 2>/dev/null || true
docker run -d --net=host --name hadoop-worker \
  -e HADOOP_ROLE=worker \
  -e HADOOP_MASTER_IP=<IP_DEL_MAESTRO> \
  -e MY_IP=<TU_IP_FISICA_WIFI> \
  -e YARN_VCORES=4 \
  -e YARN_MEMORY_MB=3072 \
  antoniosanabria/hadoop-cluster-hpc
```

### Opción Alternativa (Si ya tienes este proyecto descargado en Linux/Mac):
```bash
./unirse.sh <IP_DEL_MAESTRO>
```

---

## 4. Verificar Recursos y Nodos Conectados (RAM, CPU, HDFS)

El Maestro puede monitorear los recursos del clúster con estos comandos y paneles:

### A. Comandos en Terminal

1. **Verificar DataNodes (Almacenamiento HDFS y compañeros activos):**
   ```bash
   docker exec -it hadoop-master hdfs dfsadmin -report
   ```
   *(Muestra `Live datanodes (N)`, capacidad configurada y espacio libre en GB)*.

2. **Verificar NodeManagers (Memoria RAM y vCores totales del clúster):**
   ```bash
   docker exec -it hadoop-master yarn node -list -all
   ```
   *(Lista los nodos en estado `RUNNING`, memoria RAM y procesadores dedicados por cada compañero)*.

### B. Navegador Web (Laptop del Maestro)
* **Panel de HDFS:** [http://localhost:9870](http://localhost:9870)
* **Panel de YARN:** [http://localhost:8088](http://localhost:8088)

---

## 5. Ejecución de Trabajos para Matrices (Ejemplo con $5,000 \times 5,000$)

### 5.1. Limpiar directorio HDFS y Subir las matrices grandes:
(Para probar con otras dimensiones, cambia `5000` por `10000`, `20000`, o la ruta de tu matriz)
```bash
docker exec -it hadoop-master hdfs dfs -rm -r -f /input /salida_multiplicacion 2>/dev/null || true
docker exec -it hadoop-master hdfs dfs -mkdir -p /input
docker exec -it hadoop-master hdfs dfs -put /opt/hadoop/Matrices/5000/Matriz_A_5000x5000.txt /input/Matriz_A.txt
docker exec -it hadoop-master hdfs dfs -put /opt/hadoop/Matrices/5000/Matriz_B_5000x5000.txt /input/Matriz_B.txt
```

### 5.2. Ejecutar Multiplicación Distribuida (Fase 1 y Fase 2):
```bash
docker exec -it hadoop-master /opt/hadoop/scripts/run_job.sh multiply /input/Matriz_A.txt /input/Matriz_B.txt /salida_multiplicacion
```

### 5.3. Transponer la Matriz Resultante:
Si la lógica de negocio requiere que el resultado $C$ esté transpuesto:
```bash
docker exec -it hadoop-master /opt/hadoop/scripts/run_job.sh transpose /salida_multiplicacion /salida_final_transpuesta
```

### 5.4. Ver Resultados:
```bash
docker exec -it hadoop-master hdfs dfs -cat /salida_final_transpuesta/part-* | head -n 20
```
