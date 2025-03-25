import cv2
import mediapipe as mp
import time
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth


client_id = "c7f58264a04445819d84d74b17de3391"
client_secret = "2018a8dfb08249e0ad3b6013c084097a"
redirect_uri = 'http://127.0.0.1:9090/callback'
scope = "user-read-playback-state,user-modify-playback-state"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
  client_id=client_id,
  client_secret=client_secret,
  redirect_uri=redirect_uri,
  scope=scope
))


mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


prev_gesture = None
positions_history = {}
start_time = time.time()
cooldown = 3.0 # To prevent multiple API calls in a short time


# Play and pause gesture
def play_pause(hand_landmarks):
  '''
  This function detects the play and pause gesture using hand landmarks.
  Play gesture: open hand
  Pause gesture: closed hand with fingers touching
  '''
  thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
  index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
  middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
  ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
  pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
  index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

  hand_closed = (
    abs(index_tip.x - middle_tip.x) < 0.05 and
    abs(middle_tip.x - ring_tip.x) < 0.05 and
    abs(ring_tip.x - pinky_tip.x) < 0.05
  )
  hand_open = (
    abs(index_tip.x - thumb_tip.x) > 0.2 and
    abs(middle_tip.x - thumb_tip.x) > 0.2 and
    abs(ring_tip.x - thumb_tip.x) > 0.2 and
    abs(pinky_tip.x - thumb_tip.x) > 0.2
  )

  return hand_closed and not hand_open

# next song gesture
def next_prev_song(hand_landmarks, positions_history):
  pass

def increase_decrease_volume(Hand_landmarks, prev_position=None):
  pass

def control_spotify(gesture):
  global prev_gesture
  global start_time
  current_time = time.time()
  if current_time - start_time < cooldown:
    return
  if gesture != prev_gesture:
    try:
      if gesture:
        sp.pause_playback()
        print("spotify paused")
      else:
        sp.start_playback()
        print("spotify started")
      prev_gesture = gesture
      start_time = current_time
    except Exception as e:
      print(f"API Error: {e}")


cap = cv2.VideoCapture(1)

with mp_hands.Hands(
  min_detection_confidence=0.5,
  min_tracking_confidence=0.5
) as hands:

  while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
      continue

    start = time.time()
    frame_h, frame_w, frame_c = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # improve performance
    frame_rgb.flags.writeable = False
    results = hands.process(frame_rgb)
    # draw hand landmarks
    frame_rgb.flags.writeable = True
    frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    current_time = time.time()
    if results.multi_hand_landmarks:
      for hand_landmarks in results.multi_hand_landmarks:
        mp_drawing.draw_landmarks(
          frame_rgb,
          hand_landmarks,
          mp_hands.HAND_CONNECTIONS
        )

    # show fps
    end = time.time()
    fps = 1 / (end - start)
    cv2.putText(frame_rgb, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('Hand Tracking', frame_rgb)
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
cap.release()
cv2.destroyAllWindows()


