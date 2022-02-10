from win32api import GetSystemMetrics
import numpy as np



BOX_WIDTH, BOX_HEIGHT = 400, 400
WIDTH = GetSystemMetrics(0)
HEIGHT = GetSystemMetrics(1)

LABELS = ["ct_body", "ct_head", "t_body", "t_head"]
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")

TRAINING_FOLDER = "training/"

configs =   {     
                "generate_training": False, 
                "fps_limit": 60, 
                "box_width": BOX_WIDTH, "box_height": BOX_HEIGHT, 
                "sens_x": 0.35, "sens_y": 0.3, 
                "sens_x_d": 0.35, "sens_y_d": 0.3,
                "sens_x_i": 0.35, "sens_y_i": 0.3,
                "fps": 0, 
                "aimbot_key": "P", 
                "exit": False, 
                "show_output": True, 
                "headshot_only": True, 
                "max_distance": 100
            }