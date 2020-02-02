import os
import sys
import json
import utils
import string
import time
from datetime import datetime, timezone, timedelta

import boto3


def load_input_params(event):
    """ Load input params """
    input_params = {}
    for field, field_type, default_val in [
        ("TMPL_VAR_LOG_TIMESTAMP", str, "log_timestamp"),
        ("TMPL_VAR_LOG_NUMBER", str, "log_number"),
        ("LOG_COUNT", int, 10),
        ("LOG_INTERVAL_MS", int, 10),
        ("LOG_LEVEL", str, "DEBUG"),
        ("AWS_ASSUME_ROLE_ARN", str, ""),
        ("AWS_ASSUME_ROLE_SESSION_NAME", str, "test_firehose_logs"),
        ("AWS_ASSUME_ROLE_DURATION_SEC", int, 900),
        ("AWS_REGION", str, "us-east-1"),
        ("AWS_FIREHOSE_STREAM_NAME", str, "NOT_PROVIDED"),
    ]:
        input_params[field] = field_type(os.environ.get(field, event.get(field, default_val)))

    return input_params


def validate_input_params(input_params):
    """ Validate input """
    errors = []
    for param in input_params:
        if input_params[param] == "NOT_PROVIDED":
            errors.append("{} not provided".format(param))

    if input_params["LOG_COUNT"] > 500:
        errors.append("LOG_COUNT should be <= 500")
    return errors


def get_epoch_ms():
    """ Return epoch timestamp in milliseconds """
    # https://stackoverflow.com/questions/5395872/how-can-i-create-a-python-timestamp-with-millisecond-granularity
    now = datetime.now(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)  # use POSIX epoch
    posix_timestamp_micros = (now - epoch) // timedelta(microseconds=1)
    return posix_timestamp_micros // 1000  # or `/ 1e3` for float


def load_log_template():
    """ Load log record template """
    return string.Template(open("templates/log_record.json").read())


def _aws_assume_role(input_params):
    """ Assume role and return session """
    sts_client = boto3.client("sts")
    response = sts_client.assume_role(
        RoleArn=input_params["AWS_ASSUME_ROLE_ARN"],
        RoleSessionName=input_params["AWS_ASSUME_ROLE_SESSION_NAME"],
        DurationSeconds=input_params["AWS_ASSUME_ROLE_DURATION_SEC"],
    )

    aws_access_key_id = response["Credentials"]["AccessKeyId"]
    aws_secret_access_key = response["Credentials"]["SecretAccessKey"]
    aws_session_token = response["Credentials"]["SessionToken"]

    return boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region_name=input_params["AWS_REGION"],
    )


def get_aws_session(input_params):
    """ Connect to AWS and return session object """
    if input_params["AWS_ASSUME_ROLE_ARN"] == "":
        # connect to current AWS account
        return boto3.Session(region_name=input_params["AWS_REGION"])
    return _aws_assume_role(input_params)


def lambda_handler(event, context):
    """ Send logs to Firehose """
    # Load input params
    input_params = load_input_params(event)

    # Load logger
    global logger
    logger = utils.setup_logging(name="firehose_logger", log_level=input_params["LOG_LEVEL"])

    logger.debug("dumping_input_params", extra={"input_params": input_params})

    # Validate input params
    errors = validate_input_params(input_params)
    if errors:
        for error in errors:
            logger.error("invaid_input", extra={"error": error})
        return "FAILED"

    # Load template
    template = load_log_template()

    # Get sender account number
    aws_account_number = boto3.client("sts").get_caller_identity().get("Account")

    # Connect to AWS
    try:
        aws_session = get_aws_session(input_params)
    except Exception as ex:
        logger.error("failed_to_assume_role", extra={"exception": str(ex)})
        raise ex

    logger.debug("dumping_aws_session_object", extra={"session": aws_session})

    # Generate payloads
    payloads = []
    for count in range(input_params["LOG_COUNT"]):
        payloads.append(
            json.loads(
                template.substitute(
                    **{
                        input_params["TMPL_VAR_LOG_TIMESTAMP"]: get_epoch_ms(),
                        input_params["TMPL_VAR_LOG_NUMBER"]: count + 1,
                        "src_aws_account_number": aws_account_number,
                    }
                )
            )
        )
        time.sleep(input_params["LOG_INTERVAL_MS"] / 1000.0)
        logger.debug("dumping_firehose_payload", extra={"payload": payloads[-1]})

    # Construct firehose payload
    firehose_client = aws_session.client("firehose")
    updated_payloads = [{"Data": bytes(json.dumps(payload), "utf-8")} for payload in payloads]

    # Send payload to firehose
    response = firehose_client.put_record_batch(
        DeliveryStreamName=input_params["AWS_FIREHOSE_STREAM_NAME"], Records=updated_payloads
    )

    # Validate result
    if response["FailedPutCount"] > 0:
        logger.error("failed_put_record_batch", extra={"response": response})

    logger.info("dumping_put_record_batch_response", extra={"response": response})

    return "SUCCESS"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("ERROR: Invalid usage. Provide payload as first arg.")
        sys.exit(1)

    event = json.loads(sys.argv[1])

    status = lambda_handler(event, None)

    if status == "SUCCESS":
        sys.exit(0)

    sys.exit(1)
