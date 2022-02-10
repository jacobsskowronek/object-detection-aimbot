from configs import *
from show_output import *
from inputcontroller import *
from client import Client
import cv2, mss
import numpy as np
from multiprocessing import Process, Queue
import time
# import yolov4_inference2

box_left = int(WIDTH / 2 - BOX_WIDTH / 2)
box_right = int(WIDTH / 2 + BOX_WIDTH / 2)
box_up = int(HEIGHT / 2 - BOX_HEIGHT / 2)
box_down = int(HEIGHT / 2 + BOX_HEIGHT / 2)
ss_box = {"left": box_left, "top": box_up, "width": BOX_WIDTH, "height": BOX_HEIGHT}


import PySimpleGUI as sg

layout = [
        [sg.Output(size=(60,10))],
        [sg.Image(filename="", key="-IMAGE-")],
        [sg.Slider(range=(0, BOX_WIDTH), default_value=100, resolution=1, orientation="horizontal", key="-MAXDISTANCE-", tooltip="Aimbot FOV")],
        [sg.Slider(range=(0, 10), default_value=0.8, resolution=0.01, orientation="horizontal", key="sens_x", tooltip="Sensitivity X"), sg.Button("Apply", expand_y=True), sg.Checkbox("Headshot Only", key="-HEADSHOT-", default=True, enable_events=True)],
        [sg.Slider(range=(0, 10), default_value=0.8, resolution=0.01, orientation="horizontal", key="sens_y", tooltip="Sensitivity Y")],
        [sg.Slider(range=(0, 10), default_value=6.267, resolution=0.001, orientation="horizontal", key="sens_x_i", tooltip="Integral Sensitivity X")],
        [sg.Slider(range=(0, 10), default_value=6.267, resolution=0.001, orientation="horizontal", key="sens_y_i", tooltip="Integral Sensitivity Y")],
        [sg.Slider(range=(0, 0.2), default_value=0.0160, resolution=0.0001, orientation="horizontal", key="sens_x_d", tooltip="Derivative Sensitivity X")],
        [sg.Slider(range=(0, 0.2), default_value=0.0160, resolution=0.0001, orientation="horizontal", key="sens_y_d", tooltip="Derivative Sensitivity Y")],
        [sg.Slider(range=(1, 240), default_value=60, resolution=1, orientation="horizontal", key="fps_limit", tooltip="FPS Limit")],
        [sg.Button('Start Detection'), sg.Button("Stop Detection"), sg.Checkbox("Generate Training", default=False, key="-TRAINING-", enable_events=True), sg.Checkbox("Show Output", default=False, key="-OUTPUT-", enable_events=True), sg.Button("Exit")] 
    ]

window = sg.Window('Nagasaki University Research', layout)



import yolov4_inference as inference
def update(inference_queue, queues):
    # Use if running through server
    #client = Client(12345)

    fps = 0
    lapsed_frames = 0
    update_every = 2
    lasttime = time.time()

    configs = {}

    fps_limit = 120


    last_detected = False


    with mss.mss() as mss_instance:
        while True:
            start = time.perf_counter()
            time_delta = 1.0 / fps_limit #+ 1e-3
            if inference_queue.qsize() > 0:
                configs = inference_queue.get()

            fps_limit = configs["fps_limit"]

            img = mss_instance.grab(ss_box)
            img = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
            # Change to client.run_inference(img) if running through server
            info = inference.run_inference(img)

            boxes = []
            class_ids = []
            confidences = []


            if len(info[0]) > 0:
                boxes = info[0]
                class_ids = info[1]
                confidences = info[2]

                if last_detected == False:
                
                    print("Detected: ", time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime()))
                    last_detected = True
            else:
                last_detected = False

            if configs["exit"] == True:
                print("Exit called")
                for queue in queues:
                    queue.put((boxes, class_ids, confidences, img, configs))
                # client.disconnect()
                break

            for queue in queues:
                if queue.qsize() == 0:
                    queue.put((boxes, class_ids, confidences, img, configs))



            lapsed_frames += 1
            if time.time() - lasttime >= update_every:
                fps = int(lapsed_frames / (time.time() - lasttime))
                lapsed_frames = 0
                lasttime = time.time()
                print("FPS: ", fps)
                configs["fps"] = fps
                

            while time_delta - (time.perf_counter() - start) > 0:
                pass

            

    print("Exited inference")


def update_input(queue):
    inputcontroller = InputController(ss_box, WIDTH, HEIGHT)

    fps_limit = 60
    time_delta = 1.0 / fps_limit
    

    input_fps = 0
    lapsed_frames = 0
    update_every = 2
    lasttime = time.time()

    import pythoncom
    while True:
        start = time.perf_counter()
        # print("update_input")
        boxes = None
        class_ids = None
        if queue.qsize() > 0:
            boxes, class_ids, confidences, img, configs = queue.get()

            inputcontroller.sens_x = configs["sens_x"]
            inputcontroller.sens_y = configs["sens_y"]
            inputcontroller.sens_x_d = configs["sens_x_d"]
            inputcontroller.sens_y_d = configs["sens_y_d"]
            inputcontroller.sens_x_i = configs["sens_x_i"]
            inputcontroller.sens_y_i = configs["sens_y_i"]
            inputcontroller.headshot_only = configs["headshot_only"]
            inputcontroller.max_distance = configs["max_distance"]
            if len(boxes) > 0 and configs["generate_training"] == True and inputcontroller.aimbot_enabled():
                generate_training(boxes, class_ids, img)
            
            if configs["exit"] == True:
                break  
        inputcontroller.update(boxes, class_ids)

        

        lapsed_frames += 1
        if time.time() - lasttime >= update_every:
            input_fps = int(lapsed_frames / (time.time() - lasttime))
            lapsed_frames = 0
            lasttime = time.time()
            print("Input FPS: ", input_fps)

        
        pythoncom.PumpWaitingMessages()
        while time_delta - (time.perf_counter() - start) > 0:
            pythoncom.PumpWaitingMessages()
            pass
            #time.sleep(max(time_delta - (time.time() - start), 0))

    print("Exited input")
    return


def main():
    global configs

    inputcontroller_queue = Queue()
    img_queue = Queue()
    inference_queue = Queue()
    detection_started = False

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Exit':
            configs["exit"] = True
            inference_queue.put(configs)
            print("Joined")
            break

        if event == "Start Detection" and detection_started == False:

            configs["exit"] = False

            while inference_queue.qsize() > 0:
                inference_queue.get()
            inference_queue.put(configs)

            
            inputcontroller_process = Process(target=update_input, args=(inputcontroller_queue,), daemon=True)
            img_process = Process(target=show_image, args=(img_queue,), daemon=True)
            inference_process = Process(target=update, args=(inference_queue, [inputcontroller_queue, img_queue]), daemon=True)
            inference_process.start()
            inputcontroller_process.start()
            img_process.start()
            print("Detection started")

            detection_started = True
        
        if event == "Stop Detection" and detection_started == True:
            configs["exit"] = True
            
            inference_queue.put(configs)

            inputcontroller_process.join()
            img_process.join()
            inference_process.join()

            print("Detection stopped")

            detection_started = False

        if event == "Apply": 
            configs["sens_x"] = values["sens_x"]
            configs["sens_y"] = values["sens_y"]
            configs["sens_x_d"] = values["sens_x_d"]
            configs["sens_y_d"] = values["sens_y_d"]
            configs["sens_x_i"] = values["sens_x_i"]
            configs["sens_y_i"] = values["sens_y_i"]
            configs["fps_limit"] =  values["fps_limit"] + 1

            print("Settings applied")

        configs["show_output"] = values["-OUTPUT-"]
        configs["headshot_only"] = values["-HEADSHOT-"]
        configs["max_distance"] = values["-MAXDISTANCE-"]
        configs["generate_training"] = values["-TRAINING-"]



        inference_queue.put(configs)

    window.close()


        






if __name__ == "__main__":
    main()