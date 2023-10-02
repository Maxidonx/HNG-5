from rest_framework import serializers
from .models import *
import uuid
from django.core.validators import FileExtensionValidator


BASE_URL = 'https://recorder-api.onrender.com'

# class VideoSerializers(serializers.ModelSerializer):
#     full_video_url = serializers.SerializerMethodField()


#     class Meta:
#         model = VideoRecordings
#         fields = '__all__'

#     def get_full_video_url(self, obj):
#         return BASE_URL + obj.video.url

# class CreateRecordingSerializer(serializers.ModelSerializer):
#     videos = VideoSerializers(many=True, read_only=True)
#     name = serializers.CharField(read_only=True)
#     uploaded_videos = serializers.ListField(
#         child = serializers.FileField(max_length = 1000000, allow_empty_file = False, use_url = False),
#         write_only = True
#     )
#     class Meta:
#         model = Recordings
#         fields = ['id', 'name', 'videos', 'uploaded_videos']

#     def validate(self, attrs):
#         return attrs

# def create(self, validated_data):
#     uploaded_data = validated_data.pop('uploaded_videos')
#     recordings = Recordings.objects.create(name=uuid.uuid4(), **validated_data)
#     for i in uploaded_data:
#         VideoRecordings.objects.create(recording = recordings, video = i)
#     return recordings

class CreateRecordingSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = Recordings
        fields = ['id', 'name']

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        recordings = Recordings.objects.create(
            name=uuid.uuid4(), **validated_data)
        return recordings


class GetRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recordings
        fields = ['id', 'name', 'title', 'transcript', 'video',
                  'is_completed', 'is_transcript_completed', 'created_at']


class GetRecordingVideoSerializer(serializers.Serializer):
    recording = GetRecordingSerializer()
    # videos = VideoSerializers(many=True)


class TranscriptionSerializer(serializers.ModelSerializer):
    video = serializers.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'mp4'])])

    class Meta:
        model = Recordings
        fields = ('id', 'title', 'transcript', 'video')
