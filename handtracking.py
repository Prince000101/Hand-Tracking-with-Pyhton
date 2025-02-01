import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import Canvas, Label
import threading
from PIL import Image, ImageTk

# Mediapipe Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Global Variables
left_count = 0
right_count = 0
highlight_left = False
highlight_right = False
hand_open = True
camera_frame = None

# Function to update UI safely in Tkinter
def update_ui(root, canvas, left_label, right_label, cam_label):
    global highlight_left, highlight_right, left_count, right_count, camera_frame

    if camera_frame is not None:
        cam_image = ImageTk.PhotoImage(image=Image.fromarray(camera_frame))
        cam_label.config(image=cam_image)
        cam_label.image = cam_image  # Store reference to prevent garbage collection

    # Update left and right highlights
    canvas.delete("all")
    if highlight_left:
        canvas.create_rectangle(0, 0, 300, 500, fill="lightblue", outline="")
    if highlight_right:
        canvas.create_rectangle(300, 0, 600, 500, fill="lightgreen", outline="")
    canvas.create_line(300, 0, 300, 500, fill="black", width=2)

    # Update counters
    left_label.config(text=str(left_count))
    right_label.config(text=str(right_count))

    # Schedule next update
    root.after(10, update_ui, root, canvas, left_label, right_label, cam_label)

# Function to process webcam feed
def process_feed():
    global highlight_left, highlight_right, left_count, right_count, hand_open, camera_frame

    cap = cv2.VideoCapture(0)

    # Set higher resolution for wider screen
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    while cap.isOpened():
        success, img = cap.read()
        if not success:
            break

        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        highlight_left = False
        highlight_right = False

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                h, w, _ = img.shape
                cx, cy = int(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x * w), \
                         int(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y * h)

                if cx < w // 2:
                    highlight_left = True
                else:
                    highlight_right = True

                # Detect open or closed hand
                fingers = [1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y else 0
                           for tip, base in zip([8, 12, 16, 20], [6, 10, 14, 18])]
                is_closed = sum(fingers) == 0

                if is_closed and hand_open:
                    if highlight_left:
                        left_count += 1
                    if highlight_right:
                        right_count += 1
                    hand_open = False
                elif not is_closed:
                    hand_open = True

                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        camera_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    cap.release()  # Ensure camera is properly released

# Tkinter UI Setup
def start_app():
    root = tk.Tk()
    root.title("Hand Tracker")
    root.geometry("1100x600")  # Increased window size

    # Create Canvas
    canvas = Canvas(root, width=600, height=500, bg="white")  # Increased width
    canvas.pack(side=tk.LEFT)

    # Camera Feed Label (Increased size)
    cam_label = Label(root, bg="black", width=500, height=400)  # Increased size
    cam_label.pack(side=tk.RIGHT, padx=10, pady=10)

    # Counter Labels
    left_label = tk.Label(root, text="0", font=("Helvetica", 32), fg="blue")
    left_label.place(x=120, y=20)

    right_label = tk.Label(root, text="0", font=("Helvetica", 32), fg="green")
    right_label.place(x=420, y=20)

    # Start Mediapipe processing in a separate thread
    threading.Thread(target=process_feed, daemon=True).start()

    # Start UI update loop
    update_ui(root, canvas, left_label, right_label, cam_label)

    root.mainloop()

if __name__ == "__main__":
    start_app()

