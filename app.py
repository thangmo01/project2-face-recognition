from flask import Flask, request , Response
import json

import io, base64
import boto3
import uuid
import os

from config import AWS, DB
from libs.api_helper import *
from libs.database import *
from libs.image_process import *
from libs.face_collections import *
from libs.s3_helper import *
from libs.file_helper import *

app = Flask(__name__)

@app.route('/', methods = ['GET'])
def index():
    return 'Project2 API'

@app.route('/upload-student-image', methods = ['POST'])
def upload_student_image():
    #---- handle request ----#
    if 'image_file' not in request.files:
        return goResponse(400, 400, {}, "No image_file.")
    if 'outh_uid' not in request.form:
        return goResponse(400, 400, {}, "No outh_uid.")    
    if 'user_id' not in request.form:
        return goResponse(400, 400, {}, "No user_id.")       
    
    request_data = {
        'image_file': request.files['image_file'],
        'outh_uid': request.form['outh_uid'],
        'user_id': request.form['user_id']
    }
    
    image_content_type = request_data['image_file'].content_type
    if image_content_type != 'image/png' and image_content_type != 'image/jpeg':
        return goResponse(400, 400, {}, "File must be of JPEG or PNG format.")   
    if not request_data['outh_uid'] or not request_data['outh_uid'].isdigit():
        return goResponse(400, 400, {}, "outh_uid must be number.")           
    if not request_data['user_id'] or not request_data['user_id'].isdigit():
        return goResponse(400, 400, {}, "user_id must be number.")                       
    #---- handle request ----#
    
    #---- check outh_id in DB ----#
    select_stmt = (
        "SELECT id FROM users WHERE outh_uid = %s;"
    )
    db = connect_db(DB)
    cursor = db.cursor()
    cursor.execute(select_stmt, (request_data['outh_uid'], )) # https://blog.sqreen.com/preventing-sql-injections-in-python/
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user == None:
        return goResponse(400, 400, {}, "No match for outh_uid and user_id.")                           
    #---- check outh_id in DB ----#

    #---- check face before upload ----#
    image_tmp_name = '{}.{}'.format(uuid.uuid4().hex, image_type(image_content_type))
    image_tmp_path = os.path.join('img_temp', image_tmp_name)
    request_data['image_file'].save(image_tmp_path)
    faces = face_count(image_tmp_path)
    
    if faces != 1: 
        return goResponse(400, 400, {}, "1 face only.")                           
    #---- check face before upload ----#

    #---- upload to S3 ----#
    image_key = 'image/student/{}.{}'.format(uuid.uuid4().hex, image_type(image_content_type))
    img = open(image_tmp_path, "rb")
    image_link = upload_file_to_s3(img, image_content_type, AWS['S3_BUCKET_NAME'], AWS['S3_BUCKET_REGION'], image_key)
    if not image_link:
        return goResponse(400, 400, {}, "Upload failed.")                              
    #---- upload to S3 ----#

    #---- check duplicate image in a collection ----#
    coll_name = 'project2'
    face_id = find_face_id(coll_name, str(request_data['user_id']))
    if not face_id:
        add_face(coll_name, AWS['S3_BUCKET_NAME'], image_key, str(request_data['user_id']))
    else:
        delete_face(coll_name, [face_id])
        add_face(coll_name, AWS['S3_BUCKET_NAME'], image_key, str(request_data['user_id']))
    #---- check duplicate image in a collection ----#

    result = {
        'image_key': image_key,
        'image_link': image_link
    }
    os.remove(image_tmp_path)
    return goResponse(200, 200, result, "")

@app.route('/face-identify', methods = ['POST'])
def identify():
    #---- handle request data ----#
    request_data = {# https://www.programiz.com/python-programming/dictionary
        'class_id': request.json['class_id'],
        'image_blob': request.json['image_blob']
    }
    #---- handle request data ----#

    #---- model ----#
    select_stmt = (
        "SELECT * FROM classes WHERE id = %s;"
    )
    db = connect_db(DB)
    cursor = db.cursor()
    cursor.execute(select_stmt, (request_data['class_id'], )) # https://blog.sqreen.com/preventing-sql-injections-in-python/
    class_ = cursor.fetchone()
    cursor.close()
    db.close()
    #---- model ----#

    if(class_ == None):
        return goResponse(400, 400, {}, "class_id not match any classes")
    else:
        #---- identify ----# 
        image_tmp_name = '{}.{}'.format(uuid.uuid4().hex, 'jpg')
        image_tmp_path = os.path.join('img_temp', image_tmp_name)
        with open(image_tmp_path, "wb") as fh:
            fh.write(base64.b64decode(request_data['image_blob']))
        matches = find_face_from_local('project2', image_tmp_path, 90)
        #---- identify ----# 

        os.remove(image_tmp_path)
        
        if(matches) :
            result = {
                'user_id': matches[0]['Face']['ExternalImageId']
            }
            return goResponse(200, 200, result, "")
        else :
            return goResponse(200, 200, {}, "No match")

            
if __name__ == "__main__":
   app.run(host="0.0.0.0", port=3000, debug=True)
