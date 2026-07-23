# 2. Infraestructura de Docker y Configuración de Hadoop

Este documento detalla la estructura y configuración de la imagen Docker de base, las tareas del script de entrada (`entrypoint.sh`), y la asignación de recursos y memoria parametrizados para las laptops de los estudiantes.

---

## 1. Estructura de Archivos del Proyecto
La raíz del proyecto está organizada de la siguiente manera:
* `start_master.sh`: Script para desplegar el nodo maestro detectando la IP física.
* `unirse.sh`: Script para que los compañeros se unan como trabajadores al clúster.
* `Dockerfile`: Especifica la compilación de la imagen base con Java, Hadoop, SSH y Python.
* `entrypoint.sh`: Inicializa los servicios específicos de Hadoop según el rol de la máquina.
* `config/`: Contiene las plantillas XML de configuración con variables de entorno.
* `mapreduce/`: Contiene los scripts de Mapper y Reducer escritos en Python.
* `scripts/`: Scripts utilitarios (servidor de registro e iniciador de trabajos).
* `ssh/`: Almacena la llave SSH RSA pre-generada para la comunicación interna sin contraseñas.
* `README.md`: Guía de referencia rápida para despliegue y uso.

---

## 2. Compilación y Diseño del Dockerfile
El [Dockerfile](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/Dockerfile) utiliza un esquema de capas optimizado basado en Ubuntu 22.04 LTS:

1. **Instalación de Dependencias:** Se instala OpenJDK 11 (requerido por Hadoop 3.x), servidor/cliente de SSH, Python 3, pip3 y `gettext` (provee la utilidad `envsubst` para pre-procesar los archivos XML de configuración).
2. **Descarga de Apache Hadoop:** Se descarga Hadoop 3.3.6 (versión estable) y se extrae en `/opt/hadoop`.
3. **Pre-configuración SSH sin contraseña:**
   * Se copian las llaves SSH generadas a `/root/.ssh/`.
   * Se ajustan permisos rigurosos: `700` para el directorio `.ssh`, `600` para la clave privada e `id_rsa.pub`, y `644` para `authorized_keys`.
   * Se fuerza a SSH a escuchar en el puerto `2222`.
4. **Configuración de Variables de Entorno:** Se exportan `JAVA_HOME`, `HADOOP_HOME`, `HADOOP_CONF_DIR`, y se añaden los binarios al `PATH` global de Linux y dentro del archivo `/root/.bashrc` para que las sesiones SSH mantengan las variables.

---

## 3. Lógica del Script de Entrada (`entrypoint.sh`)
El archivo [entrypoint.sh](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/entrypoint.sh) actúa como orquestador del ciclo de vida del contenedor:

```
[Inicio de Contenedor]
        │
        ├───> [Paso 1] Arrancar Servidor SSH interno (puerto 2222)
        │
        ├───> [Paso 2] Reemplazar variables LAN (${HADOOP_MASTER_IP}) en plantillas XML
        │
        ├───> [Paso 3] Escribir puertos e IP Java en config de Hadoop
        │
        └───> [Paso 4] Ramificación según HADOOP_ROLE
                    │
                    ├───> master
                    │       ├───> Formatear NameNode (si no tiene datos previos)
                    │       ├───> Arrancar HDFS NameNode
                    │       ├───> Arrancar YARN ResourceManager
                    │       └───> Iniciar Servidor de Registro en puerto 5000
                    │
                    └───> worker
                            ├───> Obtener IP física LAN (hostname -I)
                            ├───> curl de autoregistro al Maestro
                            ├───> Arrancar HDFS DataNode
                            └───> Arrancar YARN NodeManager
```

---

## 4. Parámetros de Configuración del Clúster (Hadoop XMLs)

Para lograr que Hadoop funcione en un ambiente real heterogéneo (donde hay laptops potentes y otras con recursos muy limitados), se modificaron los archivos de configuración en [config/](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/config/):

### core-site.xml.template
* Configura `fs.defaultFS` como `hdfs://${HADOOP_MASTER_IP}:9000` permitiendo que los DataNodes distribuidos localicen al NameNode maestro usando la IP física de la subred escolar.
* Redirecciona directorios temporales de Hadoop a `/opt/hadoop/data/tmp` para evitar llenar el almacenamiento del sistema host.

### hdfs-site.xml.template
* Configura `dfs.replication` en `3` para mayor tolerancia a fallas.
* Desactiva el mapeo inverso de DNS (`dfs.client.use.datanode.hostname = false`), obligando al clúster a comunicarse estrictamente por direcciones IP, ya que las redes Wi-Fi escolares no resuelven los nombres de hosts locales de los estudiantes.

### mapred-site.xml.template
* Asigna recursos máximos por contenedor de Map y Reduce para proteger a las laptops de congelamientos:
  * `mapreduce.map.memory.mb = 1024` (1 GB RAM por tarea Map).
  * `mapreduce.reduce.memory.mb = 1024` (1 GB RAM por tarea Reduce).
  * `mapreduce.map.java.opts = -Xmx800m` (Límite heap JVM a 800 MB).
  * `mapreduce.reduce.java.opts = -Xmx800m` (Límite heap JVM a 800 MB).
* Define el classpath de MapReduce para Hadoop 3.x, asegurando que cargue correctamente los componentes de Hadoop Streaming para Python.

### yarn-site.xml.template
* Configura `yarn.resourcemanager.hostname` apuntando a la IP del maestro.
* Limita el consumo total de recursos físicos que YARN puede tomar de cada laptop individual:
  * `yarn.nodemanager.resource.memory-mb = 2048` (2 GB de RAM dedicados por estudiante).
  * `yarn.nodemanager.resource.cpu-vcores = 2` (2 núcleos de procesamiento máximo).
* Desactiva chequeos estrictos de memoria física y virtual (`yarn.nodemanager.vmem-check-enabled = false` y `yarn.nodemanager.pmem-check-enabled = false`). En sistemas Windows con WSL2 o Linux con swap reducido, YARN suele abortar prematuramente procesos de Python debido a cómo calcula el uso de la memoria virtual. Desactivar esto garantiza la estabilidad de la ejecución.
