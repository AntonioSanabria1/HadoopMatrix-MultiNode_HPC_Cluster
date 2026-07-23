# Multiplicación de Matrices Distribuida con Hadoop MapReduce en Docker

Este proyecto implementa una infraestructura distribuida de Hadoop (HDFS y YARN) ejecutable sobre contenedores Docker **multi-arquitectura (Intel/AMD `amd64` y Apple Silicon M1/M2/M3/M4 `arm64`)** para realizar operaciones matemáticas de gran escala (transposición y multiplicación de matrices de diferentes tamaños, ej. $5,000 \times 5,000$, $10,000 \times 10,000$, $20,000 \times 20,000$ y $40,000 \times 40,000$) en una red LAN local (ej. el salón de clases).

---

## Estructura del Proyecto

* **`start_master.sh`**: Script para iniciar el nodo Maestro (coordinador + nodo de datos/cómputo) detectando la IP física automáticamente.
* **`unirse.sh`**: Script para que los compañeros se unan como Trabajadores (Workers) al clúster detectando su IP local.
* **`config/`**: Plantillas XML de configuración de Hadoop (`core-site.xml`, `hdfs-site.xml`, `mapred-site.xml`, `yarn-site.xml`).
* **`mapreduce/`**: Scripts en Python para transposición y multiplicación de matrices en 2 fases con optimización de *Combiner*.
* **`scripts/`**: Utilidades auxiliares para:
  * Servidor de registro dinámico de nodos (`register_server.py`).
  * Ejecución de trabajos en HDFS (`run_job.sh`).
  * Conversor de matrices y script de validación matemática local.
* **`ssh/`**: Claves para comunicación segura y sin contraseña entre contenedores.
* **`docs/`**: Documentación técnica detallada del diseño y despliegue del proyecto.
* **`Matrices/`**: Carpeta local montada en el contenedor para almacenar las matrices de entrada (por ejemplo, en subcarpetas `5000/`, `10000/`, `20000/` y `40000/`).

---

## Guía Rápida de Despliegue en Clase (Con Docker Compose)

### 0. Configurar archivo `.env`
Antes de iniciar, debes crear un archivo `.env` en la raíz del proyecto. Puedes basarte en el archivo `.env.example`:
```bash
cp .env.example .env
```
Edita el archivo `.env` y configura las IPs físicas:
* `MASTER_IP`: La IP de la computadora que actuará como maestro.
* `MY_IP`: La IP de **tu propia computadora** en la red local (Wi-Fi o Ethernet). Si eres el maestro, será la misma que `MASTER_IP`.

### 1. Iniciar Maestro (Laptop del Coordinador)
En tu laptop, conéctate a la red y ejecuta:
```bash
docker compose up -d master
```
> **Nota:** El Maestro iniciará NameNode + ResourceManager y **también DataNode + NodeManager** para realizar cómputo y almacenamiento local.

---

### 2. Iniciar Trabajadores (Laptops de Compañeros - Mac / Windows / Linux)
Tus compañeros deben tener el archivo `docker-compose.yml` y su propio `.env` configurado. Luego, en su terminal ejecutan:
```bash
docker compose up -d worker
```

> **Notas Importantes:**
> * **Para detener o eliminar el nodo:** Simplemente ejecuta `docker compose down`.
> * **Asignación de Recursos:** Puedes modificar `YARN_VCORES` y `YARN_MEMORY_MB` en el archivo `.env` para asignar más o menos recursos.

---

## ¿Cómo verificar Recursos y Nodos Conectados (RAM, CPU, HDFS)?

### A. Desde la terminal del Maestro

1. **Ver DataNodes (Almacenamiento en HDFS):**
   ```bash
   docker exec -it hadoop-master hdfs dfsadmin -report
   ```
   *(Muestra `Live datanodes (N)`, espacio disponible en GB y estado de cada nodo)*.

2. **Ver NodeManagers (RAM y CPU totales en YARN):**
   ```bash
   docker exec -it hadoop-master yarn node -list -all
   ```
   *(Muestra la lista de laptops conectadas, estado `RUNNING`, memoria RAM y vCores asignados)*.

### B. Desde tu Navegador Web (Laptop del Maestro)
* **Panel de HDFS (Almacenamiento y Nodos):** [http://localhost:9870](http://localhost:9870)
* **Panel de YARN (Recursos de RAM, CPU y Trabajos):** [http://localhost:8088](http://localhost:8088)

---

## Ejecución de Trabajos para Matrices (Ejemplo con matrices de $5,000 \times 5,000$)

1. **Limpiar directorio HDFS anterior y subir las matrices:**
   (Cambia `5000` por la carpeta del tamaño que desees probar, ej. `10000`, `20000`, etc.)
   ```bash
   docker exec -it hadoop-master hdfs dfs -rm -r -f /input /salida_multiplicacion 2>/dev/null || true
   docker exec -it hadoop-master hdfs dfs -mkdir -p /input
   docker exec -it hadoop-master hdfs dfs -put /opt/hadoop/Matrices/5000/Matriz_A_5000x5000.txt /input/Matriz_A.txt
   docker exec -it hadoop-master hdfs dfs -put /opt/hadoop/Matrices/5000/Matriz_B_5000x5000.txt /input/Matriz_B.txt
   ```

2. **Lanzar Multiplicación Distribuida:**
   ```bash
   docker exec -it hadoop-master /opt/hadoop/scripts/run_job.sh multiply /input/Matriz_A.txt /input/Matriz_B.txt /salida_multiplicacion
   ```

3. **Transponer la Matriz Resultante:**
   (Si necesitas que el resultado final de C = A x B esté transpuesto)
   ```bash
   docker exec -it hadoop-master /opt/hadoop/scripts/run_job.sh transpose /salida_multiplicacion /salida_final_transpuesta
   ```

4. **Ver los Primeros Resultados:**
   ```bash
   docker exec -it hadoop-master hdfs dfs -cat /salida_final_transpuesta/part-* | head -n 20
   ```

---

## Documentación Detallada (Recomendado)

1. **[Arquitectura de Red y Topología](docs/1_arquitectura_red.md)**
2. **[Componentes de la Infraestructura](docs/2_componentes_infraestructura.md)**
3. **[Explicación de Algoritmos MapReduce](docs/3_explicacion_algoritmos.md)**
4. **[Guía de Despliegue y Ejecución Completa](docs/4_guia_despliegue.md)**
