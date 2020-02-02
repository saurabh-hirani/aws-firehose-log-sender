#!/bin/bash -e

usage="$0 src_account_number target_account_number"

if [[ $# -ne 2 ]]; then
  echo "ERROR: Invalid usage"
  echo "Usage: $usage"
  exit 1
fi

src_account_number=$1
target_account_number=$2

aws lambda invoke --function-name test_firehose_logger --payload "$(cat test-lambda-$src_account_number-to-$target_account_number-payload.json)" test-lambda-response.json
echo
echo "Lambda function returned $(cat test-lambda-response.json)"
rm test-lambda-response.json
