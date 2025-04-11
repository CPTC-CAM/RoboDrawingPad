# Robo Drawing Pad
The first version of this application creates a Python GUI for the user to draw on a Canvas.
While drawing the points are recorded and will then be streamed to a UR5cb3 using Wandelbots NOVA
mimicking the way the user drew their text.

## Prerequisites
- Run `pip install -r requirements.txt`
- Create a python virtual environment `python -m venv myvirtualenv
    - Choose the new venv as the Python interpreter in VS Code
- Local or cloud instance of NOVA
    - If running locally via Hyper-V, get IP using `get-vm | ?{$_.State -eq "Running"} | select -ExpandProperty networkadapters | select vmname, macaddress, switchname, ipaddresses | ft -wrap -autosize` in elevated PowerShell