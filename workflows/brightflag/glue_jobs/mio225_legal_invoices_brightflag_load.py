# Job description : This is a wrapper script, used to load data to mio225_t_legal_invoices_fact tables by calling sql tranformation script.
# Purpose: Full and Delta refresh of Legal dtat from Brightflag
# Auth: Shantanu Roy
# Date: 13-Feb-2023
#
#
# =================================================================
# Change History
# =================================================================
# V      Date                 Author                 Description
# ---   ----------       -----------------   -----------------------
# 0.1    13-Feb-2023      Shantanu roy            Initial script
# ===============================================================


import sys
import json
import re
from pgdb import connect
from lib.aws_utils.glue_utils import get_job_parameter
import getpass
import boto3
import base64
from datetime import datetime
from botocore.exceptions import ClientError
from redshift_module import pygresql_redshift_common as rs_common
from lib.aws_utils.s3_client import S3Client
from lib.aws_utils.glue_utils import get_job_parameter
from lib.aws_utils.redshift_client import RedshiftClient
from lib.common.logger import get_logger
from lib.common.utils import get_environment
from lib.common.const import PYTHON_SHELL, FULL, DELTA, IN_PROCESS, ARCHIVE


# @params: [JOB_NAME]
v_env       = get_job_parameter("env")
topic_arn   = get_job_parameter("topic_arn")
region_name = get_job_parameter("region_name")
LOAD_TYPE   = get_job_parameter("load_type")

s3 = boto3.resource("s3")

# Flow variables
MIO_NAME = "mio225_legal_invoices"
FLOW_NAME = "brightflag"
JOB_NAME = "mio225_legal_spend_load" + "_" + v_env
USER_NAME = "mio_glue_system"

# List of files containing sql-scripts

SQL_FILE_NAMES = ["mio0225_legal_invoices_fact_load.sql"]

env = get_environment(get_job_parameter("env"))
log = get_logger(JOB_NAME)

concat_user_job = f"{USER_NAME}-{JOB_NAME}"
sql_file_prefix = f'{env["s3_env_dir"]}/scripts_glue/{MIO_NAME}/{FLOW_NAME}/transformation/'


#########################################
#  Log
#########################################
def method_log(msg):
    msg = str(msg) if not isinstance(msg, str) else msg
    print("[" + str(datetime.now()) + "]: [INFO] " + msg)


#########################################
#  Error Log
#########################################
def error_log(msg):
    msg = str(msg) if not isinstance(msg, str) else msg
    print("[" + str(datetime.now()) + "]: [ERROR] " + msg)


########################################
#  Function to run Sql transformation
#########################################
def load_data(sql_file_names):
    """Function to Execute SQL transformations"""

    method_log(sql_file_names)
    # List of tables, for which hash tag should be substituted with column list
    sql_tag_tables = {}
    source_table = "newly"
    sql_file_keys = [f"{sql_file_prefix}{sql_file_name}" for sql_file_name in sql_file_names]
    for sql_file_key in sql_file_keys:
        sql_statements = s3_client.read_file(sql_file_key).format(
            concat_user_job=concat_user_job
        )  # .format(source_system_cde=SOURCE_SYSTEM_CDE, concat_user_job=concat_user_job)\
        # .replace('#mio_process#', concat_user_job)

        log.info(sql_statements)

        # Replace sql hash tags
        # List of hash tags that should be substituted with column list
        sql_tags = re.findall("#\w*\.\w*#", sql_statements)
        for sql_tag in sql_tags:
            [sql_tag_statement, sql_tag_table] = [s.strip() for s in sql_tag.lower().strip("#").split(".")]
            if sql_tag_statement in ["insert", "select", "update"]:
                if sql_tag_table not in sql_tag_tables:
                    sql_tag_table_columns = rs_client.get_columns_list(schema="public", table_name=sql_tag_table)
                    sql_tag_table_data_columns = [
                        col for col in sql_tag_table_columns if not col.startswith("mio_") and not col.endswith("_guid")
                    ]
                    sql_tag_tables[sql_tag_table] = {
                        "insert": ",".join([f'"{col}"' for col in sql_tag_table_data_columns]),
                        "select": ",".join([f'"{source_table}"."{col}"' for col in sql_tag_table_data_columns]),
                        "update": ",".join(
                            [f'"{col}" = "{source_table}"."{col}"' for col in sql_tag_table_data_columns]
                        ),
                    }
                sql_statements = sql_statements.replace(sql_tag, sql_tag_tables[sql_tag_table][sql_tag_statement])
        log.info(sql_statements)

        rs_client.execute_query(sql_statements)


if __name__ == "__main__":
    try:
        s3_client = S3Client(env)
        rs_client = RedshiftClient.get_redshift_client(env, PYTHON_SHELL)

        # Step 1. Execute transformation SQL

        s3_client.move_files(source_name="BRIGHTFLAG/matter", from_dir=LOAD_TYPE, to_dir=IN_PROCESS)
        s3_client.move_files(source_name="BRIGHTFLAG/invoice", from_dir=LOAD_TYPE, to_dir=IN_PROCESS)
        s3_client.move_files(source_name="BRIGHTFLAG/lineitem", from_dir=LOAD_TYPE, to_dir=IN_PROCESS)
        s3_client.move_files(source_name="BRIGHTFLAG/timekeeper", from_dir=LOAD_TYPE, to_dir=IN_PROCESS)

        # Step 2. Call sql transformation sqcript
        load_data(SQL_FILE_NAMES)

        method_log("MIO data load sql transformation completed ")

        # Step 3. Move source file from in_process to archive folder after processing
        method_log("Putting S3 files in archive ")
        s3_client.move_files(source_name="BRIGHTFLAG/matter", from_dir=IN_PROCESS, to_dir=ARCHIVE+'/'+LOAD_TYPE)
        s3_client.move_files(source_name="BRIGHTFLAG/invoice", from_dir=IN_PROCESS, to_dir=ARCHIVE+'/'+LOAD_TYPE)
        s3_client.move_files(source_name="BRIGHTFLAG/lineitem", from_dir=IN_PROCESS, to_dir=ARCHIVE+'/'+LOAD_TYPE)
        s3_client.move_files(source_name="BRIGHTFLAG/timekeeper", from_dir=IN_PROCESS, to_dir=ARCHIVE+'/'+LOAD_TYPE)

        method_log("************* Mio225 Load glue Job complete ****************")
    except Exception as e:
        error_log(e)
        # SNS notification for job failure

        client = boto3.client("sns", region_name, verify=False)
        message = str(datetime.now()) + " - Glue Job: " + JOB_NAME + " has failed \n \nGlue Error Message : \n" + str(e)
        subject = "MIO Job Status Notification: " + JOB_NAME + " - Failed"
        client.publish(TopicArn=topic_arn, Message=message, Subject=subject)
        raise e
