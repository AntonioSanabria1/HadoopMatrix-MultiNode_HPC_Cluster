#!/usr/bin/env python3
import sys
import os
import random

def generate_matrix(size, density, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    file_a = os.path.join(output_dir, f"Matriz_A_{size}x{size}.txt")
    file_b = os.path.join(output_dir, f"Matriz_B_{size}x{size}.txt")

    print(f"Generando Matriz A ({size}x{size}) en {file_a} ...")
    with open(file_a, 'w') as f:
        for i in range(size):
            row = [str(i)]
            for j in range(size):
                if random.random() < density:
                    val = round(random.uniform(-10.0, 10.0), 6)
                    row.append(str(val))
                else:
                    row.append("0.0")
            f.write(" ".join(row) + "\n")
            
    print(f"Generando Matriz B ({size}x{size}) en {file_b} ...")
    with open(file_b, 'w') as f:
        for i in range(size):
            row = [str(i)]
            for j in range(size):
                if random.random() < density:
                    val = round(random.uniform(-10.0, 10.0), 6)
                    row.append(str(val))
                else:
                    row.append("0.0")
            f.write(" ".join(row) + "\n")
    print("Matrices generadas exitosamente.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python3 generate_big_matrix.py <tamaño> <densidad> <directorio_salida>")
        sys.exit(1)
        
    size = int(sys.argv[1])
    density = float(sys.argv[2])
    output_dir = sys.argv[3]
    
    generate_matrix(size, density, output_dir)
