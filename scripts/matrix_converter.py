#!/usr/bin/env python3
import sys
import os
import argparse
import random

def dense_to_coords(input_path, output_path, skip_zeros=False):
    """
    Converts a dense matrix (one row per line, space-separated values)
    to a coordinate matrix format: (i, j, val).
    Streams line-by-line to avoid loading the whole file into memory.
    """
    print(f"Converting dense matrix {input_path} -> coordinate matrix {output_path}...")
    try:
        with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
            for i, line in enumerate(infile):
                if i % 1000 == 0 and i > 0:
                    print(f"  Processed {i} rows...")
                parts = line.split()
                for j, val_str in enumerate(parts):
                    try:
                        val = float(val_str)
                        if skip_zeros and val == 0.0:
                            continue
                        outfile.write(f"({i}, {j}, {val_str})\n")
                    except ValueError:
                        print(f"Warning: Could not parse value '{val_str}' at row {i}, col {j}. Skipping.")
        print("Conversion completed successfully.")
    except Exception as e:
        print(f"Error during conversion: {e}")

def coords_to_dense(input_path, output_path, num_rows, num_cols):
    """
    Converts a coordinate matrix format: (i, j, val) to a dense matrix.
    Assumes the coordinate file is sorted by row index (i) to maintain
    a streaming approach and keep memory usage extremely low (1 row at a time).
    """
    print(f"Converting coordinate matrix {input_path} -> dense matrix {output_path} ({num_rows}x{num_cols})...")
    
    def write_row(outfile, row_data):
        outfile.write("  ".join(f"{val:.6f}" for val in row_data) + "\n")
        
    try:
        with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
            current_row = 0
            row_data = [0.0] * num_cols
            
            for line_num, line in enumerate(infile):
                line = line.strip()
                if not line:
                    continue
                
                # Parse (i, j, v)
                if line.startswith('(') and line.endswith(')'):
                    line = line[1:-1]
                parts = [p.strip() for p in line.split(',') if p.strip()]
                if len(parts) != 3:
                    continue
                
                try:
                    i = int(parts[0])
                    j = int(parts[1])
                    v = float(parts[2])
                except ValueError:
                    continue
                
                if i >= num_rows or j >= num_cols:
                    print(f"Warning: Index out of bounds ({i}, {j}) for shape {num_rows}x{num_cols} at line {line_num+1}. Skipping.")
                    continue
                
                if i != current_row:
                    # Write the finished row(s)
                    write_row(outfile, row_data)
                    # Handle any empty rows between current_row and i
                    for empty_r in range(current_row + 1, i):
                        write_row(outfile, [0.0] * num_cols)
                    # Reset for the new row
                    current_row = i
                    row_data = [0.0] * num_cols
                
                row_data[j] = v
                
            # Write the last row
            write_row(outfile, row_data)
            # Write any remaining empty rows to reach num_rows
            for empty_r in range(current_row + 1, num_rows):
                write_row(outfile, [0.0] * num_cols)
                
        print("Conversion completed successfully.")
    except Exception as e:
        print(f"Error during conversion: {e}")

def generate_test_matrices(output_dir, size=5):
    """
    Generates small random matrices A (size x size) and B (size x size)
    in both dense and coordinate formats for testing purposes.
    """
    print(f"Generating small test matrices of size {size}x{size} in {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate A
    dense_a_path = os.path.join(output_dir, "test_dense_a.txt")
    coords_a_path = os.path.join(output_dir, "test_coords_a.txt")
    
    with open(dense_a_path, 'w') as f_dense, open(coords_a_path, 'w') as f_coords:
        for i in range(size):
            row_vals = []
            for j in range(size):
                val = round(random.uniform(-10, 10), 6)
                row_vals.append(str(val))
                f_coords.write(f"({i}, {j}, {val})\n")
            f_dense.write("  ".join(row_vals) + "\n")
            
    # Generate B
    dense_b_path = os.path.join(output_dir, "test_dense_b.txt")
    coords_b_path = os.path.join(output_dir, "test_coords_b.txt")
    
    with open(dense_b_path, 'w') as f_dense, open(coords_b_path, 'w') as f_coords:
        for i in range(size):
            row_vals = []
            for j in range(size):
                val = round(random.uniform(-10, 10), 6)
                row_vals.append(str(val))
                f_coords.write(f"({i}, {j}, {val})\n")
            f_dense.write("  ".join(row_vals) + "\n")
            
    print(f"Test matrices generated:")
    print(f"  Matrix A: {dense_a_path} (dense) and {coords_a_path} (coords)")
    print(f"  Matrix B: {dense_b_path} (dense) and {coords_b_path} (coords)")

def main():
    parser = argparse.ArgumentParser(description="Matrix format converter (Dense <-> Coordinates) for MapReduce.")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # Parser for dense2coords
    p_d2c = subparsers.add_parser("dense2coords", help="Convert dense matrix to coordinate format (i, j, v).")
    p_d2c.add_argument("input", help="Path to the input dense matrix file.")
    p_d2c.add_argument("output", help="Path to the output coordinate matrix file.")
    p_d2c.add_argument("--skip-zeros", action="store_true", help="Skip writing elements that are 0.0.")
    
    # Parser for coords2dense
    p_c2d = subparsers.add_parser("coords2dense", help="Convert coordinate format (i, j, v) to dense matrix.")
    p_c2d.add_argument("input", help="Path to the input coordinate file.")
    p_c2d.add_argument("output", help="Path to the output dense matrix file.")
    p_c2d.add_argument("rows", type=int, help="Number of rows in the matrix.")
    p_c2d.add_argument("cols", type=int, help="Number of columns in the matrix.")
    
    # Parser for generate_test
    p_gen = subparsers.add_parser("generate_test", help="Generate small random test matrices.")
    p_gen.add_argument("--dir", default="Matrices/test", help="Directory where test matrices will be saved.")
    p_gen.add_argument("--size", type=int, default=5, help="Dimension of the square matrices.")
    
    args = parser.parse_args()
    
    if args.command == "dense2coords":
        dense_to_coords(args.input, args.output, args.skip_zeros)
    elif args.command == "coords2dense":
        coords_to_dense(args.input, args.output, args.rows, args.cols)
    elif args.command == "generate_test":
        generate_test_matrices(args.dir, args.size)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
