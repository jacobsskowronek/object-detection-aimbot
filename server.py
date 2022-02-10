from io import BytesIO
from yolov4_inference import run_inference
import time
# To run:
# docker run --gpus=all -ti --rm --expose 12345 -v ${PWD}:/yolov4_server opencv_cuda cd yolov4_server;  python server.py
import numpy as np
import socket
import struct
from numba import njit

ADDRESS = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 2048

def pack_frame(frame):
    f = BytesIO()
    np.savez(f, frame=frame)

    length = len(f.getvalue())
    header = struct.pack("!i", length)

    out = bytearray()
    out += header

    f.seek(0)
    out += f.read()
    return out


def read_packet(sock, count):
    buf = bytearray()
    while len(buf) < count:
        newbuf = sock.recv(count - len(buf))
        # print(newbuf[:4])
        if not newbuf: return None
        buf.extend(newbuf)
    return buf

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 12345))
        s.settimeout(5.0)
        try:
            s.listen()
            conn, addr = s.accept()
        except:
            return
        print("Connected to", addr)

        with conn:
            while True:
                try:
                    length = struct.unpack("!i", read_packet(conn, 4))[0]
                    # print(length)
                    data = read_packet(conn, length)
                    # print(data)
                    # print(len(data))
                    frame = np.load(BytesIO(data[:length]), allow_pickle=True)["frame"]
                    now = time.time()
                    boxes, class_ids, confidences = run_inference(frame)
                    # print("Inference time: ", time.time() - now)
                    
                    out = pack_frame([boxes, class_ids, confidences])

                    conn.sendall(out)
                except Exception as e:
                    print(e)
                    return
while True:
    main()
    