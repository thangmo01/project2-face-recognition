import boto3   

def face_count(file_path: str):
    client=boto3.client('rekognition')
    with open(file_path, 'rb') as image:
        response = client.detect_faces(Image={'Bytes': image.read()})
    return len(response['FaceDetails'])


