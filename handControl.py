import cv2
import mediapipe as mp
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth




# Spotify API credentials
client_id = "c7f58264a04445819d84d74b17de3391"
client_secret = "2018a8dfb08249e0ad3b6013c084097a"
redirect_uri = "http://127.0.0.1:9090/callback"
scope = "user-read-playback-state,user-modify-playback-state"

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope
))

# MediaPipe initialization
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands



spotify_state = {"is_playing": False, "last_check": 0}  # Track Spotify state

# Still keep a small cooldown to prevent accidental double detection
min_cooldown = 0.2  # Minimal cooldown in seconds

def get_spotify_state():
  global spotify_state
  current_time = time.time()

  # Only check state every 2 seconds to avoid excessive API calls
  if current_time - spotify_state["last_check"] > 2:
    try:
      playback_state = sp.current_playback()
      if playback_state:
        spotify_state["is_playing"] = playback_state["is_playing"]
      else:
        spotify_state["is_playing"] = False
        spotify_state["last_check"] = current_time
    except spotipy.exceptions.SpotifyException as e:
      print(f"Error fetching Spotify state: {e}")
  return spotify_state["is_playing"]

def play_pause_gesture(hand_landmarks, last_gesture_time=None):
  """Plays or pauses the current song based on the detected gesture.
  If the hand is open with fingers extended, the song is played.
  if the hand is a fist, the song is paused.
  """
  current_time = time.time()
  if last_gesture_time and current_time - last_gesture_time < min_cooldown:
    return last_gesture_time

  thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
  index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
  middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
  ring_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
  pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

  thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]
  index_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
  middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
  ring_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP]
  pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]

  fingers_up = [
    thumb_tip.y < thumb_mcp.y, # thumb is up
    index_finger_tip.y < index_finger_mcp.y, # index finger is up
    middle_finger_tip.y < middle_finger_mcp.y, # middle finger is up
    ring_finger_tip.y < ring_finger_mcp.y, # ring finger is up
    pinky_tip.y < pinky_mcp.y # pinky is up
  ]

  is_palm = sum(fingers_up) >= 4 # if most fingers are up, it's a palm
  is_fist = sum(fingers_up) <= 1 # if most fingers are down, it's a fist

  try:
    if is_palm and not get_spotify_state():
      sp.start_playback()
      return current_time
    elif is_fist and get_spotify_state():
      sp.pause_playback()
      return current_time
  except spotipy.exceptions.SpotifyException as e:
    print(f"eror in play/pause gesture: {e}")
  return last_gesture_time

def next_prev_gesture(hand_landmarks, frame_w, last_gesture_time=None):
  """
  Goes to the next or previous song based on the detected gesture.
  Swipe right = next song, swipe left = previous song
  Returns: last_gesture_time if gesture was detected and executed
  """
  current_time = time.time()
  if last_gesture_time and current_time - last_gesture_time < min_cooldown:
    return last_gesture_time

  index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
  wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

  index_finger_x = int(index_finger_tip.x * frame_w)
  wrist_x = int(wrist.x * frame_w)

  change_in_position = index_finger_x - wrist_x

  try:
    if change_in_position > 100:
      sp.next_track()
      return current_time
    elif change_in_position < -100:
      sp.previous_track()
      return current_time
  except spotipy.exceptions.SpotifyException as e:
    print(f"Error in next/prev gesture: {e}")
  return last_gesture_time

def volume_gesture(curr_distance, min_distance=20, max_distance=350, hand_landmarks=None, last_volume=None):
  """
  Increases or decreases volumne based on the distance between index finger and thumb.
  Closer = lower volume, further = higher volume
  """
  if hand_landmarks is None:
    return last_volume, False

  middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
  ring_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
  pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

  middle_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
  ring_finger_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP]
  pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]

  fingers_closed = all([
    middle_finger_tip.y > middle_finger_mcp.y, # middle finger is down
    ring_finger_tip.y > ring_finger_mcp.y, # ring finger is down
    pinky_tip.y > pinky_mcp.y # pinky is down
  ])

  draw_line = min_distance <= curr_distance <= max_distance and fingers_closed

  if draw_line:
    normalized_distance = (curr_distance - min_distance) / (max_distance - min_distance)
    current_volume = int((normalized_distance * 1.5)*100)
    if last_volume is None or abs(current_volume - last_volume) >= 2:
      try:
        sp.volume(current_volume)
        last_volume = current_volume
      except spotipy.exceptions.SpotifyException as e:
        print(f"Error in volume gesture: {e}")
  return last_volume, draw_line




def main():
  rescaled_index_finger_tip = (0,0)
  rescaled_thumb_tip = (0,0)
  distance = 0
  cap = cv2.VideoCapture(1)

  # to prevent making too many API calls
  last_volume = None
  last_gesture_time = None
  active_gesture = None

  with mp_hands.Hands(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
  ) as hands:

    while cap.isOpened():
      ret, frame = cap.read()
      frame = cv2.flip(frame, 1)
      start = time.time()
      frame_h, frame_w, _ = frame.shape
      # convert frame to RGB
      frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      frame.flags.writeable = False
      results = hands.process(frame)
      frame.flags.writeable = True
      frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

      if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
          index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
          thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

          rescaled_index_finger_tip = (int(index_finger_tip.x * frame_w), int(index_finger_tip.y * frame_h))
          rescaled_thumb_tip = (int(thumb_tip.x * frame_w), int(thumb_tip.y * frame_h))

          distance = ((rescaled_index_finger_tip[0] - rescaled_thumb_tip[0]) ** 2 + (rescaled_index_finger_tip[1] - rescaled_thumb_tip[1]) ** 2) ** 0.5

          mp_drawing.draw_landmarks(
            frame,hand_landmarks,mp_hands.HAND_CONNECTIONS)

          last_volume, draw_line = volume_gesture(distance, hand_landmarks=hand_landmarks, last_volume=last_volume)

          if draw_line:
            if active_gesture != "volume":
              active_gesture = "volume"
            cv2.line(frame, rescaled_index_finger_tip, rescaled_thumb_tip, (255, 0, 0), 2)
            continue

          new_gesture_time = play_pause_gesture(hand_landmarks, last_gesture_time)
          if new_gesture_time != last_gesture_time:
            active_gesture = "play_pause"
            last_gesture_time = new_gesture_time
            continue;
          new_gesture_time = next_prev_gesture(hand_landmarks, frame_w, last_gesture_time)
          if new_gesture_time != last_gesture_time:
            active_gesture = "next_prev"
            last_gesture_time = new_gesture_time
            continue;

          if not draw_line and new_gesture_time == last_gesture_time:
            active_gesture = None


      end = time.time()
      fps = 1 / (end - start)
      cv2.putText(frame, f"FPS: {int(fps)}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
      cv2.imshow("frame", frame)
      if cv2.waitKey(1) & 0xFF == 27:
        break

  cap.release()
  cv2.destroyAllWindows()


if __name__ == "__main__":
  main()





