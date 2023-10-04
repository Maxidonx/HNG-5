# VIDEO API
The video API is a Django application that allows you to create, save, and retrieve video files received from any screen recording chrome extension. This application creates recordings, merge recording chunks, transcribe the merged video, and get the compiled video for a specific video ID.

## Gettin Started
**Clone this repository**
```bash
https://github.com/Maxidonx/HNG-5.git
```
**Run the Folloin commands**

- virtual environment
```bash
python -m venv venv
venv\Scripts\activate #or windows
source/venv/activate #linux
```
- download Django
```bash 
pip install django
```

- migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
- runserver
```bash
python manage.py runserver
```

# Endpoints

## Create Video
**Method:** (POST)
**Description:** Create a new video record.
**Endpoint:** https://task-5-62nf.onrender.com/api/create/
**Response:** JSON containing the created video ID.
**Example Request:**
```bash
curl -X POST https://recorder-api.onrender.com/api/create/
```
**Example Response:**
```bash
{
    "id": 14
}
Append Video Chunk (POST)
Append a video chunk to an existing video.
Method: PUT
Endpoint: https://task-5-62nf.onrender.com/api/save-data/<video_id>/
Request Body: Video chunk data in binary format.
Response: JSON with a success message.
For the first chunk:

{
    "message": "Recording(s) saved successfully!"
}
For subsequent chunks:

{
    "message": "Recording(s) saved successfully!"
}
Merge Video Chunk (POST)
Append a video chunk to an existing video.
Method: POST
Endpoint: https://recorder-api.onrender.com/api/merge-data/<video_id>/
Response: JSON with a success message.
For the first chunk:

{
    "message": "Video files is currently being merged."
}
Get Video (GET)
Retrieve the compiled video for a specific video ID.
Method: GET
Endpoint: https://recorder-api.onrender.com/api/<video_id>/
Response: JSON with a data message..
Example Request:

curl https://recorder-api.onrender.com/api/53/
Example Response

{
   "status": "success",
    "message": "Video fetched successfully!",
    "data": {
        "id": 53,
        "name": "2bbb3478-12b9-428a-9b63-b5d13f7a0a43",
        "title": null,
        "transcript": null,
        "video": "/media/videos/video_53.webm",
        "is_completed": false,
        "is_transcript_completed": false,
        "created_at": "2023-10-01T19:50:15.024237Z"
    }
}
```
## Usage
- Create a new video record using the "Create Video" endpoint. Note the returned video_id.

- Append video chunks to the video using the "Append Video Chunk" endpoint. Ensure you include the video_id in the URL.

- Merge the video chunks together with the Merge video endpoint which will operates in the background, Ensure you include the video_id of the video to be merged in the url.

- Once all video chunks are appended, you can retrieve the compiled video using the "Get Video" endpoint with the video_id.

- Deployment
The API has been deployed and can be accessed at the following base URL:

**Base URL: https://task-5-62nf.onrender.com**
