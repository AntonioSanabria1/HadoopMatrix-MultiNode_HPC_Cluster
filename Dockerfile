# Dockerfile para Clúster Hadoop Heterogéneo
# Basado en Ubuntu 22.04 LTS para estabilidad y soporte de paquetes.

FROM ubuntu:22.04

# Evitar diálogos interactivos durante la instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar e instalar dependencias necesarias
# - openjdk-11-jdk-headless: Entorno Java ejecutable para Hadoop 3.x
# - openssh-server / openssh-client: Comunicación SSH sin contraseñas
# - wget: Descarga de Apache Hadoop
# - python3 y python3-pip: Para scripts MapReduce en Python
# - gettext: Provee 'envsubst' para procesamiento dinámico de archivos XML
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk-headless \
    openssh-server \
    openssh-client \
    wget \
    curl \
    python3 \
    python3-pip \
    gettext \
    rsync \
    pdsh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear symlink dinámico de JAVA_HOME para compatibilidad multi-arquitectura (amd64 y arm64/Apple Silicon)
RUN ln -s /usr/lib/jvm/java-11-openjdk-* /usr/lib/jvm/default-java

# Instalar bibliotecas de Python necesarias para la automatización (como Flask para el registro)
RUN pip3 install --no-cache-dir flask

# Configuración de variables de entorno globales
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
ENV HADOOP_LOG_DIR=$HADOOP_HOME/logs

# Escribir las variables de entorno en .bashrc para sesiones interactivas de SSH/bash
RUN echo "export JAVA_HOME=${JAVA_HOME}" >> /root/.bashrc && \
    echo "export HADOOP_HOME=${HADOOP_HOME}" >> /root/.bashrc && \
    echo "export HADOOP_CONF_DIR=${HADOOP_CONF_DIR}" >> /root/.bashrc && \
    echo "export PATH=\${PATH}:\${HADOOP_HOME}/bin:\${HADOOP_HOME}/sbin" >> /root/.bashrc

# Descargar e instalar Apache Hadoop 3.3.6
# Usamos el CDN de Apache para descargas rápidas y mostramos progreso.
RUN wget --progress=dot:giga https://dlcdn.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz && \
    tar -xzf hadoop-3.3.6.tar.gz -C /opt/ && \
    mv /opt/hadoop-3.3.6 $HADOOP_HOME && \
    rm hadoop-3.3.6.tar.gz

# Configurar SSH interno del contenedor
# 1. Creamos el directorio del demonio SSH y configuramos llaves
RUN mkdir /var/run/sshd && \
    mkdir -p /root/.ssh

# 2. Copiamos las llaves SSH pre-generadas para acceso passwordless
COPY ssh/id_rsa /root/.ssh/id_rsa
COPY ssh/id_rsa.pub /root/.ssh/id_rsa.pub
COPY ssh/authorized_keys /root/.ssh/authorized_keys

# 3. Establecemos permisos strictly requeridos por SSH
RUN chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/id_rsa && \
    chmod 644 /root/.ssh/id_rsa.pub && \
    chmod 600 /root/.ssh/authorized_keys

# 4. Modificamos la configuración de SSH para usar puerto 2222 y permitir root login
RUN sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config

# 5. Configurar cliente SSH para que por defecto conecte en puerto 2222 y no verifique firmas de hosts nuevos
RUN echo "Host *\n\tPort 2222\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile /dev/null\n" > /root/.ssh/config && \
    chmod 600 /root/.ssh/config

# Definir variables de entorno de Hadoop para usar SSH personalizado (puerto 2222)
ENV HADOOP_SSH_OPTS="-p 2222"

# Crear directorios de datos y logs para HDFS y YARN
RUN mkdir -p /opt/hadoop/data/dfs/name && \
    mkdir -p /opt/hadoop/data/dfs/data && \
    mkdir -p /opt/hadoop/data/tmp && \
    mkdir -p $HADOOP_LOG_DIR

# Copiar las plantillas XML de configuración de Hadoop al contenedor
RUN mkdir -p /opt/hadoop/templates
COPY config/*.xml.template /opt/hadoop/templates/

# Copiar scripts de MapReduce y utilidades al contenedor
RUN mkdir -p /opt/hadoop/mapreduce
COPY mapreduce/*.py /opt/hadoop/mapreduce/
RUN chmod +x /opt/hadoop/mapreduce/*.py 2>/dev/null || true

# Copiar script de entrada (entrypoint) y scripts de automatización
RUN mkdir -p /opt/hadoop/scripts
COPY scripts/* /opt/hadoop/scripts/
RUN chmod +x /opt/hadoop/scripts/* 2>/dev/null || true

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Crear directorio de trabajo
WORKDIR /opt/hadoop

EXPOSE 2222 9000 9870 9864 8032 8088 8042

ENTRYPOINT ["/entrypoint.sh"]
