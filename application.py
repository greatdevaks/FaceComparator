import boto3
import os

from flask import Flask, request, render_template
from flask_uploads import UploadSet, configure_uploads, IMAGES

app = Flask(__name__)

photos = UploadSet('photos', IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app, photos)

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])

        # Creating Amazon S3 Client
        s3 = boto3.resource("s3")

        # Stroing object in bucket
        s3.Object("bucketaksthree", filename).put(Body=open("static/img/" + filename, "rb"))



        img_src_str = "static/img/" + filename

        # Creating boto3 client
        rekognition = boto3.client("rekognition", "us-east-1")

        collection_name = "collectionOfFaces"
        bucket_name = "bucketaksthree"
        photo_to_be_uploaded = filename

        response = rekognition.search_faces_by_image(
            CollectionId=collection_name,
            FaceMatchThreshold=75,
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': photo_to_be_uploaded,
                },
            },
            MaxFaces=5,
        )
        client = boto3.client('s3')

        if (response['FaceMatches']):
            for elements in response['FaceMatches']:
                str1 = "<p>Criminal Found!</p>"
                str5 = "<p>Similarity: " + str(elements['Similarity']) + "</p>"
                str2 = "<p>Face Id: " + elements['Face']['FaceId'] + "</p>"
                str3 = "<p>Image Id: " + elements['Face']['ImageId'] + "</p>"
                str4 = "<p>Image found: Faces/" + elements['Face']['ExternalImageId'] + ".jpg matched." + "</p>"
                str_src = elements['Face']['ExternalImageId'] + ".jpg"
                str_name = "static/img/res/" + str_src
                s3.Bucket('bucketakstwo').download_file(str_src, str_name)
                str_table = "<table><tr><td>Image Uploaded</td><td>Record Found</td></tr><tr><td><img src=\""+img_src_str+"\" width=\"200\" height=\"200\"></td><td><img src=\""+str_name+"\" width=\"200\" height=\"200\"></td></tr></table>"

                # Printing the buckets
                for bucket in s3.buckets.all():
                    print(bucket.objects.all())
                    if (bucket.name == "bucketakstwo"):
                        for key in bucket.objects.all():
                            mystr = elements['Face']['ExternalImageId'] + ".jpg"
                            if(key.key == mystr):
                                k = client.get_object(Bucket="bucketakstwo", Key=key.key)
                                str_metadata = "<p>Details:</p><p>Name: " + k['Metadata']['criminal'] + "</p><p>Ongoing Cases: " + k['Metadata']['cases'] + "</p>"
                                print(str_metadata)
            return str1 + str5 + str2 + str3 + str4 + str_table + str_metadata
        else:
            return("<h1>No match found.</h1>")
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)