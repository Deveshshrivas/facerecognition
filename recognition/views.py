import cv2
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Frame

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