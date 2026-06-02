import argparse
import os
import queue
import sounddevice as sd
import vosk
import json
import sys
import threading
from playsound import playsound


import rospy
from std_msgs.msg import Empty
from std_msgs.msg import Bool
from std_msgs.msg import String
from std_msgs.msg import Float32
from std_msgs.msg import Int16

threading.Thread(target=lambda: rospy.init_node('dvrk_voice', disable_signals=True, anonymous=True)).start()

run_pub = rospy.Publisher('/assistant/autocamera/run', Bool, queue_size=1, latch=True)
track_pub = rospy.Publisher('/assistant/autocamera/track', String, queue_size=1, latch=True)
keep_pub = rospy.Publisher('/assistant/autocamera/keep', String, queue_size=1, latch=True)
findtools_pub = rospy.Publisher('/assistant/autocamera/find_tools', Empty, queue_size=1, latch=True)
innerZoom_pub = rospy.Publisher('/assistant/autocamera/inner_zoom_value', Float32, queue_size=1, latch=True)
outerZoom_pub = rospy.Publisher('/assistant/autocamera/outer_zoom_value', Float32, queue_size=1, latch=True)
saveEcm_pub = rospy.Publisher('/assistant/save_ecm_position', Int16, queue_size=1)
gotoEcm_pub = rospy.Publisher('/assistant/goto_ecm_position', Int16, queue_size=1)
voiceCommand_pub = rospy.Publisher('/voice_command', String, queue_size=1)

q = queue.Queue()

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-f', '--filename', type=str, metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-m', '--model', type=str, metavar='MODEL_PATH',
    help='Path to the model')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
args = parser.parse_args(remaining)

try:
    if args.model is None:
        args.model = "model"
    if not os.path.exists(args.model):
        print ("Please download a model for your language from https://alphacephei.com/vosk/models")
        print ("and unpack as 'model' in the current folder.")
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])

    model = vosk.Model(args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 4000, device=args.device, dtype='int16',
                            channels=1, callback=callback):
            print('#' * 80)
            print('Press Ctrl+C to stop the recording')
            print('#' * 80)

            rec = vosk.KaldiRecognizer(model, args.samplerate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    #publish to run topic 
                    res = json.loads(rec.Result())
                    cmd = res['text']
                    #print (cmd)

                else:
                    res = json.loads(rec.PartialResult())
                    cmd = res['partial']

                    if(cmd == "davinci start auto camera" or cmd == "davinci start"):

                        print("Running autocamera")
                        rospy.Publisher('/assistant/clutch_and_move/run', Bool, latch=True, queue_size=1).publish(Bool(False))
                        rospy.Publisher('/assistant/joystick/run', Bool, latch=True, queue_size=1).publish(Bool(False))
                        rospy.Publisher('/assistant/oculus/run', Bool, latch=True, queue_size=1).publish(Bool(False))
                        rospy.Publisher('/assistant/clutchless/run', Bool, latch=True, queue_size=1).publish(Bool(False))
                        run_pub.publish(True)
                        voiceCommand_pub.publish("Da Vinci Start")
                        playsound('sound95.wav')
                        rec.Reset()

                    elif(cmd == "davinci stop auto camera" or cmd == "davinci stop"):
                        print("Stopping autocamera")
                        run_pub.publish(False)
                        voiceCommand_pub.publish("Da Vinci Stop")
                        playsound('sound95.wav')
                        rec.Reset()

                    #publish to track topic 
                    elif(cmd == "davinci track right"):
                        print("Tracking right")
                        track_pub.publish("right")
                        voiceCommand_pub.publish("Da Vinci track right")
                        playsound('sound95.wav')
                        rec.Reset()

                    elif(cmd == "davinci track left"):
                        print("Tracking left")
                        track_pub.publish("left")
                        voiceCommand_pub.publish("Da Vinci track left")
                        playsound('sound95.wav')
                        rec.Reset()

                    elif(cmd == "davinci track middle"or \
                         cmd == "davinci track off"):
                        print("Tracking middle")
                        track_pub.publish("middle")
                        voiceCommand_pub.publish("Da Vinci track middle")
                        playsound('sound95.wav')
                        rec.Reset()

                    #publish to keep topic 
                    elif(cmd == "davinci keep right"):
                        print("Keeping right")
                        keep_pub.publish("right")
                        voiceCommand_pub.publish("Da Vinci keep right")
                        playsound('sound95.wav')
                        rec.Reset()

                    elif(cmd == "davinci keep left"):
                        print("Keeping left")
                        keep_pub.publish("left")
                        voiceCommand_pub.publish("Da Vinci keep left")
                        playsound('sound95.wav')
                        rec.Reset()

                    elif(cmd == "davinci keep middle" or \
                         cmd == "davinci keep off"):
                        print("Keeping middle")
                        keep_pub.publish("middle")
                        voiceCommand_pub.publish("Da Vinci keep middle")
                        playsound('sound95.wav')
                        rec.Reset()

                    #publish to find tools topic
                    elif(cmd == "davinci find tools" or \
                         cmd == "davinci find my tools"):
                        print("Finding tools")
                        findtools_pub.publish()
                        voiceCommand_pub.publish("Da Vinci find my tools")
                        playsound('sound95.wav')
                        rec.Reset()
                        
                    else:
                        pass

                    #print(rec.PartialResult())

                if dump_fn is not None:
                    dump_fn.write(data)

                    
            
except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
