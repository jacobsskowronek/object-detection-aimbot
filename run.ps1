docker run --gpus=all -ti --rm --expose 12345 -v ${PWD}:/yolov4_server opencv_cuda cd yolov4_server;  python server.py & python maincontroller.py
PAUSE