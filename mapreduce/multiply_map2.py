#!/usr/bin/env python3
"""
Mapper para la Fase 2 de la Multiplicación de Matrices.
Este es un Mapper de Identidad. Recibe la salida de la Fase 1: i,j \t product
y la redirige tal cual al Reducer para realizar la agregación final.
*Nota de Optimización*: En Hadoop Streaming, se puede usar '/bin/cat' directamente como
mapper de esta fase para ahorrar el arranque de intérpretes de Python adicionales.
"""

import sys

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        # Emitimos directamente la línea tal cual
        print(line)

if __name__ == "__main__":
    main()
