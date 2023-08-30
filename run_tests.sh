#!/bin/bash

archive_files=("tests/test_calibrator/test_calibrator_archive.py" "tests/test_cholesky/test_cholesky_archive.py" \
"tests/test_converter/test_converter_archive.py" "tests/test_generator/test_generator_archive.py" \
"tests/test_input_reader/test_input_reader_archive.py" "tests/test_linefinder/test_finder_archive.py" \
"tests/test_output/test_save_cont_raw_archive.py" "tests/test_additional_columns/test_addcol_list_reader.py" \
"tests/test_additional_columns/test_addcol_query_reader.py")

ignored_archive_files=""
for file in "${archive_files[@]}"; do
  ignored_archive_files+=" --ignore=$file"
done

plotter_folder="tests/test_plotter"

if [ "$1" = "--no-archive" ]; then
  if [ "$2" = "--no-plotter" ]; then
    python -m pytest -s $ignored_archive_files --ignore="$plotter_folder"
  else
    python -m pytest -s $ignored_archive_files
  fi
elif [ "$1" = "--no-plotter" ]; then
  if [ "$2" = "--no-archive" ]; then
    python -m pytest -s $ignored_archive_files --ignore="$plotter_folder"
  else
    python -m pytest -s --ignore="$plotter_folder"
  fi
else
  python -m pytest -s
fi