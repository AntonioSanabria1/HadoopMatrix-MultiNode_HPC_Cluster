#!/bin/bash
TARGET_DIR="/run/media/sanabria/Disco Local 2/Matrices"

echo "Generando matriz de 5000x5000 (Dispersa al 1%)..."
python3 generate_big_matrix.py 5000 0.01 "$TARGET_DIR/5000"

echo "Generando matriz de 10000x10000 (Dispersa al 0.5%)..."
python3 generate_big_matrix.py 10000 0.005 "$TARGET_DIR/10000"

echo "Generando matriz de 20000x20000 (Dispersa al 0.1%)..."
python3 generate_big_matrix.py 20000 0.001 "$TARGET_DIR/20000"

echo "Generando matriz de 40000x40000 (Dispersa al 0.01%)..."
python3 generate_big_matrix.py 40000 0.0001 "$TARGET_DIR/40000"

echo "¡Todas las matrices dispersas de prueba generadas con éxito en el Disco Local 2!"
