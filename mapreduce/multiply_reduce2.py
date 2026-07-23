#!/usr/bin/env python3
"""
Reducer para la Fase 2 de la Multiplicación de Matrices.
Agrupa los productos parciales por la clave (coordenada i,j) y los suma.
Soporta el parámetro '--combiner' para emitir salidas compatibles con una
siguiente fase intermedia (i,j \t suma_parcial), o la salida final (i, j, suma_total) en HDFS.
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Reducer de suma para multiplicación de matrices.")
    parser.add_argument('--combiner', action='store_true', help="Activa el formato de salida para Combiner (key-value).")
    args = parser.parse_args()
    
    current_key = None
    accumulated_sum = 0.0
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('\t')
        if len(parts) != 2:
            continue
            
        key_ij, val_str = parts[0], parts[1]
        
        try:
            val = float(val_str)
        except ValueError:
            continue
            
        # Si la clave cambia, emitimos la suma acumulada para el elemento anterior
        if current_key is not None and current_key != key_ij:
            if args.combiner:
                # El Combiner debe emitir en el mismo formato que el Mapper (key \t value)
                print(f"{current_key}\t{accumulated_sum}")
            else:
                # El Reducer final emite en formato de coordenadas (i, j, v)
                try:
                    i, j = current_key.split(',')
                    print(f"({i}, {j}, {accumulated_sum})")
                except ValueError:
                    pass
            accumulated_sum = 0.0
            
        current_key = key_ij
        accumulated_sum += val
        
    # Procesar el último grupo
    if current_key is not None:
        if args.combiner:
            print(f"{current_key}\t{accumulated_sum}")
        else:
            try:
                i, j = current_key.split(',')
                print(f"({i}, {j}, {accumulated_sum})")
            except ValueError:
                pass

if __name__ == "__main__":
    main()
