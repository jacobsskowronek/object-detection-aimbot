from configs import *
import time
import cv2
import os



def add_info_to_image(img, boxes, class_ids, confidences, box_width, box_height, fps, max_distance):
    cv2.circle(img, center=(int(box_width / 2), int(box_height / 2)), radius=int(max_distance), color=(255, 255, 255), thickness=1)
    for i in range(len(boxes)):
        (x, y) = (boxes[i][0], boxes[i][1])
        (w, h) = (boxes[i][2], boxes[i][3])

        color = [int(c) for c in COLORS[class_ids[i]]]
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        
        text = "{}: {:.4f}".format(LABELS[class_ids[i]], confidences[i])
        cv2.putText(
            img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
        )
    cv2.putText(img, "FPS: " + str(fps), (20, 30), cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), 1)

    return img

def show_image(queue):
    img = []
    fps = 0

    while True:
        if queue.qsize() == 0: continue
        boxes, class_ids, confidences, img, config = queue.get()

        if config["exit"] == True: break

        show_image = config["show_output"]
        max_distance = config["max_distance"]
        fps = config["fps"]
        box_width = config["box_width"]
        box_height = config["box_height"]

        if show_image:
            img = add_info_to_image(img, boxes, class_ids, confidences, box_width, box_height, fps, max_distance)

            img = cv2.resize(img, (400, 400))
            
            cv2.imshow("Output", img)
            cv2.setWindowProperty("Output", cv2.WND_PROP_TOPMOST, 1)
            cv2.waitKey(1)
        else:
            cv2.destroyAllWindows()


lasttime = time.time()
update_every = 1
def generate_training(boxes, class_ids, img):
    global lasttime
    if time.time() - lasttime > update_every:

        savetime=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
        
        cv2.imwrite(os.path.join(TRAINING_FOLDER) + savetime + ".jpg", img)
        with open(os.path.join(TRAINING_FOLDER) + savetime + ".txt", "w") as f:
            for i in range(len(boxes)):
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])

                x2 = x + w
                y2 = y + h

                x = max(min(x, BOX_WIDTH), 0)
                y = max(min(y, BOX_HEIGHT), 0)
                x2 = max(min(x2, BOX_WIDTH), 0)
                y2 = max(min(y2, BOX_HEIGHT), 0)

                w = x2 - x
                h = y2 - y

                centerX = (x + x2) / 2.0
                centerY = (y + y2) / 2.0

                centerX /= BOX_WIDTH
                centerY /= BOX_HEIGHT
                w /= BOX_WIDTH
                h /= BOX_HEIGHT

                f.write(f"{class_ids[i]} {centerX} {centerY} {w} {h}\n")

        lasttime = time.time()

        print(f"{savetime} saved")