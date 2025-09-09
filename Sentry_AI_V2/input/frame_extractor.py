import cv2

class FrameExtractor:
    def __init__(self, resize=(640, 480)):
        """
        :param resize: tuple (width, height) to resize frames
        """
        self.resize = resize

    def preprocess(self, frame):
        """
        Preprocess frame (resize, convert to RGB if needed).
        :param frame: input frame (BGR from OpenCV).
        :return: processed frame
        """
        if self.resize:
            frame = cv2.resize(frame, self.resize)
        return frame
