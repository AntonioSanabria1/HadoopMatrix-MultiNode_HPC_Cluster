#!/usr/bin/env python3
"""
Reducer para la Transposición de Matriz.
Recibe del Shuffle de Hadoop las líneas agrupadas por clave (nueva fila 'j').
Escribe el resultado final de la transposición en formato de lista de coordenadas (j, i, v).
"""

import sys

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        # Hadoop entrega la salida dividida por tabulador: clave \t valor
        parts = line.split('\t')
        if len(parts) != 2:
            continue
        
        j, val_str = parts[0], parts[1]
        
        # El valor contiene la nueva columna 'i' y el valor flotante 'v' separados por coma
        try:
            i_str, v_str = val_str.split(',')
            # Formateamos la salida tal como se especificó: (fila, columna, valor)
            # En la matriz transpuesta, la fila es 'j' y la columna es 'i'.
            print(f"({j}, {i_str}, {v_str})")
        except ValueError:
            # En caso de datos mal formateados, saltamos la línea
            continue

if __name__ == "__main__":
    main()
