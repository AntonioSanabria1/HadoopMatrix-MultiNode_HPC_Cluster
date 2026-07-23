# 1. Arquitectura de Red y Topología del Clúster

Este documento detalla el diseño de red, la topología del clúster distributed y los mecanismos de comunicación implementados para correr Apache Hadoop sobre laptops heterogéneas de estudiantes en un aula de clases.

---

## 1. Contexto de Red y Restricciones Físicas
En un entorno universitario de cómputo distribuido real, los estudiantes conectan sus computadoras a una **red física de área local (LAN)**, la cual suele ser la red inalámbrica (Wi-Fi) del salón o un switch local. Esto introduce tres desafíos fundamentales:
1. **Heterogeneidad de Sistemas Operativos:** Los estudiantes corren diferentes sistemas operativos (Windows, macOS, Linux) que no permiten configurar Hadoop de forma nativa e idéntica fácilmente.
2. **Aislamiento de Red de Docker:** Las redes internas por defecto de Docker (`bridge` locales o redes creadas por `docker-compose`) están aisladas dentro de cada máquina host. Los contenedores de diferentes laptops no pueden comunicarse de forma natural usando estas redes virtuales internas.
3. **Ancho de Banda Limitado:** La conexión Wi-Fi de un aula es un cuello de botella crítico para la fase de *Shuffle & Sort* de MapReduce, donde se transfieren grandes cantidades de datos intermedios.

---

## 2. Solución: Modo de Red `--net=host`
Para resolver el aislamiento de los contenedores Docker a través de distintas máquinas físicas, el diseño se basa rigurosamente en el parámetro:
```bash
docker run --net=host ...
```

### ¿Cómo funciona?
* El contenedor no obtiene su propia dirección IP asignada por Docker, ni se crea una interfaz de puente virtual.
* El contenedor comparte directamente el **espacio de nombres de red de la máquina host** (la laptop del alumno).
* Todo puerto que se abra dentro del contenedor se abrirá directamente en la IP física de la laptop del alumno en la subred de la LAN (ej. `192.168.1.X`).

```mermaid
graph TD
    subgraph Laptop1 ["Laptop 1 (Maestro)"]
        A[Contenedor Maestro] -- Comparte Red -- HostNet1[Host: 192.168.1.100]
    end
    subgraph Laptop2 ["Laptop 2 (Trabajador)"]
        B[Contenedor Trabajador 1] -- Comparte Red -- HostNet2[Host: 192.168.1.101]
    end
    subgraph Laptop3 ["Laptop 3 (Trabajador)"]
        C[Contenedor Trabajador 2] -- Comparte Red -- HostNet3[Host: 192.168.1.102]
    end
    HostNet1 <-->|LAN del Salón - Puerto 2222 y Hadoop Ports| HostNet2
    HostNet1 <-->|LAN del Salón - Puerto 2222 y Hadoop Ports| HostNet3
```

---

## 3. Conflictos de Puerto y Solución SSH (Puerto 2222)
Al utilizar `--net=host`, cualquier servicio dentro del contenedor compite por los puertos de la máquina física.
* **El Problema:** La mayoría de los desarrolladores y las laptops Linux/macOS ya tienen un servidor SSH (`sshd`) corriendo localmente en el puerto estándar `22`. Si el contenedor intenta levantar `sshd` en el puerto `22`, fallará por conflicto de puerto.
* **La Solución:** 
  1. Configuramos el demonio SSH del contenedor en el puerto **`2222`** modificando `/etc/ssh/sshd_config` (`Port 2222`).
  2. Configuramos el cliente SSH dentro de la imagen de Docker mediante el archivo `/root/.ssh/config` para establecer que cualquier conexión saliente use por defecto el puerto `2222` y omita la validación estricta de llaves:
     ```text
     Host *
         Port 2222
         StrictHostKeyChecking no
         UserKnownHostsFile /dev/null
     ```
  3. Definimos la variable de entorno de Hadoop: `HADOOP_SSH_OPTS="-p 2222"` en el script de arranque.
Esto permite que comandos como `start-dfs.sh` (los cuales requieren SSH entre nodos) funcionen con total transparencia utilizando el puerto `2222` sin interferir con el SSH del host de los estudiantes.

---

## 4. Servidor de Registro Dinámico de Trabajadores
En un aula de clases, las direcciones IP de las laptops son asignadas por el DHCP del router escolar y cambian constantemente. Es inviable configurar manualmente un archivo `workers` estático con las IPs antes de compilar la imagen.

Para solucionar esto, se implementa una **arquitectura de registro activo**:
1. **Servidor HTTP Flask en el Maestro:** El entrypoint del nodo maestro arranca un servidor Python en el puerto `5000` (`register_server.py`).
2. **Autoregistro del Trabajador:** Al iniciar el contenedor en modo `worker`, este detecta su propia IP física local mediante el comando `hostname -I` y realiza una petición HTTP al maestro:
   `curl http://<IP_MAESTRO>:5000/register?ip=<IP_TRABAJADOR>`
3. **Actualización en Caliente:** El script del maestro recibe la IP, la valida para no duplicarla y la escribe directamente en el archivo `$HADOOP_HOME/etc/hadoop/workers`.
4. **Refresco Dinámico:** El servidor del maestro ejecuta comandos internos (`hdfs dfsadmin -refreshNodes` y `yarn rmadmin -refreshNodes`) para notificar al clúster Hadoop la presencia del nuevo nodo sin necesidad de reiniciar los servicios globales.

---

## 5. Tolerancia a Fallos y Replicación
Las conexiones Wi-Fi escolares son inestables, y los alumnos pueden cerrar sus laptops o desconectarse del cargador (apagando la máquina) en cualquier momento.
* Para mitigar esto, en la configuración de HDFS (`hdfs-site.xml.template`) se fuerza un factor de replicación de **`3`** (`dfs.replication`).
* Esto significa que cada bloque de 128 MB de la matriz está almacenado simultáneamente en tres laptops distintas. Si un estudiante se desconecta, los datos siguen estando disponibles en otras dos máquinas y el trabajo de MapReduce se reprogramará en los nodos restantes de forma transparente, garantizando que el cálculo final (ya sea para matrices de $5000 \times 5000$, $10000 \times 10000$, $20000 \times 20000$ o hasta $40000 \times 40000$) no se corrompa.
