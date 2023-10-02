from rest_framework.response import Response
from rest_api_payload import error_response, success_response
from rest_framework import generics
from django.http import HttpRequest
from rest_framework import status
from .serializers import CreateRecordingSerializer, GetRecordingSerializer
from .models import Recordings
from rest_framework.views import APIView
from django.conf import settings
import os
from .tasks import merge_recording


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
        recording_id = id

        if recording_id and data:
            try:
                recording = Recordings.objects.get(id=recording_id)
                folder_name = recording.name

                folder_path = os.path.join(
                    settings.BASE_DIR, 'media', folder_name)
                os.makedirs(folder_path, exist_ok=True)

                base_filename = 'received_data'
                ext = '.mp4'
                i = 0
                while True:
                    filename = f'{base_filename}{i}{ext}'
                    file_path = os.path.join(folder_path, filename)
                    if not os.path.exists(file_path):
                        break
                    i += 1

                with open(file_path, 'wb') as file:
                    for chunk in data.chunks():
                        file.write(chunk)

                # Save the received MP4 data in a file within the folder
                # file_path = os.path.join(folder_path, 'received_data.mp4')
                # with open(file_path, 'wb') as file:
                #     file.write(data)

                return Response({'message': 'Data saved successfully'}, status=status.HTTP_201_CREATED)
            except Recordings.DoesNotExist:
                return Response({'error': 'Recording not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Recording ID or Data not provided'}, status=status.HTTP_400_BAD_REQUEST)


class MergeRecordingView(generics.UpdateAPIView):
    serializer_class = GetRecordingSerializer

    def put(self, request, id):
        recording_id = id
        if recording_id:
            try:
                recording = Recordings.objects.get(id=recording_id)
                print(recording)
                merge_recording(recording_id)
                recording.is_completed = True
                recording.save()
                return Response({'message': 'Video files is currently being merged.'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({'error': 'Recording not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Recording ID not provided'}, status=status.HTTP_400_BAD_REQUEST)


class SingleVideoView(generics.ListAPIView):
    serializer_class = GetRecordingSerializer

    def get(self, request: HttpRequest, id: int):
        try:
            video = Recordings.objects.get(id=id)
            serializers = GetRecordingSerializer(video, many=False)
            payload = success_response(
                status="success",
                message=f"Video fetched successfully!",
                data=serializers.data
            )
            return Response(data=payload, status=status.HTTP_200_OK)
        except Recordings.DoesNotExist:
            payload = error_response(
                status="Failed, something went wrong",
                message=f"Video does not exist"
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)
