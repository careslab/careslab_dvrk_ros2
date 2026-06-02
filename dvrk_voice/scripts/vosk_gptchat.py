import argparse
import os
import queue
import sounddevice as sd
import vosk
import json
import sys
import threading
from playsound import playsound

import openai

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
picture_pub = rospy.Publisher('/assistant/take_picture', Bool, queue_size=1)
video_pub = rospy.Publisher('/assistant/take_video', Bool, queue_size=1)

q = queue.Queue()

#Chat GPT routines and limited choices. 

#define choice for chatgpt
choices = {'TR': 'davinci track right', 'TL': 'davinci track left', 'TM': 'davinci track middle', 
           'ST': 'davinci start', 'SX': 'davinci stop', 'KL': 'davinci keep left', 'KR': 'davinci keep right', 'FT': 'davinci find tools', 
           'TP': 'davinci take picture', 'SV': 'davinci start video', 'XV': 'davinci stop video', 'NV': 'Something not valid'}

#we limit the output of chattpt to only these commands. 
listofpossiblecommands = "TR TL TM ST SX KL KR FT TP SV XV NV"

#get the key
openai.api_key = os.getenv('OPENAI_API_KEY')

def AskGPT (prompt):
####################################################################
# This function takes a command like 'plese track the left tool' and 
# provides chatgpt some examples on how to answer the command.  Note
# that the return value is only one of the choices in the choices array
# above.   These choices should all have actions in the calling program.
#####################################################################
    completions = openai.ChatCompletion.create(
        model="gpt-4o",
        temperature = 0.7,
        messages=[
            #realtime training data... we can limit this to 3-4 times and then simplify the command to just the last part. 
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Given this phrase: 'Track the right tool' return the letters correspoing to the right answer: 'TR': 'track or follow the right tool', 'TL': 'track or follow the left' \
                'TM': 'track or follow the middle of the tools', 'ST': 'start or start moving camera', 'SX': 'stop or stop everything', 'KL': 'keep the left tool in view', 'KR': 'keep the right tool in view', 'FT': 'davinci find my tools', 'TP': 'take picture',\
                'SV': 'indication to start a video recording', 'XV': 'indications to stop the video recording', 'NV': 'something not valid or not understood"
            },
            {"role": "assistant", "content": "TR"},

            {"role": "user", "content": "Start playing the video"},
            {"role": "assistant", "content":  "SV"},

            {"role": "user", "content": "'Please take a picture of the scene'"}, 
            {"role": "assistant", "content":  "TP"},

            {"role": "user", "content": "'something not on the list of options or not valid has been said'"} ,
            {"role": "assistant", "content":  "NV"},

            #This is the acutial question to the chatgpt.
            {"role": "user", "content": prompt}    
        ]
    )
        
    #extract the index. The index is a two character string
    index = completions['choices'][0]['message']['content']

    #check to make sure that it is only 2 characters...otherwise, GPT may have returened a novel ;-)
    if (index in listofpossiblecommands) and len(index) == 2:
        print ("=====>")
        print(index) 
        return (choices [index])
    else:
        print("didn't understand")
        return (choices["NV"]) # NV is an index 

################################################################

    
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
            prevprompt =""
            prompt = ""
            cmd =""
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    #publish to run topic 
                    res = json.loads(rec.Result())
                    prompt = res['text']


                else:
                    res = json.loads(rec.PartialResult())
                    prevprompt = prompt
                    prompt = res['partial']
                    
                    #Ask GPT to interpret the user commands... only if the command has a pause and is 
                    # complete. Here we assume if the partial and the propmt are both blank, and the previous prompt is not
                    # blank, then a complete pharase has been issued.
                    #  
                    if ((res['partial'] == "") and (prompt == "") and (prevprompt != "")) :
                        #print("sending ===> to chatgpt")
                        print (prevprompt)
                        #We then ask GPT to figure out what the user wants to be done.
                        #the function returns an index to the list of items that are in choices.
                        cmd = AskGPT (prevprompt)
                        prevpromt ="" #wipe out the previous prompt
                        
                    
                    #execute the command

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
                        
                    elif cmd == "davinci take picture":
                        print("Taking picture")
                        picture_pub.publish(True)
                        voiceCommand_pub.publish("Da Vinci take picture")
                        playsound('sound95.wav')
                        picture_pub.publish(False)
                        rec.Reset()

                    elif cmd == "davinci start video":
                        print("Starting video")
                        video_pub.publish(True)
                        voiceCommand_pub.publish("Da Vinci begin recording")
                        playsound('sound95.wav')
                        rec.Reset()

                    elif cmd == "davinci stop video":
                        print("Stopping video")
                        video_pub.publish(False)
                        voiceCommand_pub.publish("Da Vinci end recording")
                        playsound('sound95.wav')
                        rec.Reset()
                  
                    elif cmd == "Something not valid":
                        print("Not valid")
                        playsound('repeat.wav')
                        rec.Reset()

                    else:
                        pass

                    #print(rec.PartialResult())
                #reset the command.
                cmd =""
                

                if dump_fn is not None:
                    dump_fn.write(data)

                    
            
except KeyboardInterrupt:
    print('\nDone')
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))

