import pygame
import cv2
import mediapipe as mp
import threading
import time
import math

# Initialize Pygame
pygame.init()

# Screen dimensions (Increased for a larger view)
WIDTH, HEIGHT = 1200, 600
GAME_WIDTH = 700  # Increased width for gameplay
CAM_WIDTH = WIDTH - GAME_WIDTH  # Remaining space for camera feed
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Box Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Clock for FPS
clock = pygame.time.Clock()

# Mediapipe Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Webcam Feed
cap = cv2.VideoCapture(0)

# Set webcam resolution to match the new camera section
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

# Game variables
boxes = [{"x": GAME_WIDTH - 60, "y": HEIGHT - 60, "held": False, "color": RED},
         {"x": 60, "y": HEIGHT - 60, "held": False, "color": BLUE}]
hand_pos = (0, 0)  # Hand position
hand_closed = False  # Whether the hand is closed
running = True
camera_frame = None

# Function to process webcam feed
def process_webcam():
    global hand_pos, hand_closed, camera_frame

    while running:
        success, img = cap.read()
        if not success:
            break

        # Flip and process the frame
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                h, w, _ = img.shape
                # Get the position of the index finger tip (landmark 8)
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                hand_pos = (cx * GAME_WIDTH // w, cy * HEIGHT // h)  # Scale to game size

                # Calculate distance between thumb tip (4) and index finger tip (8)
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                thumb_x, thumb_y = thumb_tip.x * w, thumb_tip.y * h
                distance = math.hypot(thumb_x - index_tip.x * w, thumb_y - index_tip.y * h)

                # Determine if the hand is closed (distance threshold)
                hand_closed = distance < 50  # Slightly increased threshold for accuracy

                # Draw landmarks on the frame
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Resize camera frame to fit the updated section
        camera_frame = cv2.resize(img, (CAM_WIDTH, HEIGHT))

        # Add a delay to avoid high CPU usage
        time.sleep(0.01)

# Start webcam processing in a separate thread
threading.Thread(target=process_webcam, daemon=True).start()

# Function to detect if hand is over a box
def hand_over_box(hand_pos, box):
    hand_x, hand_y = hand_pos
    return box["x"] - 30 <= hand_x <= box["x"] + 30 and box["y"] - 30 <= hand_y <= box["y"] + 30

# Game loop
while running:
    screen.fill(WHITE)

    # Draw dividing line in the game section
    pygame.draw.line(screen, BLACK, (GAME_WIDTH, 0), (GAME_WIDTH, HEIGHT), 5)

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update boxes
    for box in boxes:
        if hand_over_box(hand_pos, box):
            box["color"] = GREEN
            if hand_closed:  # If hand is closed, pick up the box
                box["held"] = True
        else:
            box["color"] = RED

        # If the box is held, move it with the hand
        if box["held"]:
            box["x"], box["y"] = hand_pos
            if not hand_closed:  # Drop the box if the hand is opened
                box["held"] = False

        # Keep the box within bounds
        box["x"] = max(30, min(GAME_WIDTH - 30, box["x"]))
        box["y"] = max(30, min(HEIGHT - 30, box["y"]))

        # Draw the box (Increased size for better visibility)
        pygame.draw.rect(screen, box["color"], (box["x"] - 30, box["y"] - 30, 60, 60))

    # Draw the hand position (change color based on open/closed hand)
    hand_color = GREEN if hand_closed else BLUE
    pygame.draw.circle(screen, hand_color, hand_pos, 15)

    # Display the camera feed
    if camera_frame is not None:
        cam_surf = pygame.surfarray.make_surface(cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB))
        cam_surf = pygame.transform.rotate(cam_surf, -90)  # Rotate for proper orientation
        cam_surf = pygame.transform.flip(cam_surf, True, False)  # Mirror the feed
        screen.blit(cam_surf, (GAME_WIDTH, 0))

    # Update the display
    pygame.display.flip()
    clock.tick(60)

# Clean up
cap.release()
pygame.quit()
cv2.destroyAllWindows()