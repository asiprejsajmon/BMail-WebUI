# BMail-WebUI
BMail WebUI is a extension to BMail that'll launch a small Flask server with MailTM based burner email python script on it.

BMail WebUI is a one-file simple script that'll launch a Flask server with clean and minimal UI for the BMail application. BMail is a simple python script that uses mailtm's api to get free email domains which the script than uses to generate free disposable burner email. BMail WebUI is a extension to this script which provides clean and minimalistic website ui for the script itself. The UI doesnt provide any more functions than the old script but it adds a aesthetic style to it and the convenience of it being usable on multiple devices while running on a server using something like tailscale.

The website runs on a public ip on the 8080 port. (you can change all this in the script) If you wish the server would run on a local ip, just edit the main.py script so the ip is 172.0.0.1 at the bottom of the script. 

Installation:

git clone https://github.com/asiprejsajmon/BMail-WebUI.git

python3 -m venv .venv

source .venv/bin/activate

python3 -m pip install flask mailtm

chmod +x start.sh && ./start 
OR 
python3 main.py
