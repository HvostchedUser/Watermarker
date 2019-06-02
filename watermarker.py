import random

import cv2
import sys
import time
import subprocess
import os
import wave

command = "ffmpeg -i input.mp4 -ab 160k -ac 2 -ar 44100 -vn input.wav"

if not os.path.isfile('input.wav'):
    subprocess.call(command, shell=True)

wave_file = wave.open('input.wav', 'rb')

loss=0



step=1024*1
cap = cv2.VideoCapture("input.mp4")
fps=cap.get(cv2.CAP_PROP_FPS)
len = (cap.get(cv2.CAP_PROP_FRAME_COUNT))
cur=0


lens=0
with open("input.wav", "rb") as fwav:
    data = fwav.read(step)
    while data:
        lens+=1
        data = fwav.read(step)
#with wave.open('input.wav', 'rb') as fwav:
#    lens=fwav.getnframes()/step
#    #print(lens)
curs=0


#print(len)
#print(lens)


def genHeader(sampleRate, bitsPerSample, channels, samples):
    datasize = samples * channels * bitsPerSample // 8
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o


class VideoCamera(object):
    def __init__(self):
        global cur,len
        cur=0
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        #self.video = cv2.VideoCapture(0)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        self.video = cv2.VideoCapture('input.mp4')

    def __del__(self):
        self.video.release()

    def get_frame(self):
        t=time.time()
        global cur
        global len
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        image = cv2.resize(image, (640, 480))
        overlay = image.copy()
        output = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(overlay,(sys.argv[1]),(random.randint(0, 600),random.randint(0, 460)), font, 0.5,(255,255,255),1,cv2.LINE_AA)
        alpha=0.5
        cv2.addWeighted(overlay, alpha, output, 1 - alpha,
                        0, output)
        ret, jpeg = cv2.imencode('.jpg', output)
        cur+=1

        while time.time()<=t+1/fps:
            time.sleep(0.0001)
        return jpeg.tobytes()



from flask import Flask, render_template, Response
app = Flask(__name__,template_folder='.')

@app.route('/audio')
def audio():
    # start Recording
    def sound():
        global curs,lens,loss
        header=genHeader(44100, 32, 1, 200000)
        curs=0
        with open("input.wav", "rb") as fwav:
            data = fwav.read(step)
            while data:
                yield data
                data = fwav.read(int(step))
                #fwav.read(int(loss))
                curs+=1
                while curs/lens >= cur/len:
                    time.sleep(0.001)
                #loss=min(step-1,(cur/len-curs/lens)*1000000)
                #print(loss)
    return Response(sound(), mimetype="audio/x-wav")
@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)