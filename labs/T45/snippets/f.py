import os
from ncclient import manager

with manager.connect(host=os.environ["HOST"], port=830, username=os.environ["USER"],
                     password=os.environ["PASS"], hostkey_verify=False) as m:
    for capability in m.server_capabilities:
        print(capability)
    reply = m.get_config(source="running")
    print(reply.data_xml[:200])
