#!/usr/bin/env python3
"""
Mapper para la Fase 1 de la Multiplicación de Matrices.
Soporta automáticamente AMBOS formatos de entrada:
  1. Formato Coordenadas: (i, j, v)
  2. Formato Denso: Valores flotantes separados por espacio o tabulador por cada fila.

Salidas producidas:
  Para Matriz A (elemento A[i][k] = v): emite "k \t A,i,v" (agrupa por columna k).
  Para Matriz B (elemento B[k][j] = w): emite "k \t B,j,w" (agrupa por fila k).
"""

import sys
import os

def main():
    # Obtener el nombre del archivo de entrada para discernir entre Matriz A y Matriz B
    input_file = os.environ.get('mapreduce_map_input_file', '').lower()
    
    parts = input_file.split('/')
    is_matrix_b = False
    if len(parts) >= 1:
        is_matrix_b = 'b' in parts[-1]
    if not is_matrix_b and len(parts) >= 2:
        is_matrix_b = 'b' in parts[-2]
    matrix_name = 'B' if is_matrix_b else 'A'
    
    row_index = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        # FORMATO 1: Coordenadas (i, j, v)
        if line.startswith('(') and line.endswith(')'):
            line_content = line[1:-1].replace('\t', ',').replace(' ', ',')
            p = [x.strip() for x in line_content.split(',') if x.strip()]
            if len(p) == 3:
                try:
                    row, col, val = int(p[0]), int(p[1]), float(p[2])
                    if matrix_name == 'A':
                        print(f"{col}\tA,{row},{val}")
                    else:
                        print(f"{row}\tB,{col},{val}")
                except ValueError:
                    pass
                    
        # FORMATO 2: Matriz Densa Indexada (Fila v1 v2 v3 ...)
        else:
            tokens = line.split()
            if len(tokens) >= 2:
                try:
                    row_idx = int(tokens[0])
                    for col_idx, tok in enumerate(tokens[1:]):
                        try:
                            val = float(tok)
                            if val != 0.0:
                                if matrix_name == 'A':
                                    # Elemento A[row_idx][col_idx] = val -> Clave: col_idx (k), Valor: A,row_idx,val
                                    print(f"{col_idx}\tA,{row_idx},{val}")
                                else:
                                    # Elemento B[row_idx][col_idx] = val -> Clave: row_idx (k), Valor: B,col_idx,val
                                    print(f"{row_idx}\tB,{col_idx},{val}")
                        except ValueError:
                            pass
                except ValueError:
                    pass

if __name__ == "__main__":
    main()
