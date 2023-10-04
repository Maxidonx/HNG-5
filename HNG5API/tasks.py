#import whisper
from celery import shared_task
from django.conf import settings
import os
from django.core.files.storage import default_storage
from pydub import AudioSegment
from .models import Recordings
from moviepy.editor import *
from .serializers import TranscriptionSerializer
from asgiref.sync import sync_to_async

#model = whisper.load_model("base")


# class Transcribe:

#     @staticmethod
#     def get_audio_file(recording):
#         path = default_storage.path(recording.video.name)
#         if (recording.file.name.endswith('.mp4')):
#             audio = AudioSegment.from_file(path, format='mp4')
#             dir_path = os.path.dirname(path)
#             new_file_name = recording.video.name.replace('.mp4', '.mp3')
#             new_file_path = os.path.join(dir_path, new_file_name)
#             audio.export(new_file_path, format='mp3')
#         return path

#     @sync_to_async
#     def transcribe_file(self, recording_id):
#         recording = Recordings.objects.filter(id=recording_id).first()
#         if (not recording):
#             return None
#         audio_file = Transcribe.get_audio_file(recording)
#         transcription = model.transcribe(audio_file)
#         recording.transcript = transcription['text'].strip()
#         recording.is_transcript_completed = True
#         recording.save()
#         data = TranscriptionSerializer(recording).data
#         return data


# @shared_task
# def transcribe_video(recording_id):
#     return Transcribe().transcribe_file(recording_id)


@shared_task
def merge_recording(recording_id):
    if recording_id:
        try:
            recording = Recordings.objects.get(id=recording_id)
            folder_name = recording.name

            folder_path = os.path.join(
                settings.BASE_DIR, 'media', folder_name)

            video_files = [f for f in os.listdir(
                folder_path) if f.endswith('.mp4')]

            if len(video_files) < 2:
                return 'Not enough video files to merge'

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

            # transcribe_video(recording_id)

            return 'Video files merged successfully'
        except Recordings.DoesNotExist:
            return 'Recording not found'
    else:
        return 'Recording ID not provided'