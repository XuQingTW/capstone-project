import subprocess
import os
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

WACS = os.path.join(parent_dir, "win-acme", "wacs.exe")

cert_print = os.path.abspath(os.path.join(parent_dir, 'certs'))
SSL_API = os.environ.get("SSL_API")

if SSL_API is None:
    raise RuntimeError("請設定 SSL_API 環境變數")

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
    "--closeonfinish"
]

proc = subprocess.run(CMD, capture_output=True,encoding="utf-8", text=True, timeout=600)
print("Exit code:", proc.returncode)
print("STDOUT:\n", proc.stdout)
print("STDERR:\n", proc.stderr)
