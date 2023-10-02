from django.db import models
from compat import StringIO

# Create your models here.

class TimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at', '-updated_at']

class Recordings(TimeStamp):
    title = models.CharField(max_length=300, blank=True, null=True)
    name = models.CharField(max_length=270, blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    video = models.FileField(("Video File"), upload_to='videos/', null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    
    
    
    def __str__(self):
        return self.name 
    
    
# class VideoRecordings(TimeStamp):
#     recording = models.ForeignKey(Recordings, on_delete=models.CASCADE)
#     video = models.FileField(("Video File"), upload_to='videos/', null=True)
#     transcript = models.TextField(blank=True, null=True)
    
    
#     def __str__(self):
#         return self.recordings.name + ": " + str(self.video)