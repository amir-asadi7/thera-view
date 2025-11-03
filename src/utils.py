import cv2

def create_writer(filename, codec, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc(*codec)
    return cv2.VideoWriter(filename, fourcc, fps, (width, height))
