import cv2
import numpy as np
import time
CONFIDENCE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.6
MODEL_PATH = "trained_yolov4/yolov4_tiny_1.weights"
CFG_PATH = "trained_yolov4/yolov4_tiny.cfg"



net = cv2.dnn.readNet(model=MODEL_PATH, config=CFG_PATH)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)


layer = net.getLayerNames()
layer = [layer[i - 1] for i in net.getUnconnectedOutLayers()]



def run_inference(img):
    blob = cv2.dnn.blobFromImage(img, 1/255., (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    # now = time.time()
    outs = net.forward(layer)
    # print(time.time() - now)
    boxes = []
    class_ids = []
    confidences = []

    img_width = img.shape[0]
    img_height = img.shape[1]
        
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > CONFIDENCE_THRESHOLD:
                box = detection[0:4] * np.array([img_width, img_height, img_width, img_height])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, width, height])
                class_ids.append(class_id)
                confidences.append(confidence)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)

    final_boxes, final_class_ids, final_confidences = [], [], []


    final_boxes = [boxes[i] for i in range(len(boxes)) if i in idxs]
    final_class_ids = [class_ids[i] for i in range(len(boxes)) if i in idxs]
    final_confidences = [confidences[i] for i in range(len(boxes)) if i in idxs]

    # for i in range(len(boxes)):
    #     if i in idxs:
    #         final_boxes.append(boxes[i])
    #         final_class_ids.append(class_ids[i])
    #         final_confidences.append(confidences[i])


    return final_boxes, final_class_ids, final_confidences


if __name__ == "__main__":
    import time
    count = cv2.cuda.getCudaEnabledDeviceCount()
    print("GPU Count: ", count)
    image = cv2.imread("test_image.jpg")


    update_every = 1
    now = time.time()
    count = 0
    while True:
        result = run_inference(image)
        if time.time() - now >= update_every:
            print(count / update_every)
            count = 0
            now = time.time()

        count += 1