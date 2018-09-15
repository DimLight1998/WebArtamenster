import time

import cv2
from darkflow.net.build import TFNet
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from CentroidTracker import CentroidTracker


class FrameProcessor:
    def process(self, frame):
        """
        Process the frame using certain method
        :param frame: Frame to be processed, should be in openCV format.
        :return: Processing result.
        """
        raise NotImplementedError


class AbsoluteMotionDetectionFrameProcessor(FrameProcessor):
    """
    Ref: https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    """

    def __init__(self, initial_frame, min_area=500, tolerance=50):
        """
        :param initial_frame: First frame of the sequence.
        :param min_area: A area, difference smaller than this will be ignored.
        :param tolerance: Used for threshold the the difference, the lower the more sensitive.
        """
        self.initial_gray_frame = None
        self.reset_initial_frame(initial_frame)
        self.min_area = min_area
        self.tolerance = tolerance

    def reset_initial_frame(self, initial_frame):
        """
        Reset initial frame.
        :param initial_frame: New initial frame.
        """
        if initial_frame is not None:
            initial_gray_frame = cv2.cvtColor(initial_frame, cv2.COLOR_BGR2GRAY)
            self.initial_gray_frame = cv2.GaussianBlur(initial_gray_frame, (21, 21), 0)
        else:
            self.initial_gray_frame = None

    def process(self, frame):
        frame_copy = frame.copy()
        gray_frame = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        frame_delta = cv2.absdiff(self.initial_gray_frame, gray_frame)
        threshold = cv2.threshold(frame_delta, self.tolerance, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None, iterations=2)
        contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]

        for c in contours:
            if cv2.contourArea(c) < self.min_area:
                continue

            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return frame_copy


class RelativeMotionDetectionFrameProcessor(FrameProcessor):
    """
    Ref: https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    """

    def __init__(self, min_area=500, tolerance=50):
        """
        :param min_area: A area, difference smaller than this will be ignored.
        :param tolerance: Used for threshold the the difference, the lower the more sensitive.
        """
        self.internal_processor = AbsoluteMotionDetectionFrameProcessor(None, min_area, tolerance)

    def process(self, frame):
        if self.internal_processor.initial_gray_frame is None:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.internal_processor.initial_gray_frame = gray_frame
            return frame
        else:
            ret = self.internal_processor.process(frame)
            self.internal_processor.reset_initial_frame(frame)
            return ret


class DarknetObjectDetectionFrameProcessor(FrameProcessor):
    """
    Ref: https://github.com/thtrieu/darkflow
    """

    @staticmethod
    def draw_rect(drawing, topleft, bottomright, outline, width):
        """
        Draw a rectangle with line width on `ImageDraw` object.
        """
        top_left = topleft
        bottom_right = bottomright
        top_right = (bottomright[0], topleft[1])
        bottom_left = (topleft[0], bottomright[1])

        drawing.line([top_left, top_right], fill=outline, width=width)
        drawing.line([top_right, bottom_right], fill=outline, width=width)
        drawing.line([bottom_right, bottom_left], fill=outline, width=width)
        drawing.line([bottom_left, top_left], fill=outline, width=width)

    def __init__(self, model, weights, gpu_limit, threshold=0.1):
        """
        :param model: Path to the model (e.g. './darkflow/cfg/yolo.cfg')
        :param weights: Path to the weights file (e.g. './darkflow/bin/yolo.weights')
        :param gpu_limit: Limitation of GPU, set to 0 to run on CPU only.
        :param threshold: Threshold of recognition.
        """
        self.tf_net = TFNet({
            'model': model, 'load': weights, 'threshold': threshold, 'gpu': gpu_limit, 'labels': 'cfg/coco.names'
        })

    def process(self, frame):
        now = time.time()
        image = Image.fromarray(frame[:, :, ::-1])
        results = self.tf_net.return_predict(frame)
        draw = ImageDraw.ImageDraw(image)
        font = ImageFont.truetype('Consolas.ttf', 15)

        for result in results:
            if result['confidence'] < 0.5:
                continue

            alpha = int((result['confidence'] * 2 - 1) * 125 + 100)

            DarknetObjectDetectionFrameProcessor.draw_rect(
                draw,
                (result['topleft']['x'], result['topleft']['y']),
                (result['bottomright']['x'], result['bottomright']['y']),
                (95, 248, 111, alpha), 4
            )
            text = f'{result["label"]} - {"%.2f" % (100 * result["confidence"])}%'
            draw.text(
                (result['topleft']['x'], result['topleft']['y'] - 18),
                text, fill=(95, 258, 111, alpha), font=font
            )
        print(f'process takes {time.time() - now} sec')
        return np.array(image)[:, :, ::-1]


class MobileNetSsdObjectDetectionFrameProcessor(FrameProcessor):
    """
    Ref: https://www.pyimagesearch.com/2017/09/18/real-time-object-detection-with-deep-learning-and-opencv/
    """

    def __init__(self, proto, model, confidence_threshold=0.2):
        """
        :param proto: Path to the prototxt (e.g. MobileNetSSD_deploy.prototxt.txt)
        :param model: Path to the caffe model (e.g. MobileNetSSD_deploy.caffemodel)
        :param confidence_threshold: Threshold of the confidence to filter less confident detections.
        """
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        self.net = cv2.dnn.readNetFromCaffe(proto, model)
        self.confidence_threshold = confidence_threshold

    def process(self, frame):
        (height, width) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()

        for i in np.arange(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > self.confidence_threshold:
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                (startX, startY, endX, endY) = box.astype("int")

                label = "{}: {:.2f}%".format(self.classes[idx], confidence * 100)
                cv2.rectangle(frame, (startX, startY), (endX, endY), self.colors[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors[idx], 2)

        return frame


class ObjectTrackerFrameProcessor(FrameProcessor):
    """
    Ref: https://www.pyimagesearch.com/2018/07/23/simple-object-tracking-with-opencv/
    """

    def __init__(self, proto, model, confidence_threshold=0.5):
        """
        :param proto: Path to the prototxt
        :param model: Path to the caffe model
        :param confidence_threshold: Threshold of the confidence to filter less confident detections.
        """
        self.centroidTracker = CentroidTracker()
        self.net = cv2.dnn.readNetFromCaffe(proto, model)
        self.confidence_threshold = confidence_threshold

    def process(self, frame):
        (height, width) = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(frame, 1.0, (width, height), (104.0, 177.0, 123.0))
        self.net.setInput(blob)
        detections = self.net.forward()
        rects = []

        for i in range(0, detections.shape[2]):
            if detections[0, 0, i, 2] > self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                rects.append(box.astype("int"))

                (startX, startY, endX, endY) = box.astype("int")
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)

        objects = self.centroidTracker.update(rects)

        for (objectID, centroid) in objects.items():
            text = "ID {}".format(objectID)
            cv2.putText(
                frame, text, (centroid[0] - 10, centroid[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )
            cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

        return frame
