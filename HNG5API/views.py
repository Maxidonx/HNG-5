from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, FileResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
from .models import Video
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
import boto3
from botocore.exceptions import NoCredentialsError, WaiterError, ClientError
import time
from .tasks import start_transcription
from .serializers import VideoSerializer
from rest_framework import generics
from django.http import StreamingHttpResponse
import uuid
import shutil
from django.urls import reverse

# Create your views here.
class ListVideosView(generics.ListAPIView):
    """
    View for retrieving a list of all videos.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

api_view(['GET'])
def video_playback(request, video_id):
    # Retrieve the video object from the database or return a 404 if it doesn't exist
    video = get_object_or_404(Video, id=video_id)

    # Get the S3 object key (file path) from the video object
    s3_object_key = video.file_path

    try:
        # Initialize AWS S3 client
        s3 = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Generate a pre-signed URL for the S3 object (video)
        # This URL will be temporary and provide secure access to the video
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_object_key},
            ExpiresIn=3600  # Set expiration time (e.g., 1 hour)
        )

         # Create a dictionary with video details and URLs
        video_data = {
            "upload_id": video.id,
            # "upload_status": video.status,
            "created_on": video.upload_timestamp,
            "filename": video.title,
            "url": presigned_url,
            "transcript_url": reverse('get_transcription', args=[video.id]),
        }

        # Return the video details as JSON response
        return JsonResponse(video_data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
def get_transcription(request, video_id):
    # Retrieve the video object from the database or return a 404 if it doesn't exist
    video = get_object_or_404(Video, id=video_id)

    # Get the S3 object key (file path) for the transcription
    transcription_key = f'transcripts/{video.file_path.split("/")[-1]}.json'

    try:
        s3 = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Check if the transcription file exists on S3
        try:
            head_object = s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=transcription_key)
        except ClientError as e:  # Use ClientError to catch AWS service-related exceptions
            if e.response['Error']['Code'] == '404':
                # Transcript not found, return a custom 404 response
                return Response({'message': 'No transcript available for this video.'}, status=status.HTTP_404_NOT_FOUND)
            else:
                # Handle other exceptions
                return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate a pre-signed URL for the S3 object (transcription file)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': transcription_key},
            ExpiresIn=3600  # Set expiration time (e.g., 1 hour)
        )

        return Response({'transcription_url': presigned_url}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# Define a temporary storage directory for video chunks
TEMP_CHUNKS_DIR = os.path.join(settings.MEDIA_ROOT, 'temp_chunks')

@api_view(['POST'])
@transaction.atomic
def upload_video(request):
    uploaded_chunk = request.FILES.get('chunk')
    video_id = request.data.get('video_id')  # Include a video ID to associate chunks
    is_last_chunk = request.data.get('is_last_chunk', '').lower() == 'true'  # Ensure is_last_chunk is a boolean

    if uploaded_chunk and video_id:
        try:
            # Ensure the directory for this video_id exists
            video_dir = os.path.join(TEMP_CHUNKS_DIR, video_id)
            os.makedirs(video_dir, exist_ok=True)

            # Determine the file path for this chunk based on the video_id
            chunk_file_path = os.path.join(video_dir, uploaded_chunk.name)

            # Save the received chunk to a temporary location or buffer
            with open(chunk_file_path, 'wb') as destination:
                for chunk in uploaded_chunk.chunks():
                    destination.write(chunk)

            if is_last_chunk:
                # Concatenate all chunks to create the complete video
                complete_video_path = os.path.join(video_dir, 'complete.mp4')
                concatenate_chunks(video_dir, complete_video_path)

                # Initialize AWS S3 client
                s3 = boto3.client('s3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )

                # Define the S3 bucket name
                bucket_name = settings.AWS_STORAGE_BUCKET_NAME

                uuid_str = uuid.uuid4().hex
                # Generate a unique S3 object key (file path)
                s3_object_key = f'media/{video_id}_{uuid_str}.mp4'

                # Upload the video to the S3 bucket with the generated key
                s3.upload_file(complete_video_path, bucket_name, s3_object_key)

                # Create a database record for the uploaded video with the S3 object key
                video = Video(title='Your Video Title', file_path=s3_object_key)
                video.save()

                # Call the transcription function with the S3 URI of the uploaded video
                input_uri = f's3://{bucket_name}/{s3_object_key}'
                start_transcription.delay(input_uri)

                # Clean up the temporary directory for this video
                shutil.rmtree(video_dir)

                return Response({'message': 'Video uploaded and transcription started.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Chunk uploaded successfully.'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        return Response({'message': 'Video upload failed.'}, status=status.HTTP_400_BAD_REQUEST)


def concatenate_chunks(temp_dir, complete_video_path):
    # Concatenate all chunks in the temporary directory into the complete video file
    with open(complete_video_path, 'wb') as output_file:
        for chunk_filename in sorted(os.listdir(temp_dir)):
            chunk_path = os.path.join(temp_dir, chunk_filename)
            with open(chunk_path, 'rb') as chunk_file:
                output_file.write(chunk_file.read())