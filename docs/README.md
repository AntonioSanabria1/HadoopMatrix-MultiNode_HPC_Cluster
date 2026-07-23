# Documentación del Clúster Hadoop Distribuido en Docker (Red LAN)

Este directorio contiene la documentación técnica estructurada y las guías operativas para compilar, configurar, desplegar y ejecutar algoritmos MapReduce sobre un clúster heterogéneo de Hadoop corriendo en contenedores Docker a través de la red física de un salón de clases.

---

## Índice de Documentación Detallada

Para comprender a fondo el funcionamiento e implementación de cada componente del proyecto, consulte los siguientes documentos ordenados lógicamente:

1. **[1. Arquitectura de Red y Topología](1_arquitectura_red.md):**
   * Justificación del modo de red `--net=host`.
   * Solución para el servicio SSH en el puerto alternativo `2222`.
   * Mecanismo de registro automático por HTTP para capturar IPs de estudiantes dinámicamente.
   * Estrategias de tolerancia a fallos en redes inalámbricas.

2. **[2. Componentes de la Infraestructura](2_componentes_infraestructura.md):**
   * Detalles de construcción de la imagen base mediante el `Dockerfile`.
   * Ciclo de vida y tareas del script de inicio `entrypoint.sh`.
   * Parametrización fina de CPU y límites de memoria RAM asignados en las plantillas XML de configuración de Hadoop (`core-site`, `hdfs-site`, `mapred-site`, `yarn-site`).

3. **[3. Lógica de los Algoritmos MapReduce](3_explicacion_algoritmos.md):**
   * Teoría matemática y modelado MapReduce en Python Streaming para la transposición matricial.
   * Análisis del tráfico de red para multiplicación de una fase vs. dos fases.
   * Implementación de la multiplicación distribuida en dos fases utilizando un *Combiner* local en los nodos para optimizar el canal físico.

4. **[4. Guía de Despliegue y Ejecución Paso a Paso](4_guia_despliegue.md):**
   * Instrucciones del uso de `start_master.sh` y `unirse.sh`.
   * Procedimiento de carga de matrices en HDFS.
   * Lanzamiento de ejecuciones usando `run_job.sh`.
   * Consulta de interfaces de monitoreo web de HDFS (`9870`) y YARN (`8088`).

---

## Resumen de Uso Rápido para Clase

### A. Iniciar Maestro (Solo el coordinador de clase)
```bash
docker compose up -d master
```

### B. Iniciar Trabajador (Demás alumnos de la clase)
```bash
docker compose up -d worker
```

### C. Ejecución de Trabajos (Solo en la terminal del Maestro)
```bash
# Ingresar al contenedor maestro
docker exec -it hadoop-master bash

# Ejecutar transposición:
/opt/hadoop/scripts/run_job.sh transpose /input/Matriz_A.txt /salida_traspuesta

# Ejecutar multiplicación:
/opt/hadoop/scripts/run_job.sh multiply /input/Matriz_A.txt /input/Matriz_B.txt /salida_multiplicacion
```
