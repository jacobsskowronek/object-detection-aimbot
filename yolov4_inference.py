import cv2
import numpy as np
import time
from numba import njit
CONFIDENCE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.6
MODEL_PATH = "trained_yolov4/yolov4_tiny_1.weights"
CFG_PATH = "trained_yolov4/yolov4_tiny.cfg"



net = cv2.dnn.readNet(model=MODEL_PATH, config=CFG_PATH)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)


layer = net.getLayerNames()
layer = [layer[i - 1] for i in net.getUnconnectedOutLayers()]


img_width = 0
img_height = 0

def net_forward(img):
    global img_width, img_height
    blob = cv2.dnn.blobFromImage(img, 1/255., (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    # now = time.time()
    outs = net.forward(layer)

    img_width = img.shape[0]
    img_height = img.shape[1]

    return outs
@njit
def process_out(out):
    boxes = []
    class_ids = []
    confidences = []
    for detection in out:
        scores = detection[5:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]

        if confidence > CONFIDENCE_THRESHOLD:
            box = detection[0:4] * np.array([img_width, img_height, img_width, img_height])
            (centerX, centerY, width, height) = box.astype(np.int32)
            x = int(centerX - (width / 2))
            y = int(centerY - (height / 2))

            boxes.append([x, y, width, height])
            class_ids.append(class_id)
            confidences.append(confidence)
    
    return boxes, class_ids, confidences


#@njit
def process_nms(idxs, boxes, class_ids, confidences):

    final_boxes = [boxes[i] for i in range(len(boxes)) if i in idxs]
    final_class_ids = [class_ids[i] for i in range(len(boxes)) if i in idxs]
    final_confidences = [confidences[i] for i in range(len(boxes)) if i in idxs]

    return final_boxes, final_class_ids, final_confidences


def run_inference(img):
    boxes = []
    class_ids = []
    confidences = []

    outs = net_forward(img)
    for out in outs:
        new_boxes, new_class_ids, new_confidences = process_out(out)
        boxes = boxes + new_boxes
        class_ids = class_ids + new_class_ids
        confidences = confidences + new_confidences

    
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)

    # boxes = np.array(boxes)
    # class_ids = np.array(class_ids)
    # confidences = np.array(confidences)

    final_boxes, final_class_ids, final_confidences = process_nms(idxs, boxes, class_ids, confidences)

    

    for i in range(len(boxes)):
        if i in idxs:
            final_boxes.append(boxes[i])
            final_class_ids.append(class_ids[i])
            final_confidences.append(confidences[i])


    return final_boxes, final_class_ids, final_confidences


if __name__ == "__main__":
    import time
    count = cv2.cuda.getCudaEnabledDeviceCount()
    print("GPU Count: ", count)
    img = cv2.imread("test_image.jpg")


    update_every = 1
    now = time.time()
    count = 0

    import cProfile
    import pstats
    import mss
    from win32api import GetSystemMetrics
    BOX_WIDTH, BOX_HEIGHT = 400, 400
    WIDTH = GetSystemMetrics(0)
    HEIGHT = GetSystemMetrics(1)
    box_left = int(WIDTH / 2 - BOX_WIDTH / 2)
    box_right = int(WIDTH / 2 + BOX_WIDTH / 2)
    box_up = int(HEIGHT / 2 - BOX_HEIGHT / 2)
    box_down = int(HEIGHT / 2 + BOX_HEIGHT / 2)
    ss_box = {"left": box_left, "top": box_up, "width": BOX_WIDTH, "height": BOX_HEIGHT}
    with mss.mss() as mss_instance:
        for i in range(0, 10000):
            img2 = mss_instance.grab(ss_box)
            #img2 = np.array(img2)
            #img2 = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
            if i == 5000:
                with cProfile.Profile() as pr:
                    run_inference(img)
                    #break
            result = run_inference(img)
            if time.time() - now >= update_every:
                print(count / update_every)
                count = 0
                now = time.time()

            count += 1

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()