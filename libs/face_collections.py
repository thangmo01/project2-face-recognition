import boto3
from typing import List

def list_collections() -> List[str]:
    client = boto3.client('rekognition')
    response = client.list_collections()
    result = []
    collections = response['CollectionIds']
    result.extend(collections)
    return result

def collection_exists(coll_name: str):
    return coll_name in list_collections()

def create_collection(coll_name: str):
    from botocore.exceptions import ClientError
    client = boto3.client('rekognition')
    try:
        response = client.create_collection(CollectionId=coll_name)
    except ClientError as e:
        raise e.response['Error']['Code']

def delete_collection(coll_name: str):
    from botocore.exceptions import ClientError
    client = boto3.client('rekognition')
    try:
        client.delete_collection(CollectionId=coll_name)
    except ClientError as e:
        raise e.response['Error']['Code']

def list_faces(coll_name: str) -> List[dict]:
    client = boto3.client('rekognition')
    response = client.list_faces(CollectionId=coll_name)
    print(response)
    tokens = True
    result = []
    while tokens:
        faces = response['Faces']
        result.extend(faces)

        if 'NextToken' in response:
            next_token = response['NextToken']
            response = client.list_faces(CollectionId=coll_name,
                                         NextToken=next_token)
        else:
            tokens = False

    return result

def add_face(coll_name: str, bucket_name: str, image_key: str, external_image_id: str):
    client = boto3.client('rekognition')
    rekresp = client.index_faces(CollectionId=coll_name,
                                 Image={
                                    'S3Object': {
                                        'Bucket': bucket_name,
                                        'Name': image_key
                                    }    
                                 },
                                 ExternalImageId=external_image_id,
                                 MaxFaces=1)

    if rekresp['FaceRecords'] == []:
        raise Exception('No face found in the image')

def find_face_id(coll_name: str, ext_img_id: str) -> str:
    face = [face for face in list_faces(coll_name) if face['ExternalImageId'] == ext_img_id]
    if face != []:
        return face[0]['ImageId']
    else:
        return ''

def delete_face(coll_name: str, face_ids: List[str]) -> str:
    client = boto3.client('rekognition')
    response = client.delete_faces(CollectionId=coll_name,
                                   FaceIds=face_ids)
    return response['DeletedFaces']

def find_face_from_s3(coll_name: str, bucket_name: str, image_key: str, face_match_treshold: float = 80):
    client = boto3.client('rekognition')
    rekresp = client.search_faces_by_image(CollectionId=coll_name,
                                          Image={
                                            'S3Object': {
                                                'Bucket': bucket_name,
                                                'Name': image_key
                                            }
                                          },
                                          FaceMatchTreshold=face_match_treshold 
                                          )

    return rekresp['FaceMatches']

def find_face_from_local(coll_name: str, face_to_find: str, face_match_threshold: float = 80):
    client = boto3.client('rekognition')
    rekresp = client.search_faces_by_image(CollectionId=coll_name,
                                           Image={'Bytes': get_image_from_file(face_to_find)},
                                            FaceMatchThreshold=face_match_threshold 
                                          )

    return rekresp['FaceMatches']

def get_image_from_file(filename):
    with open(filename, 'rb') as imgfile:
        return imgfile.read()



