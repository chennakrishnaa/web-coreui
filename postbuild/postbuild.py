import gzip
import boto3
import os
import sys
import threading
from botocore.exceptions import ClientError
from pathlib import Path
import shutil
from io import BytesIO

#cred = boto3.Session().get_credentials()

s3client = boto3.client('s3')
bucketname = 'kriman.io'
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucketname)
class ProgressPercentage(object):

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

def upload_gzipfile(file_name, key, gzip_object, metadata):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client
        response = s3client.put_object(
            Bucket=bucketname, 
            Body=gzip_object, 
            Key=key,
            Metadata={"Content-Encoding":"gzip"}
        )

    except ClientError as e:
        print(e)
        return False
    return True

list_of_files = (entry for entry in Path("../build/static/").glob("**/*") if entry.is_file())

def upload_gzipped(bucket, key, fp, compressed_fp=None, content_type='text/plain'):
    """Compress and upload the contents from fp to S3.
    If compressed_fp is None, the compression is performed in memory.
    """
    if not compressed_fp:
        compressed_fp = BytesIO()
    with gzip.GzipFile(fileobj=compressed_fp, mode='wb') as gz:
        shutil.copyfileobj(fp, gz)
    compressed_fp.seek(0)
    bucket.upload_fileobj(
        compressed_fp,
        key,
        {'ContentType': content_type, 'ContentEncoding': 'gzip'})

for file in list_of_files:
    print(file)
    if(file.suffix == '.css'):
        key="static/css/" + file.name 
        content_type="text/css"
    else:
        key="static/js/" + file.name
        content_type="text/javascript"

    with open(file, 'rb') as fp:
        upload_gzipped(bucket, key, fp, content_type=content_type)

    

# s3client = boto3.client('s3',
#                             aws_access_key_id=cred.access_key,
#                             aws_secret_access_key=cred.secret_key,
#                             aws_session_token=cred.token
#                             )

   
#key = 'filename.js'  

#s_in = b"Lots of content here"
#gzip_object = gzip.compress(s_in)

#s3client.put_object(Bucket=bucketname, Body=gzip_object, Key=key)

