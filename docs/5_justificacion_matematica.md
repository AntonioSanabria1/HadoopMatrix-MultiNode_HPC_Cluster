# Justificación Matemática del Límite de Escalabilidad en MapReduce

La multiplicación de matrices de gran escala ($N = 40,000$) utilizando la arquitectura de Apache Hadoop impone desafíos de Entrada/Salida (I/O) en disco y red que superan la capacidad computacional y de almacenamiento de un clúster local estándar. A continuación se expone la demostración matemática rigurosa de por qué una Matriz 100% Densa colapsa el sistema, y cómo las Matrices Dispersas (Sparse) resuelven este problema en tiempo polinomial reducido.

## 1. Complejidad Algorítmica $O(N^3)$

Sean dos matrices cuadradas $A$ y $B$ de orden $N \times N$. El producto matricial $C = A \times B$ define cada entrada $C_{i,j}$ como:

$$C_{i,j} = \sum_{k=0}^{N-1} A_{i,k} \cdot B_{k,j}$$

Para calcular **una sola entrada** de $C$, se requieren $N$ multiplicaciones y $N-1$ sumas.
Como la matriz $C$ posee $N^2$ entradas en total, el número total de multiplicaciones cruzadas requeridas es estrictamente:

$$\text{Operaciones} = N^2 \cdot N = N^3$$


## 2. Emisión de Datos Intermedios en MapReduce

A diferencia del procesamiento en Memoria (RAM) con algoritmos compartidos (como OpenMP o NumPy), MapReduce opera bajo el paradigma **Shared-Nothing**. El algoritmo clásico elemento-por-elemento (*element-wise*) implementado en este proyecto distribuye la computación de la siguiente manera:

1. El **Mapper** aisla los elementos. Para cada entrada no nula, genera pares clave-valor que luego son transferidos por la red (Fase de Shuffle & Sort) hacia el disco local de los Reducers.
2. El **Reducer** realiza el producto cartesiano de vectores columna y vectores fila. Específicamente, para un índice compartido $k$, el Reducer ejecuta un doble bucle anidado que cruza cada $A_{i,k}$ con cada $B_{k,j}$.

Si la densidad de la matriz es $D = 1.0$ (100% Densa):
El número de productos parciales explícitos generados (y escritos en HDFS como texto) es exactamente $N^3$.

### Cálculo Físico para $N = 40,000$ (Densidad 100%)
* $N^3 = (40,000)^3 = 64,000,000,000,000$ (64 billones de productos parciales).
* Cada producto parcial emitido por el Reducer tiene el formato `i,j \t producto`. Un ejemplo típico: `39999,39999 \t -145.6789`, lo cual ocupa aproximadamente **20 bytes** en codificación UTF-8 / ASCII.

La cuota de disco duro (I/O) requerida únicamente para almacenar los resultados intermedios de la Fase 1 es:

$$\text{Volumen}_{Intermedio} \approx 64 \times 10^{12} \text{ operaciones} \times 20 \text{ bytes/operación}$$

$$\text{Volumen}_{Intermedio} \approx 1.28 \times 10^{15} \text{ bytes} \approx 1.28 \text{ Petabytes (PB)}$$

Un clúster LAN convencional no posee 1.28 PB de almacenamiento flash, ni el ancho de banda de red necesario para ordenar dicha magnitud de datos. El clúster colapsará con errores de `Disk out of space`.

---

## 3. Resolución Mediante Optimización de Matrices Dispersas (Sparse)

Hadoop fue diseñado para lidiar con topologías masivas donde la densidad probabilística de los datos es diminuta (e.g. Grafos de la web en PageRank). Si reducimos la densidad $D$, el impacto en el algoritmo MapReduce decrece exponencialmente.

Sea $D = 0.001$ ($0.1\%$ de densidad). La cantidad de entradas **no nulas** por cada fila/columna decrece de $N$ a $N \cdot D$.
El número total de multiplicaciones emitidas se define por:

$$\text{Operaciones}_{Sparse} = N \cdot (N \cdot D) \cdot (N \cdot D) = N^3 \cdot D^2$$


### Cálculo Físico para $N = 40,000$ (Densidad 0.1%)
* $\text{Operaciones} = 64,000,000,000,000 \times (0.001)^2$
* $\text{Operaciones} = 64,000,000,000,000 \times 0.000001 = 64,000,000$

Al emitir únicamente 64 millones de productos parciales, el volumen temporal de I/O en HDFS se reduce a:

$$\text{Volumen}_{Intermedio} \approx 64,000,000 \times 20 \text{ bytes} = 1.28 \text{ Gigabytes (GB)}$$


### Conclusión Arquitectónica
**1.28 GB** de transferencia en disco y red es una carga computacional trivial que el clúster Hadoop actual procesará en cuestión de minutos. Nuestro algoritmo fue diseñado matemáticamente de forma robusta: el Mapper omite cualquier celda con valor `0.0`. Por tanto, generar la matriz de entrada en formato Denso (preservando visualmente los ceros para integridad de la demostración) no impacta el clúster, ya que el Mapper purgará los ceros antes de iniciar la explosión $O(N^3)$. La arquitectura actual soporta operaciones matemáticas de altísima complejidad computacional apoyándose en principios de algebra lineal dispersa.
