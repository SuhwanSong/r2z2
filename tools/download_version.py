import os
import sys
import json
import time
import requests

def get_chromium_binary_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchrome-linux.zip?alt=media"
    return url

def get_chromium_binary_name_position(position):
    name = f"{position}-chrome-linux.zip"
    return name

def get_chromium_driver_download_url(position):
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F{position}%2Fchromedriver_linux64.zip?alt=media"
    return url

def get_chromium_driver_name_position(position):
    name = f"{position}-chromedriver-linux64.zip"
    return name

def download(url, name, base="."):
    r = requests.request("GET", url)

    try:
        r.raise_for_status()
        with open(os.path.join(base, name), "wb") as f:
            for chunk in r:
                f.write(chunk)
        return True
    except:
        return False

def download_chromium_position(position):
    if not position:
        print("[-] Version is not correct :(")
        return 1

    url = get_chromium_binary_download_url(position)
    name = get_chromium_binary_name_position(position)
    try:
        ret = download(url, name)
    except:
        return 1
    if not ret:
        print("[-] No pre-built binary :(")
        return 1
   
    os.system("unzip " + name)
    os.system("mv chrome-linux " + position)
    os.system("rm -rf " + name)

    url = get_chromium_driver_download_url(position)
    name = get_chromium_driver_name_position(position)
    try:
        ret = download(url, name)
    except:
        return 1
    
    if not ret:
        print("[-] No pre-built binary :(")
        return 1

    os.system("unzip " + name)
    os.system("mv chromedriver_linux64/chromedriver " + position)
    os.system("rm -rf chromedriver_linux64 " + name)
    
    return 0
def get_commit_from_position(position):
    URL = 'https://crrev.com/' + position
    response = requests.get(URL)
    if response.status_code == 404:
        print(response.status_code)
        return 0
    else:
        a = 66
        b = 41
        print(response.text[a:a+b])
        return str(response.text[a:a+b])


def main():

    dir_list = os.listdir()
    dir_list.sort()
    start = int(sys.argv[1])

    pos = str(start)
    if not os.path.exists(pos): 
        try:
            commit = get_commit_from_position(pos)
            if commit == 0: return 0
            print("downloading " + pos)
            ret = download_chromium_position(pos)
        except:
            pass
    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)
