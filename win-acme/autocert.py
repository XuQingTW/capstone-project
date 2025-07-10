import subprocess
from pathlib import Path
import os
WACS = os.path.dirname(__file__) + "\\wacs.exe"

cert_print = os.path.dirname(__file__).replace("win-acme", "certs")

CMD = [
    str(WACS),
    "--source", "manual",
    "--host", "capstone-project.me",
    "--validation", "cloudflare",
    "--cloudflareapitoken", "XxAKRUg-WrC4lwihb0EpTNO_93J72pg-pDrj2oAb",
    "--store", "pemfiles",
    "--pemfilespath", cert_print,
    "--emailaddress", "evan060893@gmail.com",
    "--accepttos",
    "--verbose",
    "--closeonfinish",
]

print(CMD)

proc = subprocess.run(CMD, capture_output=True,encoding="utf-8", text=True, timeout=600)
print("Exit code:", proc.returncode)
print("STDOUT:\n", proc.stdout)
print("STDERR:\n", proc.stderr)
