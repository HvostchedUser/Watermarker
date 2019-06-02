import random

import cv2
import sys
import time
import subprocess
import os
import wave
from flask import request
import json

sameshit=False
dbpath="db.json"
progress=dict()
db="";
with open(dbpath) as json_file:
    db = json.load(json_file)
command = "ffmpeg -i input.mp4 -ab 160k -ac 2 -ar 44100 -vn input.wav -y"

#if not os.path.isfile('input.wav'):
#    subprocess.call(command, shell=True)
subprocess.call(command, shell=True)

wave_file = wave.open('input.wav', 'rb')

loss=0
login="";
permkey=""
watmark="nothing"

step=10#1024
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

    def get_frame(self,watmarkk,lgg,cur):
        t=time.time()
        global progress
        global len
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        image = cv2.resize(image, (640, 480))
        overlay = image.copy()
        output = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(overlay,(watmarkk),(random.randint(0, 550),random.randint(0, 460)), font, 0.5,(255,255,255),1,cv2.LINE_AA)
        alpha=0.1
        cv2.addWeighted(overlay, alpha, output, 1 - alpha,
                        0, output)
        #output = image.copy()
        overlay=output.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(overlay, ("specially for "+lgg), (10, 20), font, 0.5, (255, 255, 255),
                    1, cv2.LINE_AA)
        alpha2 = 0.5
        cv2.addWeighted(overlay, alpha2, output, 1 - alpha2,
                        0, output)

        ret, jpeg = cv2.imencode('.jpg', output)
        #cur+=1
        progress[lgg]=cur/len
        while time.time()<t+1/fps:
            time.sleep(0.0001)
        return jpeg.tobytes()



from flask import Flask, render_template, Response
app = Flask(__name__,template_folder='.')

@app.route('/audio')
def audio():
    global login
    lgg=login
    # start Recording
    def sound():
        global lens
        header=genHeader(44100, 32, 1, 200000)
        curs=0
        with open("input.wav", "rb") as fwav:
            data = fwav.read(step)
            while data:
                yield data
                data = fwav.read(int(step))
                #fwav.read(int(loss))
                curs+=1
                while curs/lens >= progress[lgg]:
                    time.sleep(0.001)
                #loss=min(step-1,(cur/len-curs/lens)*1000000)
                #print((str)(progress[lgg])+" --"+(str)(lgg))
    return Response(sound(), mimetype="audio/x-wav")
@app.route('/', methods=['GET','POST'])
def index():
    with open(dbpath) as json_file:
        db = json.load(json_file)
    global watmark,login,permkey,sameshit,progress
    login=request.args.get("login")
    permkey=request.args.get("permit_key")
    for p in db['permits']:
        if p['login'] == login:
            print("same login")
            if p['active'] == True:
                print("active")
                if p['permit_key'] == permkey:
                    print("same key")
                    print(time.time()*1000)
                    print(int(p['release_timestamp']))
                    if int(p['release_timestamp'])+30000>=time.time()*1000:
                        print("same time")
                        #print(login)
                        #print(permkey)
                        watmark = str(request.args.get("login")) + " " + str(round(time.time(),10))
                        sameshit=True
                        print("same shit")
                        progress[login]=0
                        return render_template('index.html')
    return """<html><body>Please follow <a href="http://lmgtfy.com/?q=why+am+i+so+stupid%3F">this link</a>.</body></html>"""


def gen(camera):
    if not(request):
        wma=watmark
        lgg=login
        cur=0
        while True:
            frame = camera.get_frame(wma,lgg,cur)
            cur+=1
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    global sameshit
    if sameshit:
        sameshit=False
        print(request)
        time.sleep(0.5)
        return Response(gen(VideoCamera()),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return """<html><body>Please follow <a href="http://lmgtfy.com/?q=why+am+i+so+stupid%3F">this link</a>.</body></html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)