## dvrk_voice - Voice assistant for the DVRK platform 

- ### [Installation](#installation-instructions)
- ### [Startup](#usage)
---
### Installation Instructions  
1. Clone this repository to your catkin workspace
2. Build
3. Could need to install the [autocamera](https://github.com/careslab/autocamera) and/or [dvrk_autocamera](https://github.com/careslab/dvrk_autocamera) packages as well
4. Conda also required

### Usage
1. Start daVinci
2. Open a Terminal and and paste `roslaunch autocamera test_hardware.launch`
   - Power On
   - Home the hardware
   - Select Clutch and Move
   - Verify Clutch and Move
3. Open a new Terminal and paste `rosrun dvrk_autocamera autocamera_control_node.py`
4. Open a new Terminal and paste `rosrun dvrk_assistant_bridge bridge`
5. Open a new Terminal and paste `conda activate vosk`
   - Navigate to dvrk_voice/scripts in your {catkin workspace}  `cd ~/{catkin workspace}/src/dvrk_voice/scripts`
   - List numbers of avaiable microphones `python test_mic_vad.py -l`
   - Check the list and find the microphone number {N}
   - `python test_mic_vad.py -d {N}`
   - Check functionality
