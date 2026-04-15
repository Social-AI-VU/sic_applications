# Droomrobot

## Installation
1) Clone this repository: ```git clone https://github.com/Social-AI-VU/Droomrobot.git```
2) Set-up virtual environment
3) Install dependencies: pip install --upgrade social_interaction_cloud[dialogflow,google-tts,openai-gpt,alphamini]
   1) On MacOS: pip install --upgrade 'social_interaction_cloud[dialogflow,google-tts,openai-gpt,alphamini]'

### Run with Start Script (Windows)
1. (Only once) Allow Script Execution via PowerShell
    1. Open (normal) PowerShell
    2. Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
2. Create shortcut on desktop (optional)
   1. Target: powershell.exe -ExecutionPolicy Bypass -File "C:\...\start-droomrobot.ps1"
   2. Start in: C:\...\droomrobot_python
3. Run start-droomrobot.ps1 directly or double click shortcut
4. To stop: ctrl-c in main terminal and after it closed, close any remaining window.

### Run without Start Script
1. In terminal: conf/redis/redis-server.exe conf/redis/redis.conf
2. In new terminal (within venv): run-dialogflow
3. In new terminal (within venv): run-gpt
4. (Optional in case of google-tts): run-google-tts
5. Create conf/droomrobot_default_settings.json
   1. Copy conf/droomrobot/default_settings_templase.json to conf/droomrobot/default_settings.json
   2. Update ip, id, and password of alphamini
   3. Update redis_ip → your device ip. Obtain e.g. via ipconfig command in terminal.
   4. Fine-tune the settings.
6. run droomrobot/droomrobot_gui.py

### Troubleshooting (Windows)
- ```RuntimeError: Could not start SIC on remote device```: Make sure the network you are on is marked as private. Add port 
6379 to inbound and outbound rules at Windows Defender Firewall with advanced security
- ```Failed to connect to mini device```: Add UDP ports 5353 and 6000-6010 to inbound rules at Windows Defender Firewall with advanced security
 
## Credits
_beach_waves.wav_ credits to [Benson_Arizona](https://freesound.org/people/Benson_Arizona/) at [freesound.org](https://freesound.org/). Original sound: [20250814_1150_Herm](https://freesound.org/people/Benson_Arizona/sounds/822525/)
