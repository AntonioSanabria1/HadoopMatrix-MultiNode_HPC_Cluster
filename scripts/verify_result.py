#!/usr/bin/env python3
import sys
import os

def parse_coords_file(filepath):
    """Parsea un archivo de coordenadas (row, col, value)."""
    matrix = {}
    max_row, max_col = 0, 0
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Quitar paréntesis si existen
            if line.startswith('(') and line.endswith(')'):
                line = line[1:-1]
            parts = [p.strip() for p in line.split(',') if p.strip()]
            if len(parts) == 3:
                r, c, val = int(parts[0]), int(parts[1]), float(parts[2])
                matrix[(r, c)] = val
                if r > max_row: max_row = r
                if c > max_col: max_col = c
    return matrix, max_row + 1, max_col + 1

def parse_result_file(filepath):
    """Parsea el resultado del reducer (fila, col, valor)."""
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # El reducer emite usando tabulador o tupla de texto
            # Formato esperado: (i, j, valor) o i,j\tvalor
            if '\t' in line:
                key_part, val_part = line.split('\t')
                key_part = key_part.replace('(', '').replace(')', '')
                r, c = map(int, key_part.split(','))
                val = float(val_part)
                result[(r, c)] = val
            else:
                if line.startswith('(') and line.endswith(')'):
                    line = line[1:-1]
                parts = [p.strip() for p in line.split(',') if p.strip()]
                if len(parts) == 3:
                    r, c, val = int(parts[0]), int(parts[1]), float(parts[2])
                    result[(r, c)] = val
    return result

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_a = os.path.join(base_dir, "Matrices/test200/test_coords_a.txt")
    file_b = os.path.join(base_dir, "Matrices/test200/test_coords_b.txt")
    file_res = os.path.join(base_dir, "resultado_200x200.txt")

    if not os.path.exists(file_a) or not os.path.exists(file_b):
        print(f"Error: No se encuentran los archivos de entrada en Matrices/test200")
        sys.exit(1)
    if not os.path.exists(file_res):
        print(f"Error: No se encuentra el archivo de resultado {file_res}")
        sys.exit(1)

    print("Cargando matrices de entrada...")
    A, rows_A, cols_A = parse_coords_file(file_a)
    B, rows_B, cols_B = parse_coords_file(file_b)
    
    print(f"Dimensiones de A: {rows_A}x{cols_A} (Elementos cargados: {len(A)})")
    print(f"Dimensiones de B: {rows_B}x{cols_B} (Elementos cargados: {len(B)})")

    if cols_A != rows_B:
        print(f"Error: Dimensiones incompatibles para multiplicación: {cols_A} != {rows_B}")
        sys.exit(1)

    print("Cargando resultado de MapReduce...")
    obtained_C = parse_result_file(file_res)
    print(f"Elementos en resultado MapReduce: {len(obtained_C)}")

    print("Calculando producto de forma directa para validación...")
    # Multiplicación directa para coordenadas dispersas/densas
    expected_C = {}
    for i in range(rows_A):
        for j in range(cols_B):
            sum_val = 0.0
            for k in range(cols_A):
                val_A = A.get((i, k), 0.0)
                val_B = B.get((k, j), 0.0)
                sum_val += val_A * val_B
            if abs(sum_val) > 1e-9:  # Solo guardar no nulos si es dispersa
                expected_C[(i, j)] = sum_val

    # Comparación
    print("Comparando resultados...")
    errors = 0
    max_diff = 0.0
    compared = 0

    all_keys = set(expected_C.keys()).union(set(obtained_C.keys()))

    for (r, c) in all_keys:
        exp = expected_C.get((r, c), 0.0)
        obt = obtained_C.get((r, c), 0.0)
        diff = abs(exp - obt)
        if diff > max_diff:
            max_diff = diff
        if diff > 1e-4:
            if errors < 10:
                print(f"  Macho de celda ({r},{c}) no coincide: Esperado={exp:.6f}, Obtenido={obt:.6f} (Dif: {diff:.6f})")
            errors += 1
        compared += 1

    print("\n=== RESUMEN DE LA VALIDACIÓN ===")
    print(f"Celdas comparadas: {compared}")
    print(f"Diferencia máxima absoluta: {max_diff:.8e}")
    if errors == 0:
        print("¡ÉXITO ROTUNDO! La multiplicación distribuida es matemática y completamente correcta.")
    else:
        print(f"FALLO: Se encontraron {errors} discrepancias numéricas.")
        sys.exit(1)

if __name__ == "__main__":
    main()
