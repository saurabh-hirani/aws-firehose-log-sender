#!/bin/bash -e

aws lambda invoke --function-name test-firehose-log-sender-lambda --payload "$(cat $1)" test-lambda-response.json
echo
echo "Lambda function returned $(cat test-lambda-response.json)"
rm test-lambda-response.json
