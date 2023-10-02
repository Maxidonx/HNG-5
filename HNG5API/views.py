from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
from moviepy.editor import VideoFileClip, concatenate_videoclips
import tempfile
from django.shortcuts import get_object_or_404, render
from rest_framework.response import Response
from rest_api_payload import error_response, success_response
from rest_framework import generics
from django.http import HttpRequest, HttpResponse
from rest_framework import status
import uuid
from .serializers import CreateRecordingSerializer, GetRecordingSerializer
from .models import Recordings
from rest_framework.views import APIView
from django.http import StreamingHttpResponse
from rest_framework.renderers import JSONRenderer
from django.conf import settings
import os
from django.core.files import File
import io
from django.core.files.base import ContentFile


# Create your views here.
BASE_URL = settings.BASE_DIR


class CreateRecordingView(generics.CreateAPIView):
    serializer_class = CreateRecordingSerializer
    queryset = Recordings.objects.all()

    def get_serializer_context(self):
        return {'request': self.request}

    def post(self, request: HttpRequest):
        serializer = CreateRecordingSerializer(data=request.data)
        name = serializer.initial_data.get("name")
        if serializer.is_valid():
            serializer.save()

            payload = success_response(
                status="success",
                message=f"Recording(s) saved successfully!",
                data=serializer.data
            )
            return Response(data=payload, status=status.HTTP_201_CREATED)
        else:
            payload = error_response(
                status="Failed something went wrong",
                message=serializer.errors
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)


class AllRecordingsView(generics.ListAPIView):
    serializer_class = GetRecordingSerializer
    queryset = Recordings.objects.all()

    def get(self, request: HttpRequest):

        recordings = self.get_queryset()
        serializers = self.serializer_class(recordings, many=True)
        payload = success_response(
            status="success",
            message=f"All recordings fetched successfully!",
            data=serializers.data
        )
        return Response(data=payload, status=status.HTTP_200_OK)


class GetDataView(APIView):
    def put(self, request, id):
        data = request.data.get("data")
        print(request.FILES, "request files")
        print(request.data, "request data")
        recording_id = id
        if recording_id:
            try:
                video = Recordings.objects.get(pk=recording_id)
            except Recordings.DoesNotExist:
                return Response({'error': 'No video found'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the request contains a body with data
            if not data:
                return Response({'error': 'No video data provided'}, status=status.HTTP_400_BAD_REQUEST)

            new_video_data = data

            if video.video:
                # Read the existing video data
                existing_video_data = video.video.read()

                # Create temporary files to save the video data
                with tempfile.NamedTemporaryFile(delete=False) as existing_tempfile:
                    existing_tempfile.write(existing_video_data)
                    existing_tempfile_path = existing_tempfile.name

                with tempfile.NamedTemporaryFile(delete=False) as new_tempfile:
                    new_tempfile.write(new_video_data)
                    new_tempfile_path = new_tempfile.name

                # Create VideoFileClip objects from the temporary files
                existing_clip = VideoFileClip(existing_tempfile_path)
                new_clip = VideoFileClip(new_tempfile_path)

                # Concatenate the video clips
                final_clip = concatenate_videoclips([existing_clip, new_clip])

                # Save the concatenated video data to the video model
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as final_tempfile:
                    final_clip.write_videofile(
                        final_tempfile.name, codec='libx264')
                    final_tempfile_path = final_tempfile.name

                video.video.save(f'video_{video.id}.mp4', ContentFile(
                    open(final_tempfile_path, 'rb').read()))

                # Clean up temporary files
                os.remove(existing_tempfile_path)
                os.remove(new_tempfile_path)
                os.remove(final_tempfile_path)

                return Response({'message': 'Video appended and joined successfully'}, status=status.HTTP_200_OK)
            else:
                # If there's no existing video, use the new video data directly
                video.video.save(
                    f'video_{video.id}.mp4', new_video_data)
                return Response({'message': 'Video added successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No ID'}, status=status.HTTP_200_OK)
    # def get(self, request):
    #     data = request.data.get("data")
    #     recording_id = request.data.get("recording_id")

    #     if recording_id:
    #         try:
    #             recording = Recordings.objects.get(id=recording_id)
    #             folder_name = recording.name

    #             folder_path = os.path.join(settings.BASE_DIR, 'media', folder_name)
    #             os.makedirs(folder_path, exist_ok=True)

    #             base_filename = 'received_data'
    #             ext = '.mp4'
    #             i = 0
    #             while True:
    #                 filename = f'{base_filename}{i}{ext}'
    #                 file_path = os.path.join(folder_path, filename)
    #                 if not os.path.exists(file_path):
    #                     break
    #                 i += 1

    #             with open(file_path, 'wb') as file:
    #                 for chunk in data.chunks():
    #                     file.write(chunk)

    #             # Save the received MP4 data in a file within the folder
    #             # file_path = os.path.join(folder_path, 'received_data.mp4')
    #             # with open(file_path, 'wb') as file:
    #             #     file.write(data)

    #             return Response({'message': 'Data saved successfully'}, status=status.HTTP_201_CREATED)
    #         except Recordings.DoesNotExist:
    #             return Response({'error': 'Recording not found'}, status=status.HTTP_404_NOT_FOUND)
    #     else:
    #         return Response({'error': 'Recording ID not provided'}, status=status.HTTP_400_BAD_REQUEST)


class MergeRecordingView(APIView):

    def put(self, request):
        recording_id = request.data.get("recording_id")

        if recording_id:
            try:
                recording = Recordings.objects.get(id=recording_id)
                folder_name = recording.name

                folder_path = os.path.join(
                    settings.BASE_DIR, 'media', folder_name)

                video_files = [f for f in os.listdir(
                    folder_path) if f.endswith('.mp4')]

                if len(video_files) < 2:
                    return Response({'error': 'Not enough video files to merge'}, status=status.HTTP_400_BAD_REQUEST)

                video_files.sort()

                file_paths = [os.path.join(folder_path, video_file)
                              for video_file in video_files]

                video_clips = [VideoFileClip(file_path)
                               for file_path in file_paths]

                final_clip = video_clips[0]
                for clip in video_clips[1:]:
                    final_clip = final_clip.set_duration(
                        final_clip.duration + clip.duration)
                    final_clip = final_clip.set_end(
                        final_clip.end + clip.duration)

                final_video_path = os.path.join(folder_path, 'final_video.mp4')
                final_clip.write_videofile(
                    final_video_path, codec='libx264', temp_audiofile='temp-audio.m4a', remove_temp=True)

                for file_path in file_paths:
                    os.remove(file_path)

                return Response({'message': 'Video files merged successfully'}, status=status.HTTP_200_OK)
            except Recordings.DoesNotExist:
                return Response({'error': 'Recording not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Recording ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

# class VideoRecordingsView(generics.ListAPIView):
#     serializer_class = GetRecordingVideoSerializer

#     def get(self, request:HttpRequest, id:int):
#         try:
#             recording = Recordings.objects.get(id=id)
#             videos = VideoRecordings.objects.filter(recording=recording)
#             serializers = GetRecordingVideoSerializer(instance={'recording': recording, 'videos': videos}, many=False)
#             payload = success_response(
#                 status="success",
#                 message=f"Videos for recording {recording.name} fetched successfully!",
#                 data=serializers.data
#             )
#             return Response(data=payload, status=status.HTTP_200_OK)
#         except Recordings.DoesNotExist:
#             payload = error_response(
#                 status="Failed, something went wrong",
#                 message=f"Recording does not exist"
#             )
#             return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

# class SingleVideoView(generics.ListAPIView):
#     serializer_class = VideoSerializers

#     def get(self, request:HttpRequest, id:int):
#         try:
#             video = VideoRecordings.objects.get(id=id)
#             serializers = VideoSerializers(video, many=False)
#             payload = success_response(
#                 status="success",
#                 message=f"Video fetched successfully!",
#                 data=serializers.data
#             )
#             return Response(data=payload, status=status.HTTP_200_OK)
#         except VideoRecordings.DoesNotExist:
#             payload = error_response(
#                 status="Failed, something went wrong",
#                 message=f"Video does not exist"
#             )
#             return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)