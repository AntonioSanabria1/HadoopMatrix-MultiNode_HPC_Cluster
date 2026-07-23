#!/usr/bin/env bash
# Script de conveniencia para ejecutar los trabajos de MapReduce en HDFS.
# Uso: 
#   ./run_job.sh transpose <hdfs_input_path> <hdfs_output_path>
#   ./run_job.sh multiply <hdfs_input_A_path> <hdfs_input_B_path> <hdfs_output_path>

set -e

# Encontrar el JAR de Hadoop Streaming dinámicamente
STREAMING_JAR=$(find "$HADOOP_HOME" -name "hadoop-streaming-*.jar" | head -n 1)

if [ -z "$STREAMING_JAR" ]; then
    echo "ERROR: No se encontró hadoop-streaming-*.jar en $HADOOP_HOME."
    exit 1
fi

show_usage() {
    echo "Uso:"
    echo "  $0 transpose <hdfs_input> <hdfs_output>"
    echo "  $0 multiply <hdfs_input_A> <hdfs_input_B> <hdfs_output>"
    exit 1
}

# Limpiar directorio de salida en HDFS si ya existe
hdfs_clean_dir() {
    local dir=$1
    if "$HADOOP_HOME/bin/hdfs" dfs -test -d "$dir"; then
        echo "Directorio de salida HDFS existente detectado: $dir"
        echo "Eliminando directorio anterior..."
        "$HADOOP_HOME/bin/hdfs" dfs -rm -r -f "$dir"
    fi
}

run_transposition() {
    local input=$1
    local output=$2
    
    if [ -z "$input" ] || [ -z "$output" ]; then
        show_usage
    fi
    
    hdfs_clean_dir "$output"
    
    echo "=== Iniciando Trabajo de Transposición ==="
    echo "Entrada HDFS: $input"
    echo "Salida HDFS: $output"
    
    START_TIME=$(date +%s)
    
    "$HADOOP_HOME/bin/hadoop" jar "$STREAMING_JAR" \
        -files /opt/hadoop/mapreduce/transpose_map.py,/opt/hadoop/mapreduce/transpose_reduce.py \
        -mapper /opt/hadoop/mapreduce/transpose_map.py \
        -reducer /opt/hadoop/mapreduce/transpose_reduce.py \
        -input "$input" \
        -output "$output"
        
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
        
    echo "Trabajo de transposición completado con éxito."
}

run_multiplication() {
    local input_a=$1
    local input_b=$2
    local output=$3
    
    if [ -z "$input_a" ] || [ -z "$input_b" ] || [ -z "$output" ]; then
        show_usage
    fi
    
    local temp_phase1="/tmp/multiplication_phase1_$(date +%s)"
    
    hdfs_clean_dir "$temp_phase1"
    hdfs_clean_dir "$output"
    
    # Obtener el número total de vCores activos en el clúster usando la API de YARN
    echo "Consultando la capacidad del clúster para calcular los Reducers ideales..."
    NUM_REDUCERS=$(curl -s http://localhost:8088/ws/v1/cluster/metrics | python3 -c "import sys, json; print(json.load(sys.stdin).get('clusterMetrics', {}).get('totalVirtualCores', 1))" 2>/dev/null || echo "1")
    if [ "$NUM_REDUCERS" -lt 1 ]; then
        NUM_REDUCERS=1
    fi
    echo "--> vCores detectados en el clúster: $NUM_REDUCERS. Se lanzarán $NUM_REDUCERS Reducers distribuidos."
    
    echo "=== Iniciando Multiplicación: FASE 1 (Generación de Productos Parciales) ==="
    echo "Matriz A: $input_a"
    echo "Matriz B: $input_b"
    echo "Salida Temporal: $temp_phase1"
    
    START_TIME_1=$(date +%s)
    
    "$HADOOP_HOME/bin/hadoop" jar "$STREAMING_JAR" \
        -D mapreduce.job.reduces=$NUM_REDUCERS \
        -files /opt/hadoop/mapreduce/multiply_map1.py,/opt/hadoop/mapreduce/multiply_reduce1.py \
        -mapper /opt/hadoop/mapreduce/multiply_map1.py \
        -reducer /opt/hadoop/mapreduce/multiply_reduce1.py \
        -input "$input_a" \
        -input "$input_b" \
        -output "$temp_phase1"
        
    END_TIME_1=$(date +%s)
        
    echo "=== Iniciando Multiplicación: FASE 2 (Suma de Productos Parciales con Combiner) ==="
    echo "Entrada: $temp_phase1"
    echo "Salida Final: $output"
    
    # Ejecuta la agregación final.
    # Se usa el script multiply_reduce2.py tanto de Combiner como de Reducer.
    # El Combiner se ejecuta pasándole '--combiner' para mantener el formato key-value.
    START_TIME_2=$(date +%s)
    
    "$HADOOP_HOME/bin/hadoop" jar "$STREAMING_JAR" \
        -D mapreduce.job.reduces=$NUM_REDUCERS \
        -files /opt/hadoop/mapreduce/multiply_map2.py,/opt/hadoop/mapreduce/multiply_reduce2.py \
        -mapper /opt/hadoop/mapreduce/multiply_map2.py \
        -combiner "/opt/hadoop/mapreduce/multiply_reduce2.py --combiner" \
        -reducer /opt/hadoop/mapreduce/multiply_reduce2.py \
        -input "$temp_phase1" \
        -output "$output"
        
    END_TIME_2=$(date +%s)
        
    # Limpiar los productos parciales temporales
    echo "Limpiando archivos temporales en HDFS..."
    "$HADOOP_HOME/bin/hdfs" dfs -rm -r -f "$temp_phase1"
    
    ELAPSED_1=$((END_TIME_1 - START_TIME_1))
    ELAPSED_2=$((END_TIME_2 - START_TIME_2))
    TOTAL_ELAPSED=$((ELAPSED_1 + ELAPSED_2))
    
    echo ""
    echo "=========================================================="
    echo "  RESUMEN DE TIEMPOS DE EJECUCIÓN (PROFILING)"
    echo "=========================================================="
    echo "  Fase 1 (Generación de Productos): ${ELAPSED_1} segundos"
    echo "  Fase 2 (Suma con Combiner):       ${ELAPSED_2} segundos"
    echo "  --------------------------------------------------------"
    echo "  TIEMPO TOTAL DEL TRABAJO:         ${TOTAL_ELAPSED} segundos"
    echo "=========================================================="
    
    echo "Multiplicación matricial de dos fases completada con éxito."
}

# Evaluar el primer argumento
action=$1
shift

case "$action" in
    transpose)
        run_transposition "$@"
        ;;
    multiply)
        run_multiplication "$@"
        ;;
    *)
        show_usage
        ;;
esac
