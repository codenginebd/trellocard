# trellocard

1. Create a virtualenv with python3.5+
2. Activate the virtualenv and install pip install -r requirements.txt
3. cd to the project directory
4. Run python trello_card.py

# How to build the installer
1. Install
PyInstaller==3.4
pywin32==224
2. To build the exe
pyinstaller --onefile trello_card.py
3. The dist directory will contain the exe.
4. You need to copy the config.json and mapping directory there to make it running
5. Double click on the exe and it should run