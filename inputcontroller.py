# import pydirectinput
import win32api, win32con
import pyWinhook as pyHook
import pythoncom
import time
import numpy as np
import pydirectinput
aimbot_key = "V"
aimbot_enabled = False

def OnKeyboardEvent(event):
    global aimbot_enabled

    if event.Key == aimbot_key and event.Transition == 0:
        aimbot_enabled = True
    elif event.Key == aimbot_key and event.Transition != 0:
        aimbot_enabled = False

    return True

def distance(x1, y1, x2, y2):
    return pow(pow(x1-x2, 2) + pow(y1-y2, 2), 0.5)

def midpoint(x1, x2):
    return (x1 + x2) / 2.

class InputController:
    def __init__(self, ss_box, screen_width, screen_height, sens_x=0.8, sens_y=0.8, sens_x_d=1.0, sens_y_d=1.0, sens_x_i=1.0, sens_y_i=1.0, headshot_only=True, max_distance=1000):
        self.sens_x = sens_x
        self.sens_y = sens_y
        self.sens_x_d = sens_x_d
        self.sens_y_d = sens_y_d
        self.sens_x_i = sens_x_i
        self.sens_y_i = sens_y_i
        self.headshot_only = headshot_only
        self.max_distance = max_distance

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.ss_box = ss_box

        self.closest_x = self.closest_y = 0
        self.closest_box_width = 0
        self.last_mouse_relative_x = self.last_mouse_relative_y = 0
        self.integral_x = 0
        self.integral_y = 0

        self.integral_reset_timer = 0

        self.last_step = 0

        hm = pyHook.HookManager()
        hm.KeyDown = OnKeyboardEvent
        hm.KeyUp = OnKeyboardEvent
        hm.HookKeyboard()

        #self.arduino = serial.Serial('COM6', 113111, timeout=0)



    def convert_to_screen_from_box(self, x, y):
        new_x = self.ss_box["left"] + x
        new_y = self.ss_box["top"] + y

        return new_x, new_y

    def update_configs(self, configs):
        self.sens_x = configs["sens_x"]
        self.sens_y = configs["sens_y"]

    def aimbot_enabled(self):
        return aimbot_enabled

    def update(self, boxes, class_ids):

        #print(aimbot_enabled)

        if aimbot_enabled == False:
            self.integral_x = 0
            self.integral_y = 0
            self.last_mouse_relative_x = 0
            self.last_mouse_relative_y = 0
            self.last_step = time.time()
            return # Enable

        
        mouse_x, mouse_y = pydirectinput.position()

        closest_distance = 9999

        if boxes is not None:
            self.closest_x = self.closest_y = 0
            if len(boxes) == 0:
                self.integral_reset_timer += 1
                if self.integral_reset_timer >= 5:
                    self.integral_x = self.integral_y = 0
            for i in range(len(boxes)):
                (x1, y1) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])
                (x2, y2) = (x1 + w, y1 + h)

                x1, y1 = self.convert_to_screen_from_box(x1, y1)
                x2, y2 = self.convert_to_screen_from_box(x2, y2)


                if mouse_x < x2 and mouse_x > x1:
                    print("Shoot")




                box_class = class_ids[i]

                target_x = midpoint(x1, x2)

                if (box_class == 0 or box_class == 2) and self.headshot_only:
                    head = y1 - (y2 - y1) * 0.8
                    target_y = midpoint(head, y2)
                else:
                    y1 = y1 - (y2 - y1) * 0.4
                    target_y = midpoint(y1, y2)

                relative_distance = distance(target_x, target_y, mouse_x, mouse_y)

                if relative_distance < closest_distance and relative_distance < self.max_distance:
                    self.closest_x = target_x
                    self.closest_y = target_y
                    self.closest_box_width = x2 - x1

        
            
        if self.closest_y > 0 and self.closest_x > 0:
            mouse_relative_x = self.closest_x - mouse_x
            mouse_relative_y = self.closest_y - mouse_y
        else:
            mouse_relative_x = 0
            mouse_relative_y = 0

        now = time.time()
        dt = now - self.last_step
        self.last_step = now


        if abs(mouse_relative_x) < 4:#2 * (self.closest_box_width / 3.0) and abs(mouse_relative_x) > self.closest_box_width / 3.0:
            mouse_relative_x = 0
        if abs(mouse_relative_y) < 4:
            mouse_relative_y = 0

        derivative_x = (mouse_relative_x - self.last_mouse_relative_x) / dt
        derivative_y = (mouse_relative_y - self.last_mouse_relative_y) / dt

        self.integral_x += (mouse_relative_x * dt)
        self.integral_y += (mouse_relative_y * dt)

        self.last_mouse_relative_x = mouse_relative_x
        self.last_mouse_relative_y = mouse_relative_y




        final_x = int((mouse_relative_x * self.sens_x) + (derivative_x * self.sens_x_d) + (self.integral_x * self.sens_x_i))
        final_y = int((mouse_relative_y * self.sens_y) + (derivative_y * self.sens_y_d) + (self.integral_y * self.sens_y_i))

        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, final_x, final_y, 0, 0) # Enable




# data = str(final_x) + ":" + str(final_y)
# self.arduino.write(data.encode())
# int(self.screen_width / 2), int(self.screen_height)


                
                    

                