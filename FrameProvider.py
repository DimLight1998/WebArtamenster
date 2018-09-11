import cv2
from imutils.video import videostream


class FrameProvider:
    def next_frame(self):
        """
        Get the most recent frame.
        :return: Data of the frame, openCV format (unencoded).
        """
        raise NotImplementedError


class QueueFrameProvider(FrameProvider):
    def __init__(self, use_local_camera=True, url=None):
        """
        Initialize the frame provider.
        :param use_local_camera: If using camera of the computer, set to `True`.
        :param url: If using video over RTSP/HTTP, set this parameter. Ignored when `use_local_camera` is `True`.
        """
        if use_local_camera:
            self.source = cv2.VideoCapture(0)
        else:
            self.source = cv2.VideoCapture(url)

    def next_frame(self):
        frame = self.source.read()[1]
        return frame


class NewestFrameProvider(FrameProvider):
    def __init__(self, use_local_camera=True, url=None):
        """
        Initialize the frame provider.
        :param use_local_camera: If using camera of the computer, set to `True`.
        :param url: If using video over RTSP/HTTP, set this parameter. Ignored when `use_local_camera` is `True`.
        """
        if use_local_camera:
            self.source = videostream.VideoStream().start()
        else:
            self.source = videostream.VideoStream(url).start()

    def next_frame(self):
        frame = self.source.read()
        return frame
