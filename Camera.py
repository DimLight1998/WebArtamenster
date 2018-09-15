from FrameProvider import *
from FrameProcessor import *
import redis
import redis_lock
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('camera_mode', metavar='camera_mode', type=str,
                        help='< queue | newest >')
    parser.add_argument('camera_source', metavar='camera_source', type=str,
                        help='< local | url_to_remote_camera >')
    parser.add_argument('process_method', metavar='process_method', type=str,
                        help='< abs_motion | rel_motion | darknet | ssd_obj | obj_tracker >')

    args = parser.parse_args()

    if args.camera_mode == 'queue':
        if args.camera_source == 'local':
            frame_provider = QueueFrameProvider()
        else:
            frame_provider = QueueFrameProvider(False, args.camera_source)
    elif args.camera_mode == 'newest':
        if args.camera_source == 'local':
            frame_provider = NewestFrameProvider()
        else:
            frame_provider = NewestFrameProvider(False, args.camera_source)
    else:
        print('unknown camera mode')
        exit()

    if args.process_method == 'abs_motion':
        frame_processor = AbsoluteMotionDetectionFrameProcessor(frame_provider.next_frame())
    elif args.process_method == 'rel_motion':
        frame_processor = RelativeMotionDetectionFrameProcessor()
    elif args.process_method == 'darknet':
        frame_processor = DarknetObjectDetectionFrameProcessor('net/Yolo.cfg', 'net/Yolo.weights', 1.0)
    elif args.process_method == 'ssd_obj':
        frame_processor = MobileNetSsdObjectDetectionFrameProcessor(
            'net/MobileNetSsd.proto', 'net/MobileNetSsd.caffemodel'
        )
    elif args.process_method == 'obj_tracker':
        frame_processor = ObjectTrackerFrameProcessor('net/ObjectTracker.proto', 'net/ObjectTracker.caffemodel')
    else:
        print('unknown process method!')
        exit()

    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    # press q to exit
    while True:
        img = cv2.imencode('.jpg', frame_processor.process(frame_provider.next_frame()))[1]
        with redis_lock.Lock(r, "image"):
            r.set('image', img.tobytes())
