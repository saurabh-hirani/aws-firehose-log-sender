#!/bin/bash -e

python3 firehose_log_sender.py "$(cat $1 | tr -d '\n')"  2>&1 | jq -R '. as $raw | try fromjson catch $raw'
