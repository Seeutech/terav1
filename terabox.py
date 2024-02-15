import requests
import re


def getUrl(url):
    s = requests.session()
    r1 = s.get("https://teraboxdownloader.net/")

    re1 = re.search(r'<input type="hidden" id="token" value="([^"]*)">', r1.text)
    if not re1:
        return None
    token = re1.group(1)

    data = {"url": url, "token": token}
    r2 = s.post("https://teraboxdownloader.net/", json=data)
    res = r2.json()
    if (res["status"] != "success"):
        return None
    re2 = re.search(
        '<a id="download_file" style="background: orange" target="_blank" rel="noopener noreferrer" href="([^\"]*)">', res["message"])
    if not re2:
        return None
    url = re2.group(1)
    return url


