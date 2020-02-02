#!/bin/bash

set -x
set -e

lambda_function_file=${1:-firehose_log_sender.py}

usage="$0 [lambda_function_file]"
PACKAGE_FILE_PATH='package.txt'

if ! [[ -f $lambda_function_file ]]; then
  echo "ERROR: Invalid uage. File $lambda_function_file does not exist"
  echo "$usage"
  exit 1
fi

lambda_function_zip="${lambda_function_file%.*}.zip"

virtual_env_dir="$(pwd)/venv"

echo "Using virtualenv: $virtual_env_dir"

# Backup already existing artifact
if [[ -f $lambda_function_zip ]]; then
  mv "$lambda_function_zip" "$lambda_function_zip.bkp"
fi

# Add virtualenv libs in new zip file
working_dir=$(pwd)
package_dir="$virtual_env_dir/lib/python3.7/site-packages"

if [[ -f $PACKAGE_FILE_PATH ]]; then
  package_file_contents=$(cat "$PACKAGE_FILE_PATH" | tr '\n' ' ')
else
  package_file_contents='*'
fi

cd "$package_dir" && zip -r9 -X "$lambda_function_zip" $package_file_contents
mv "$package_dir/$lambda_function_zip" "$working_dir"
cd "$working_dir" && zip -r9 -X "$lambda_function_zip" "$lambda_function_file" utils.py templates
