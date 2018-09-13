from FrameProvider import *
from FrameProcessor import *
import redis

if __name__ == '__main__':
    # you will need a frame provider and a processor

    # provider examples
    # provider = NewestFrameProvider()  # computer camera, always get newest
    # provider = QueueFrameProvider()  # computer camera, get images in a queue
    # provider = NewestFrameProvider(False, 'http://192.168.137.12:8080/video')  # phone camera over http, newest
    # provider = QueueFrameProvider(False, 'http://192.168.137.12:8080/video')  # phone camera over http, queued
    frame_provider = NewestFrameProvider()  # computer camera, always get newest

    # processor examples
    # processor = AbsoluteMotionDetectionFrameProcessor(frame_provider.next_frame())
    # processor = RelativeMotionDetectionFrameProcessor()
    # processor = DarknetObjectDetectionFrameProcessor('net/Yolo.cfg', 'net/Yolo.weights', 1.0)  # need darkflow
    # processor = MobileNetSsdObjectDetectionFrameProcessor('net/MobileNetSsd.proto', 'net/MobileNetSsd.caffemodel')
    # processor = ObjectTrackerFrameProcessor('net/ObjectTracker.proto', 'net/ObjectTracker.caffemodel')
    frame_processor = MobileNetSsdObjectDetectionFrameProcessor('net/MobileNetSsd.proto', 'net/MobileNetSsd.caffemodel')

    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    # press q to exit
    while True:
        img = cv2.imencode('.jpg', frame_processor.process(frame_provider.next_frame()))[1]
        r.set('image', img)
