import cv2
import time
from camera import Camera
from utils import create_writer
from config import OUTPUT_FILE, CODEC, FPS, FRAME_WIDTH, FRAME_HEIGHT

def record_video(duration=10):  # Default is 10 seconds
    cam = Camera()
    writer = create_writer(OUTPUT_FILE, CODEC, FPS, FRAME_WIDTH, FRAME_HEIGHT)
    start = time.time()

    print(f"Recording for {duration} seconds...")

    while True:
        frame = cam.read_frame()
        writer.write(frame)

        # Optional preview (can remove for headless mode)
        # cv2.imshow("Preview", frame)
        # if cv2.waitKey(1) & 0xFF == ord("q"):
        #     break

        if time.time() - start >= duration:
            break

    cam.release()
    writer.release()
    cv2.destroyAllWindows()
    print(f"Recording complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    record_video()  # records for 10 seconds
