# aws-firehose-log-sender

AWS Lambda to send logs to a Kinesis Firehose hosted in another account. Also used for testing [sender example](https://github.com/saurabh-hirani/terraform-aws-firehose-elasticsearch/tree/master/examples/sender) setup for https://github.com/saurabh-hirani/terraform-aws-firehose-elasticsearch

## Pre-requisites

1. Setup a receiver AWS account with AWS Kinesis Firehose as described [here](https://github.com/saurabh-hirani/terraform-aws-firehose-elasticsearch/tree/master/examples/receiver)
2. Setup a sender AWS account with this lambda as described [here](https://github.com/saurabh-hirani/terraform-aws-firehose-elasticsearch/tree/master/examples/sender)

## Local setup

1. Setup and activate virtualenv as per instructions provided [here](https://gist.github.com/saurabh-hirani/3a2d582d944a792d0e896892e0ee0dea)

## Test locally

Before sending cross account (sender AWS account to receiver AWS account), try out this setup to send directly to the receiver AWS account from
your laptop.

1. Ensure that you have the AWS credentials set in your environment for the receiver AWS account which hosts the AWS Kinesis firehose.

2. Update the config file ```test-localhost.json``` if required:

    ```sh
    {
        "TMPL_VAR_LOG_TIMESTAMP": "log_timestamp",
        "TMPL_VAR_LOG_NUMBER": "log_number",
        "LOG_COUNT": 10,
        "LOG_INTERVAL_MS": 10,
        "LOG_LEVEL": "DEBUG",
        "AWS_REGION": "us-east-1",
        "AWS_FIREHOSE_STREAM_NAME": "test-firehose"
    }
    ```

    where

    | Sr. No. | Item                     |                  Description                                                         |
    |:-------:|:-----------------------: |:------------------------------------------------------------------------------------ |
    |    1    | TMPL_VAR_LOG_TIMESTMAP   | Timestamp field template var in ```templates/log_record.json```                      |
    |    2    | TMPL_VAR_LOG_NUMBER      | Log number field template var in ```templates/log_record.json```                     |
    |    3    | LOG_COUNT                | No. of log records to send - max value - 500                                         |
    |    4    | LOG_LEVEL                | Log level                                                                            |
    |    5    | AWS_REGION               | AWS region to use while creating AWS session                                         |
    |    6    | AWS_FIREHOSE_STREAM_NAME | AWS Firehose stream to send logs to                                                  |

3. Run the following command:

    ```sh
    ./test-localhost.sh test-localhost.json
    ```

    Verify the terminal logs last line to check ```HTTPStatusCode``` of the log submission call.

    ```sh
    "ResponseMetadata": {
      "RequestId": "xxx-xxx-xxx",
      "HTTPStatusCode": 200,
      "HTTPHeaders": {
        "x-amzn-requestid": "xxx-xxx-xx",
        "x-amz-id-2": "xxx-xxx-xxx",
        "content-type": "application/x-amz-json-1.1",
        "content-length": "1234",
        "date": "Sat, 08 Feb 2020 00:00:00 GMT"
      },
      "RetryAttempts": 0
    }
    ```

4. Check AWS Kinesis Firehose and AWS Elasticsearch dashboards to verify if logs have reached the destination.

## Test cross account

1. Ensure that you have the AWS credentials set in your environment for the sender AWS account which hosts the AWS Kinesis firehose.

2. Update the config file ```test-lambda.json``` if required:

    ```sh
    {
        "AWS_ASSUME_ROLE_ARN": "arn:aws:iam::12345678:role/test-firehose-kinesis_agent",
        "AWS_FIREHOSE_STREAM_NAME": "test-firehose"
    }
    ```

    where

    | Sr. No. | Item                     |                  Description                                                         |
    |:-------:|:-----------------------: |:------------------------------------------------------------------------------------ |
    |    1    | AWS_ASSUME_ROLE_ARN      | AWS role to assume of the receiver AWS account                                       |
    |    2    | AWS_FIREHOSE_STREAM_NAME | AWS Firehose stream to send logs to                                                  |

3. Run the following command:

    ```sh
    export AWS_DEFAULT_REGION=us-east-1
    ./test-lambda.sh test-lambda.json
    ```

4. You should see a response like the following:

    ```sh
    {
        "StatusCode": 200,
        "ExecutedVersion": "$LATEST"
    }
    Lambda function returned "SUCCESS"
    ```

5. Check AWS Kinesis Firehose and AWS Elasticsearch dashboards to verify if logs have reached the destination.
