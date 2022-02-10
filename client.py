import socket
import struct
import time
from io import BytesIO
import numpy as np

from yolov4_inference import run_inference

def pack_frame(frame, add_header=True):
    f = BytesIO()
    np.savez(f, frame=frame)

    length = len(f.getvalue())
    header = struct.pack("!i", length)

    out = bytearray()
    if add_header:
        out += header

    f.seek(0)
    out += f.read()
    return out

def read_packet(sock, count):
    buf = bytearray()
    while len(buf) < count:
        newbuf = sock.recv(count - len(buf))
        if not newbuf: return None
        buf.extend(newbuf)
    return buf


class Client:
    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("127.0.0.1", port))


    def disconnect(self):
        self.socket.close()

    def run_inference(self, img):
        out = pack_frame(img)


        sendtime = time.time()
        self.socket.sendall(out)

        length = struct.unpack("!i", read_packet(self.socket, 4))[0]

        data = read_packet(self.socket, length)

        frame = np.load(BytesIO(data[:length]), allow_pickle=True)["frame"]


        return frame

