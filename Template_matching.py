import cv2
import numpy as np
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from twilio.rest import Client
from datetime import datetime, timedelta
from playsound import playsound
import threading

# alert sound function


def play_alert_sound():
    playsound(r"C:\Users\Vachu jothi\OneDrive\Desktop\sound\emergency-alarm-with-reverb-29431.mp3")


def crime_detection(camera_feed, reference_images, reference_videos, credentials_path, twilio_account_sid,
                    twilio_auth_token, recipient_number, image_threshold=0.7, video_threshold=0.5):



    reference_images_list = [cv2.imread(image_path) for image_path in reference_images]



    reference_videos_list = [cv2.VideoCapture(video_path) for video_path in reference_videos]



    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    drive_service = build('drive', 'v3', credentials=credentials)

    # Initialize the Twilio client

    twilio_client = Client(twilio_account_sid, twilio_auth_token)

    # Twilio configurations

    sender_number = 'whatsapp:+14155238886'  # Twilio sandbox number
    message_body = 'Crime detected! Crime video and message sent to Varshini.'

    # Open the camera

    cap = cv2.VideoCapture(camera_feed)

    # Initialize variables for recording

    recording = False
    recorded_frames = []
    crime_detected = False
    start_recording_time = None

    while True:
        # Read frame from the camera

        ret, frame = cap.read()

        # Break the loop if there's an issue reading the frame

        if not ret:
            print("Error reading frame from the camera")
            break

        # Convert the frame to grayscale

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Display the camera feed

        cv2.imshow('Crime Detection', frame)
        cv2.waitKey(1)  # Add waitKey to display the frame

        # Iterate over each reference image

        for reference_image in reference_images_list:

            # Use template matching to find the reference image in the frame

            result = cv2.matchTemplate(gray_frame, cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY),
                                       cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= image_threshold)

            # If a match is found, set crime_detected flag

            if len(locations[0]) > 0:
                crime_detected = True
                break

        # Iterate over each reference video if crime is not detected

        if not crime_detected:
            for reference_video, reference_video_path in zip(reference_videos_list, reference_videos):
                # Read frame from the reference video

                ret_ref, frame_ref = reference_video.read()

                # Break the loop if there's an issue reading the reference frame

                if not ret_ref:
                    print(f"Error reading frame from reference video: {reference_video_path}")
                    continue

                # Convert the reference frame to grayscale

                gray_frame_ref = cv2.cvtColor(frame_ref, cv2.COLOR_BGR2GRAY)

                # Resize the reference frame to match the camera frame size

                gray_frame_ref = cv2.resize(gray_frame_ref, (frame.shape[1], frame.shape[0]))

                # Use template matching to find the reference frame in the camera frame

                result_ref = cv2.matchTemplate(gray_frame, gray_frame_ref, cv2.TM_CCOEFF_NORMED)
                locations_ref = np.where(result_ref >= video_threshold)

                # If a match is found, set crime_detected flag

                if len(locations_ref[0]) > 0:
                    crime_detected = True
                    break

        # If crime is detected, start recording

        if crime_detected and not recording:
            recording = True
            start_recording_time = datetime.now()
            print("Crime detected! Recording started.")

            # alert sound
            alert_sound = threading.Thread(target=play_alert_sound)
            alert_sound.start()

        # If recording, save frames

        if recording:
            recorded_frames.append(frame)

        # If recording time exceeds 5 seconds, stop recording

        if recording and (datetime.now() - start_recording_time) >= timedelta(seconds=10):

            # Save recorded frames to video file

            out = cv2.VideoWriter('recorded_video.avi', cv2.VideoWriter_fourcc(*'XVID'), 30,
                                  (frame.shape[1], frame.shape[0]))
            for frame in recorded_frames:
                out.write(frame)
            out.release()

            # Upload video to Google Drive

            file_metadata = {'name': 'recorded_video.avi'}
            media = MediaFileUpload('recorded_video.avi', mimetype='video/avi')
            uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = uploaded_file.get('id')

            # Set permissions for the uploaded video

            drive_service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'},
                fields='id'
            ).execute()

            # Generate public URL for the uploaded video file

            file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

            # Send WhatsApp message with Google Drive public URL

            message_body = f'Crime detected! please confirm if it is a crime by checking the below video (location- v laptop cam): {file_url}'
            twilio_client.messages.create(from_=sender_number, body=message_body, to=recipient_number)
            print("WhatsApp message sent to varshini with video URL.")

            # Reset variables

            recording = False
            recorded_frames = []
            crime_detected = False

        # Break the loop if 'q' is pressed

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and reference videos, and close the windows

    cap.release()
    for reference_video in reference_videos_list:
        reference_video.release()
    cv2.destroyAllWindows()


# Specify the camera feed (usually 0 for the default camera)

camera_feed = 0

# Specify the paths to the reference crime images

reference_images = [
    r"C:\images'\image.jpg",
    r"C:\Users\Vachu jothi\Downloads\resized image\image (4).jpg"


    # Add more paths as needed
]


# Specify the paths to the reference crime videos

reference_videos = [
    r"C:\images'\crime video.mp4"
    # Add more paths as needed
]


# Specify the path to the Google Drive credentials JSON file

credentials_path = r'C:\Users\Vachu jothi\Downloads\android-eye-crime-detectiom-96e66e0abcd6.json'


# Specify Twilio credentials and recipient number

twilio_account_sid = 'ACa53d727c38e880350478b69c30644aa2'
twilio_auth_token = '9631f1a61e3ad028367f6814f4394860 '
recipient_number = 'whatsapp:+919363572196'  # Replace with the actual recipient's number


# Set the matching thresholds (adjust as needed)

image_matching_threshold = 0.7
video_matching_threshold = 0.5

# Run the crime detection function

crime_detection(camera_feed, reference_images, reference_videos, credentials_path, twilio_account_sid,
                twilio_auth_token, recipient_number, image_matching_threshold, video_matching_threshold)
