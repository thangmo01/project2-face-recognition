import boto3

def upload_file_to_s3(file, content_type, bucket_name, region, key, acl="public-read"):
    client_s3 = boto3.client('s3')
    try:
        client_s3.upload_fileobj(
            file,
            bucket_name,
            key,
            ExtraArgs={
                "ACL": acl,
                "ContentType": content_type
            }
        )
    except Exception as e:
        print("Something Happened: ", e)
        return False
    return "https://s3-{}.amazonaws.com/{}/{}".format(region, bucket_name, key)
