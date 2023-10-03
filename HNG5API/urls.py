from django.urls import path
from . import views

urlpatterns = [
    
    path('api/upload_video/', views.upload_video, name='upload_video'),
    path('api/video/play/<int:video_id>/', views.video_playback, name='video_playback'),
    path('api/videos/', views.ListVideosView.as_view(), name='list_videos'),
    path('api/get_transcription/<int:video_id>/', views.get_transcription, name='get_transcription'),
    
]