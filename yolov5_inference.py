import cv2
from matplotlib.pyplot import axes
import torch
import numpy as np
import time
from numba import njit
CONFIDENCE_THRESHOLD = 0.7
NMS_THRESHOLD = 0.6
MODEL_PATH = ""


model = torch.hub.load('ultralytics/yolov5', 'custom', path=MODEL_PATH)
model.conf = CONFIDENCE_THRESHOLD
model.iou = NMS_THRESHOLD
img_width = 0
img_height = 0

def net_forward(img):
    global img_width, img_height
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #img /= 255.0
    img_width = img.shape[0]
    img_height = img.shape[1]

    img = cv2.resize(img, (416, 416))

    #now = time.time()
    outs = model(img, size=img_width)
    #print(time.time() - now)
    return outs

@njit
def parse_outs(outs_np, img_width):
    
    boxes = []
    class_ids = []
    confidences = []

    for i in outs_np:
        box = i[0:4]
        box /= 416.0
        box *= img_width
        box[2] = box[2] - box[0]
        box[3] = box[3] - box[1]


        boxes.append(box.astype(np.int32))
        class_ids.append(i[5])
        confidences.append(i[4])

    return boxes, class_ids, confidences

def run_inference(img):

    #now = time.time()
    outs = net_forward(img)
    #print(time.time() - now)
    df = outs.pandas().xyxy[0].drop(["name"], axis=1)
    outs_np = df.to_numpy()
    #print(outs_np.shape)
    if outs_np.shape[0] == 0:
        return [], [], []
    boxes, class_ids, confidences = parse_outs(outs_np, img_width)


    return boxes, class_ids, confidences


if __name__ == "__main__":
    import time
    count = cv2.cuda.getCudaEnabledDeviceCount()
    print("GPU Count: ", count)
    img = cv2.imread("test_image.jpg")

    #print(model.cuda())
    

    update_every = 1
    now = time.time()
    count = 0

    import cProfile
    import pstats
    for i in range(0, 1000):
        if i == 999:
            with cProfile.Profile() as pr:
                run_inference(img)
                break
        boxes, class_ids, confidences = run_inference(img)
        # print(boxes)
        # print(boxes[0])
        if time.time() - now >= update_every:
            print(count / update_every)
            count = 0
            now = time.time()

        count += 1

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()