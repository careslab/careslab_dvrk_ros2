import os
import tempfile 
import sounddevice as sd
import soundfile as sf
import whisper 
import json
import sys
import threading
from playsound import playsound

from classification import Classification


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
# new commands publishers
draw_left_pub = rospy.Publisher('/assistant/draw_left', Bool, queue_size=1)
draw_right_pub = rospy.Publisher('/assistant/draw_right', Bool, queue_size=1)
clear_drawings_pub = rospy.Publisher('/assistant/clear_drawings', Bool, queue_size=1)
stop_drawing_pub = rospy.Publisher('/assistant/stop_drawing', Bool, queue_size=1)
blood_pressure_pub = rospy.Publisher('/assistant/blood_pressure', Bool, queue_size=1)
heart_rate_pub = rospy.Publisher('/assistant/heart_rate', Bool, queue_size=1)
pulse_oximeter_pub = rospy.Publisher('/assistant/pulse_oximeter', Bool, queue_size=1)
respiratory_rate_pub = rospy.Publisher('/assistant/respiratory_rate', Bool, queue_size=1)
body_temperature_pub = rospy.Publisher('/assistant/body_temperature', Bool, queue_size=1)

#library of choices
command_library = {'TR': 'davinci track right', 'TL': 'davinci track left', 'TM': 'davinci track middle', 
           'ST': 'davinci start', 'SX': 'davinci stop', 'ML': 'davinci keep left', 'MR': 'davinci keep right', 'FT': 'davinci find tools', 
           'TP': 'davinci take picture', 'SV': 'davinci start video', 'XV': 'davinci stop video', 'NV': 'Something not valid', 
#new commands
           'DL': 'davinci draw left', 'DR': 'davinci draw right', 'CX': 'davinci clear my drawings', 'DX': 'davinci stop drawing', 
           'BP': 'davinci blood pressure', 'HR': 'davinci heart rate', 'PO': 'davinci pulse oximeter', 
           'RR': 'davinci respiratory rate', 'BT': 'davinci body temperature'}

#we limit the output of chattpt to only these commands. 
listofpossiblecommands = "TR TL TM ST SX ML MR FT TP SV XV NV DL DR CX DX BP HR PO RR BT"
     
# Initialize the Classification model
clf=Classification()

# # Load Whisper model
whisper_model = whisper.load_model("base") # You can also use "tiny", "small", etc.

#Audio settings
samplerate = 16000
duration = 5  # seconds

# Main loop
try:
    print("#" * 80)
    print("Listening for voice commands. Press Ctrl+C to stop.")
    print("#" * 80)

    while True:
        # Record audio
        audio = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, samplerate)
            audio_path = f.name

        # Transcribe using Whisper
        result = whisper_model.transcribe(audio_path)
        prompt = result['text'].strip()

        # TEST 1
        print("Whisper transcription:", prompt)

        if not prompt:
            continue

        print("You said:", prompt)
        cmd = clf.handle_command(prompt)

        # TEST 2
        print("Command after classification:", cmd)

        #check to make sure the cmd is only two letters and convert it into an actual command
        if (cmd in listofpossiblecommands) and len(cmd) == 2:
            #print (f"=====> {cmd}")
            (command_library[cmd])
        else:
            print("Invalid command detected. Please try again.")

        # ROS command logic
        if cmd == "davinci start":
            print("Running autocamera")
            for topic in ['/assistant/clutch_and_move/run', '/assistant/joystick/run', '/assistant/oculus/run', '/assistant/clutchless/run']:
                rospy.Publisher(topic, Bool, latch=True, queue_size=1).publish(Bool(False))
            run_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci Start")
            playsound('sound95.wav')

            # TEST 3
            #print(f"[SUCCESS] Executed command: '{prompt}' -> '{cmd}'")

        elif cmd == "davinci stop":
            print("Stopping autocamera")
            run_pub.publish(False)
            voiceCommand_pub.publish("Da Vinci Stop")
            playsound('sound95.wav')

        elif cmd == "davinci track right":
            print("Tracking right")
            track_pub.publish("right")
            voiceCommand_pub.publish("Da Vinci track right")
            playsound('sound95.wav')

            # TEST 4
            #print(f"[SUCCESS] Executed command: '{prompt}' -> '{cmd}'")

        elif cmd == "davinci track left":
            print("Tracking left")
            track_pub.publish("left")
            voiceCommand_pub.publish("Da Vinci track left")
            playsound('sound95.wav')

        elif cmd == "davinci track middle":
            print("Tracking middle")
            track_pub.publish("middle")
            voiceCommand_pub.publish("Da Vinci track middle")
            playsound('sound95.wav')

        elif cmd == "davinci keep right":
            print("Keeping right")
            keep_pub.publish("right")
            voiceCommand_pub.publish("Da Vinci keep right")
            playsound('sound95.wav')

        elif cmd == "davinci keep left":
            print("Keeping left")
            keep_pub.publish("left")
            voiceCommand_pub.publish("Da Vinci keep left")
            playsound('sound95.wav')

        elif cmd == "davinci keep middle":
            print("Keeping middle")
            keep_pub.publish("middle")
            voiceCommand_pub.publish("Da Vinci keep middle")
            playsound('sound95.wav')

        elif cmd == "davinci find tools":
            print("Finding tools")
            findtools_pub.publish()
            voiceCommand_pub.publish("Da Vinci find my tools")
            playsound('sound95.wav')

        elif cmd == "davinci take picture":
            print("Taking picture")
            picture_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci take picture")
            playsound('sound95.wav')
            picture_pub.publish(False)

        elif cmd == "davinci start video":
            print("Starting video")
            video_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci begin recording")
            playsound('sound95.wav')

        elif cmd == "davinci stop video":
            print("Stopping video")
            video_pub.publish(False)
            voiceCommand_pub.publish("Da Vinci end recording")
            playsound('sound95.wav')

        elif cmd == "Something not valid":
            print("Not valid")
            playsound('repeat.wav')
#New commands logic
        elif cmd == "davinci draw left":
            print("Drawing left")
            draw_left_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci draw left")
            playsound('sound95.wav')

        elif cmd == "davinci draw right":
            print("Drawing right")
            draw_right_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci draw right")
            playsound('sound95.wav')

        elif cmd == "davinci clear my drawings":
            print("Clearing drawings")
            clear_drawings_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci clear my drawings")
            playsound('sound95.wav')

        elif cmd == "davinci stop drawing":    
            print("Stopping drawing")
            stop_drawing_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci stop drawing")
            playsound('sound95.wav')

        elif cmd == "davinci blood pressure":
            print("Taking blood pressure")
            blood_pressure_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci take blood pressure")
            playsound('sound95.wav')

        elif cmd == "davinci heart rate":
            print("Taking heart rate")
            heart_rate_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci take heart rate")
            playsound('sound95.wav')

        elif cmd == "davinci pulse oximeter":   
            print("Taking pulse oximeter")
            pulse_oximeter_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci take pulse oximeter")
            playsound('sound95.wav')

        elif cmd == "davinci respiratory rate":
            print("Taking respiratory rate")
            respiratory_rate_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci take respiratory rate")
            playsound('sound95.wav')

        elif cmd == "davinci body temperature":
            print("Taking body temperature")
            body_temperature_pub.publish(True)
            voiceCommand_pub.publish("Da Vinci take body temperature")
            playsound('sound95.wav')

except KeyboardInterrupt:
    print("\nExiting...")

except Exception as e:
    print("Error:", str(e))

