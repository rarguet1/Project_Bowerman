#!/bin/bash

INPUT_JSON_DIR=$1

if [ ! -d "$INPUT_JSON_DIR" ]; then
    echo "Whoops... $INPUT_JSON_DIR doesn't exist, try again!"
fi

for file in "$INPUT_JSON_DIR"*; do
    echo "Processing: $file"
    python normalize.py "$file" --conf --stdout | python ingest.py
done