# 3. Lógica Algorítmica y MapReduce (Python Streaming)

Este documento contiene la explicación matemática y el diseño técnico de los algoritmos implementados para realizar la transposición y la multiplicación matricial distribuidas de una matriz de gran escala bajo el paradigma MapReduce con Hadoop Streaming y Python.

---

## 1. Módulo de Transposición de Matriz

### Formato de Entrada
La matriz de entrada se almacena en formato **Denso Indexado** para ahorrar espacio en disco, o alternativamente en formato de coordenadas. 
- **Denso Indexado:** `i val0 val1 ... valN` (donde $i$ es el índice de la fila y el resto son sus valores).
- **Coordenadas:** `(i, j, v) \implies A_{i, j} = v`

Nuestros mappers de Fase 1 y Transposición detectan automáticamente cualquiera de los dos formatos.

### Fundamento Matemático
La transposición de una matriz $A$ para obtener $A^T$ se define como:

$$A^T_{j, i} = A_{i, j}$$

Es decir, el elemento en la fila $i$ y columna $j$ pasa a ser el elemento en la fila $j$ y columna $i$.

### Implementación MapReduce
Dado que la transposición es una operación puramente puntual (cada elemento se transforma de manera independiente y no requiere combinarse con otros para obtener el resultado), se utiliza la siguiente estrategia:

#### Estrategia Map-Reduce
* **Mapper ([transpose_map.py](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/transpose_map.py)):**
  Lee la línea, limpia los paréntesis y comas, y emite:
  
  $$\text{Key} = j \quad , \quad \text{Value} = i, v$$

  *Esto le indica a Hadoop que agrupe todos los elementos que compartirán la nueva fila $j$.*
* **Reducer ([transpose_reduce.py](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/transpose_reduce.py)):**
  Recibe los grupos por fila $j$, lee las tuplas de valores `i,v` y emite a HDFS la línea final en formato estándar de coordenadas:
  
  $$(j, i, v)$$


```mermaid
seqDiagram
    participant HDFS_In as HDFS Entrada
    participant Map as Mapper
    participant Shuffle as Hadoop Shuffle & Sort
    participant Red as Reducer
    participant HDFS_Out as HDFS Salida

    HDFS_In->>Map: Lee "(i, j, v)"
    Map->>Shuffle: Emite "j \t i,v"
    Note over Shuffle: Agrupa por la nueva fila 'j'
    Shuffle->>Red: Entrega "j" con lista de "i,v"
    Red->>HDFS_Out: Escribe "(j, i, v)"
```

---

## 2. Módulo de Multiplicación Matricial

Multiplicar dos matrices de gran escala presenta desafíos de ancho de banda y memoria en un clúster.

### Fundamento Matemático
Sean $A$ (de tamaño $I \times K$) y $B$ (de tamaño $K \times J$). Su producto $C = A \times B$ es una matriz de tamaño $I \times J$ donde cada celda se calcula como:

$$C_{i, j} = \sum_{k=0}^{K-1} A_{i, k} B_{k, j}$$


---

### Algoritmo de Dos Fases (Implementado)

#### Fase 1: Agrupar y Calcular Productos Parciales
1. **Mapper 1 ([multiply_map1.py](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/multiply_map1.py)):**
   Identifica a qué matriz pertenece la entrada según el archivo. Agrupa por el índice interno compartido $k$:
   * Si es de $A$ (elemento $A_{i,k}$): emite `k \t A,i,v`.
   * Si es de $B$ (elemento $B_{k,j}$): emite `k \t B,j,w`.
2. **Reducer 1 ([multiply_reduce1.py](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/multiply_reduce1.py)):**
   Para cada clave $k$, carga los elementos correspondientes a la columna $k$ de $A$ y la fila $k$ de $B$.
   Realiza el producto cruzado entre ellos y emite cada multiplicación individual etiquetada por su celda final destino:
   
   $$\text{Key} = i, j \quad , \quad \text{Value} = A_{i,k} \times B_{k,j}$$


```text
Entrada: k
Valores de A: [(i1, vA1), (i2, vA2), ...]
Valores de B: [(j1, vB1), (j2, vB2), ...]
Salida Reducer 1:
   i1,j1 \t vA1*vB1
   i1,j2 \t vA1*vB2
   ...
```

#### Fase 2: Agrupación y Suma Final
1. **Mapper 2 ([multiply_map2.py](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/multiply_map2.py)):**
   Actúa como un mapeador de identidad. Pasa las claves `i,j` y sus valores asociados al Shuffle de Hadoop.
2. **Combiner ([multiply_reduce2.py --combiner](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/multiply_reduce2.py)):**
   *Optimización clave:* Agrupa localmente en el nodo trabajador los valores de una celda `i,j` generados en esa máquina física y los pre-suma antes de enviarlos a través de la red LAN hacia el Reducer final. Esto reduce el tráfico por red.
3. **Reducer 2 ([multiply_reduce2.py](file:///home/sanabria/Documentos/Escuela/Cuatrimestre3/HPC3/Proyecto1_clean/mapreduce/multiply_reduce2.py)):**
   Recibe todas las sumas parciales para la celda destino `i,j`, realiza la acumulación final y escribe a HDFS en el formato estándar:
   
   $$(i, j, \text{suma})$$

