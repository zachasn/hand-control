# Spotify Hand Gesture Control

A computer vision application that allows you to control Spotify playback using hand gestures captured through your webcam.

## Features

- **Play/Pause**: Open palm to play, closed fist to pause
- **Next/Previous Track**: Swipe right for next track, swipe left for previous track
- **Volume Control**: Adjust the distance between index finger and thumb while keeping other fingers closed

## Requirements

- Python 3.6+
- OpenCV
- MediaPipe
- Spotipy
- A Spotify Premium account

## Setup

1. Clone this repository
2. Install required packages:
   ```
   pip install opencv-python mediapipe spotipy
   ```
3. Set up Spotify API credentials:
   - Create an application on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Set the redirect URI to `http://127.0.0.1:9090/callback`
   - Replace the client_id and client_secret in the code with your own

## Usage

1. Run the application:
   ```
   python handControl.py
   ```
2. Position your hand in front of the webcam
3. Use the following gestures:
   - Open palm: Play music
   - Closed fist: Pause music
   - Swipe right: Next track
   - Swipe left: Previous track
   - Pinch gesture (index finger and thumb): Control volume

## Future Improvements

I plan to reimplement this project in C++ to improve latency and overall performance. The current Python implementation works well, but a C++ version would provide better real-time responsiveness.
