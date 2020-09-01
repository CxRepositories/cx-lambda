from __future__ import print_function
from boto3.session import Session
from botocore.client import Config
import json
import boto3
import botocore
import traceback
import uuid
import os
from os import environ
import CxService

print('Loading function')

code_pipeline = boto3.client('codepipeline')
ssm = boto3.client('ssm')


def find_artifact(artifacts, name):
    for artifact in artifacts:
        if artifact['name'] == name:
            return artifact

    raise Exception('Input artifact named "{0}" not found in event'.format(name))


def get_artifact(s3, artifact):
    bucket = artifact['location']['s3Location']['bucketName']
    key = artifact['location']['s3Location']['objectKey']
    print("Artifact = " + bucket + key)
    filename = "/tmp/cx-" + str(uuid.uuid4()) + ".zip"
    s3.download_file(bucket, key, filename)
    return filename


def put_job_success(job, message):
    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job)


def put_job_failure(job, message):
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(jobId=job, failureDetails={'message': message, 'type': 'JobFailed'})


def get_user_params(job_data):
    try:
        # Get the user parameters which contain the stack, artifact and file settings
        user_parameters = job_data['actionConfiguration']['configuration']['UserParameters']
        decoded_parameters = json.loads(user_parameters)

    except Exception as e:
        # We're expecting the user parameters to be encoded as JSON
        # so we can pass multiple values. If the JSON can't be decoded
        # then fail the job with a helpful message.
        raise Exception('UserParameters could not be decoded as JSON')

    return decoded_parameters


def setup_s3_client(job_data):
    key_id = job_data['artifactCredentials']['accessKeyId']
    key_secret = job_data['artifactCredentials']['secretAccessKey']
    session_token = job_data['artifactCredentials']['sessionToken']

    session = Session(aws_access_key_id=key_id,
                      aws_secret_access_key=key_secret,
                      aws_session_token=session_token)
    return session.client('s3', config=botocore.client.Config(signature_version='s3v4'))


def lambda_handler(event, context):
    try:
        job_id = event['CodePipeline.job']['id'] # type: object
        if environ.get('CX_URL') is None or \
                environ.get('CX_USER') is None or \
                environ.get('CX_PASSWORD') is None:
            raise Exception('CX_URL, CX_USER, CX_PASSWORD must be provided')

        server = os.environ['CX_URL']
        user = os.environ['CX_USER']
        password = os.environ['CX_PASSWORD']

        ssm_flag = False
        if environ.get('SSM') is not None:
            ssm_flag = os.environ['SSM']

        if bool(ssm_flag):
            userParam = ssm.get_parameter(Name=user, WithDecryption=True)
            passwordParam = ssm.get_parameter(Name=password, WithDecryption=True)
            serverParam = ssm.get_parameter(Name=server)
            user = userParam['Parameter']['Value']
            password = passwordParam['Parameter']['Value']
            server = serverParam['Parameter']['Value']

        cx_config = {
            "preset": "Checkmarx Default",
            "configuration": "Default Configuration",
            "team": "\CxServer\SP\Checkmarx",
        }

        if environ.get('CX_PRESET') is not None:
            cx_config['preset'] = os.environ['CX_PRESET']
        if environ.get('CX_CONFIGURATION') is not None:
            cx_config['configuration'] = os.environ['CX_CONFIGURATION']
        if environ.get('CX_TEAM') is not None:
            cx_config['team'] = os.environ['CX_TEAM']

        # login to checkmarx
        cx = CxService.CxService(server + "/CxRestAPI", user, password, cx_config)

        # Extract the Job Data
        job_data = event['CodePipeline.job']['data']
        # Extract the params
        params = get_user_params(job_data)
        # default to SourceArtifact
        input_type = CxService.CxService.source_artifact
        if 'project' in params:
            cx_config['project'] = params['project']
        else:
            raise Exception("project must be provided")

        if 'team' in params:
            cx_config['team'] = params['team']
        if 'preset' in params:
            cx_config['preset'] = params['preset']
        if 'source' in params and params['source'] == "build":
            input_type = CxService.CxService.build_artifact

        print("Using the following config:")
        print(cx_config)

        # Get the list of artifacts passed to the function
        artifacts = job_data['inputArtifacts']

        artifact_data = find_artifact(artifacts, input_type)

        # Get S3 client to access artifact with
        s3 = setup_s3_client(job_data)
        source = get_artifact(s3, artifact_data)
        print("To scan: " + source)
        cx_config['file'] = source
        cx.start_scan(cx_config)
        put_job_success(job_id, "done")
    except Exception as e:
        print('Function failed due to exception.')
        print(e)
        traceback.print_exc()
        put_job_failure(job_id, 'Function exception: ' + str(e))

    print('Function complete.')
    return "Complete."
