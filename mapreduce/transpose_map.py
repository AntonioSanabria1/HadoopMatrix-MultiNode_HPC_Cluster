#!/usr/bin/env python3
"""
Mapper para la Transposición de Matriz.
Convierte coordenadas (i, j, v) a (j, i, v).
Recibe las líneas por STDIN y emite (j, i, v) a través de STDOUT para el Reducer.
"""

import sys

def parse_line(line):
    """
    Parsea una línea en formato (i, j, v) de forma robusta.
    Soporta formatos tipo:
    - (i, j, v)
    - i,j,v
    - i\tj\tv
    """
    line = line.strip()
    if not line:
        return None
    
    # Quitar paréntesis exteriores si existen
    if line.startswith('(') and line.endswith(')'):
        line = line[1:-1]
        
    # Reemplazar tabulaciones y espacios por comas para estandarizar
    line = line.replace('\t', ',').replace(' ', ',')
    parts = [p.strip() for p in line.split(',') if p.strip()]
    
    if len(parts) == 3:
        try:
            i = int(parts[0])
            j = int(parts[1])
            v = float(parts[2])
            return i, j, v
        except ValueError:
            return None
    return None

def main():
    for line in sys.stdin:
        if line.strip().startswith('('):
            parsed = parse_line(line)
            if parsed is None:
                continue
            
            i, j, v = parsed
            # Formato de salida: clave \t valor
            print(f"{j}\t{i},{v}")
        else:
            # Formato Denso Indexado: fila val0 val1 ...
            tokens = line.split()
            if len(tokens) >= 2:
                try:
                    i = int(tokens[0])
                    for j, tok in enumerate(tokens[1:]):
                        try:
                            v = float(tok)
                            if v != 0.0:
                                print(f"{j}\t{i},{v}")
                        except ValueError:
                            pass
                except ValueError:
                    pass

if __name__ == "__main__":
    main()
