#!/usr/bin/env python3
"""
Reducer para la Fase 1 de la Multiplicación de Matrices.
Agrupa los elementos por el índice compartido k.
Crea el producto cruzado de los elementos de A y B para el mismo k.
Emite: (i, j) \t (A[i][k] * B[k][j]) para que la Fase 2 sume los productos parciales.
"""

import sys

def emit_partial_products(key_k, list_A, list_B):
    """Genera y emite los productos parciales entre los elementos de A y B para un k dado."""
    if not list_A or not list_B:
        return
    
    for row_i, val_A in list_A:
        for col_j, val_B in list_B:
            product = val_A * val_B
            # Clave: fila_i,columna_j (coordenada final en la matriz resultante C)
            # Valor: producto parcial
            print(f"{row_i},{col_j}\t{product}")

def main():
    current_key = None
    list_A = []
    list_B = []
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) != 2:
            continue
            
        k_str, val_str = parts[0], parts[1]
        
        try:
            k = int(k_str)
        except ValueError:
            continue
            
        # Si la clave cambia, procesamos el grupo anterior
        if current_key is not None and current_key != k:
            emit_partial_products(current_key, list_A, list_B)
            list_A = []
            list_B = []
            
        current_key = k
        
        # Parsea el valor: 'A,i,val' o 'B,j,val'
        val_parts = val_str.split(',')
        if len(val_parts) != 3:
            continue
            
        matrix_type, idx_str, val_num_str = val_parts[0], val_parts[1], val_parts[2]
        
        try:
            idx = int(idx_str)
            val_num = float(val_num_str)
            
            if matrix_type == 'A':
                list_A.append((idx, val_num))
            elif matrix_type == 'B':
                list_B.append((idx, val_num))
        except ValueError:
            continue
            
    # No olvidar procesar el último grupo
    if current_key is not None:
        emit_partial_products(current_key, list_A, list_B)

if __name__ == "__main__":
    main()
