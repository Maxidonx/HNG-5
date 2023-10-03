import boto3
from botocore.exceptions import WaiterError
from django.conf import settings
import time
from rest_framework.response import Response
from celery import shared_task

# Initialize the Transcribe client
transcribe = boto3.client('transcribe', region_name=settings.AWS_S3_REGION_NAME)


@shared_task(bind=True)
def start_transcription(self, input_uri):
    try:
        job_name = f'TranscriptionJob_{int(time.time())}'
        
        # Ensure that input_uri is a string before splitting
        if isinstance(input_uri, str):
            # Extract the input video file name from the input_uri
            input_video_name = input_uri.split('/')[-1]
            print(f"INput URI: {input_uri}")
            print(f"INput video name: {input_video_name}")
            # Use the input video name as the base name for the output key
            output_key = f'transcripts/{input_video_name}.json'


        # Start transcription job
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': input_uri},
            MediaFormat='mp4',
            LanguageCode='en-US',  # Change the language code as needed
            OutputBucketName=settings.AWS_STORAGE_BUCKET_NAME,
            OutputKey=output_key,  # Adjust the output key as needed
        )

        # Return a response indicating that the job has started
        return {'message': 'Transcription job started', 'job_name': job_name}

    except WaiterError as e:
        # Handle any WaiterError exceptions if needed
        return {'message': f'Error: {str(e)}', 'status': 500}