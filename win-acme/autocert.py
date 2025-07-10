import subprocess
from pathlib import Path
import os
WACS = os.path.dirname(__file__) + "\\wacs.exe"

cert_print = os.path.dirname(__file__).replace("win-acme", "certs")
SSL_API = os.environ.get('SSL_API')
CMD = [
    str(WACS),
    "--source", "manual",
    "--host", "capstone-project.me",
    "--validation", "cloudflare",
    "--cloudflareapitoken", SSL_API ,
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
