import cv2
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
#
import threading
import requests
from .models import Frame
from pymongo import MongoClient
import numpy as np
import face_recognition
from django.conf import settings


# Configure logging
logging.basicConfig(level=logging.DEBUG)

@csrf_exempt
@api_view(['POST'])
def upload_video(request):
    if 'video' not in request.FILES or 'userId' not in request.POST:
        print("Missing video file or userId")
        return JsonResponse({'error': 'Missing video file or userId'}, status=400)
    
    user_id = request.POST['userId']
    video = request.FILES['video']
    
    try:
        # Save the uploaded video to a temporary location
        video_path = default_storage.save('temp_video.mp4', ContentFile(video.read()))
        video_full_path = os.path.join(default_storage.location, video_path)
        logging.debug(f"Video saved to temporary location: {video_full_path}")
        print(f"Video saved to temporary location: {video_full_path}")
        
        # Open the video file using OpenCV
        cap = cv2.VideoCapture(video_full_path)
        frame_count = 0
        frames = []

        while cap.isOpened() and frame_count < 50:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert frame to binary data
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()
            
            # Append frame data to the frames array
            frames.append(frame_data)
            
            frame_count += 1
        
        cap.release()
        logging.debug(f"Extracted {frame_count} frames from the video")
        print(f"Extracted {frame_count} frames from the video")
        
        # Save frames to the database
        Frame.objects.create(user_id=user_id, frames=frames)
        logging.debug("Frames saved to the database")
        print("Frames saved to the database")
        
        # Clean up the temporary video file
        default_storage.delete(video_path)
        logging.debug("Temporary video file deleted")
        print("Temporary video file deleted")
        
        print("Sending response with status 201")
        return JsonResponse({'message': 'Video uploaded and frames extracted successfully', 'userId': user_id, 'frame_count': frame_count}, status=201)
    
    except Exception as e:
        logging.error(f"Error uploading video: {e}")
        print(f"Error uploading video: {e}")
        return JsonResponse({'message': 'Video upload failed.', 'error': str(e)}, status=500)

# call_external_api 
def call_external_api(image_path):
    try:
        external_api_url = settings.EXTERNAL_API_URL# Replace with actual API URL
        headers = {'Content-Type': 'application/json'}
        payload = {'image_path': image_path}  # Send the image path

        response = requests.post(external_api_url, headers=headers, data=payload)
        response_data = response.json()
        
        if response.status_code == 200:
            print(f"External API successfully processed the image: {response_data}")
        else:
            print(f"External API returned an error: {response_data}")
    except Exception as e:
        print(f"Error calling external API: {e}")



# another view to get images from the database
@csrf_exempt
@api_view(['POST'])
def upload_image(request):
    if 'image' not in request.FILES or 'userID' not in request.POST or 'imageID' not in request.POST:
        print("Missing image file, userID, or imageID")
        return JsonResponse({'error': 'Missing image file, userID, or imageID'}, status=400)
    
    user_id = request.POST['userID']
    image_id = request.POST['imageID']
    image = request.FILES['image']
    
    try:
        # Create a directory for temporary storage if it doesn't exist
        temp_dir = os.path.join(default_storage.location, 'temp_images')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Save the uploaded image to the temporary directory
        image_path = default_storage.save(os.path.join('temp_images', f'{image_id}.jpg'), ContentFile(image.read()))
        image_full_path = os.path.join(default_storage.location, image_path)
        logging.debug(f"Image saved to temporary location: {image_full_path}")
        print(f"Image saved to temporary location: {image_full_path}")
        
        # Process the image if needed
        # ...
        response = JsonResponse({'message': 'Image uploaded successfully'}, status=201) 
        # return JsonResponse({'message': 'Image uploaded successfully'}, status=201)

        threading.Thread(target=call_external_api, args=(image_full_path,)).start()
        return response
    except Exception as e:
        logging.error(f"Error uploading image: {e}")
        print(f"Error uploading image: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
def check_person_in_group(request):
    if 'group_image' not in request.FILES:
        print("Missing group_image")
        return JsonResponse({'error': 'Missing group_image'}, status=400)
    
    group_image = request.FILES['group_image']
    
    try:
        # Save the uploaded group image to a temporary location
        group_image_path = default_storage.save('temp_group_image.jpg', ContentFile(group_image.read()))
        group_image_full_path = os.path.join(default_storage.location, group_image_path)
        logging.debug(f"Group image saved to temporary location: {group_image_full_path}")
        print(f"Group image saved to temporary location: {group_image_full_path}")
        
        # Connect to MongoDB and retrieve all user IDs and their frames
        client = MongoClient('mongodb://localhost:27017/')
        db = client['your_database']
        collection = db['your_collection']
        
        documents = collection.find({})
        results = {}
        
        for document in documents:
            user_id = document['user_id']
            frames = document['frames']
            
            # Convert the binary data to images
            target_face_images = [binary_to_image(frame) for frame in frames]
            
            # Get face encodings for the target images
            target_face_encodings = [get_face_encodings(image) for image in target_face_images]
            target_face_encodings = [encoding for encoding in target_face_encodings if encoding is not None]
            
            if not target_face_encodings:
                continue
            
            # Average the target face encodings
            average_target_face_encoding = np.mean(target_face_encodings, axis=0)
            
            # Load the group image
            group_image = preprocess_image(group_image_full_path)
            
            # Find all the faces in the group image
            face_locations = face_recognition.face_locations(group_image)
            
            # Find all the face encodings in the group image
            group_face_encodings = face_recognition.face_encodings(group_image, face_locations)
            
            # Set a stricter threshold for face distance
            threshold = 0.4
            
            # Loop through each face found in the group image
            for face_encoding in group_face_encodings:
                # Calculate the distance between the average target face and the current face
                face_distance = face_recognition.face_distance([average_target_face_encoding], face_encoding)[0]
                
                # Check if the face distance is below the threshold
                if face_distance < threshold:
                    results[user_id] = 1  # Person found in the group image
                    break
            else:
                results[user_id] = 0  # Person not found in the group image
        
        # Delete the temporary group image file
        default_storage.delete(group_image_path)
        logging.debug("Temporary group image file deleted")
        print("Temporary group image file deleted")
        
        return JsonResponse({'message': 'Check completed successfully', 'results': results}, status=200)
    except Exception as e:
        logging.error(f"Error checking person in group: {e}")
        print(f"Error checking person in group: {e}")
        return JsonResponse({'error': str(e)}, status=500)