
# -*- coding: utf-8 -*-

import os
import re
import requests
import sys
import time
import traceback

# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn virtualenv
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn requests


USER_INFO = [
    # {"user_name": The name of iwara user, "file_prefix": Add a prefix for all video files if needed}
    # {"user_name": "嫚迷GirlFans", "file_prefix": "M"},
    # {"user_name": "AlZ", "file_prefix": ""},
    # {"user_name": "chaiC_MMD", "file_prefix": ""},
    # {"user_name": "三仁月饼", "file_prefix": "S"},
    {"user_name": "LTDEND", "file_prefix": ""},
]
PROXIES = {
    "https": "http://127.0.0.1:8080"
}
TARGET_INDEX = []  # Download the video by index in this list only. Leave it blank for all.
MAX_RETRY = 5  # Maximum retry time if download progress is broke. Try to change network or use a proxy instead.

IWARA_HOME = "https://ecchi.iwara.tv"  # Change to www for normal video (Are you sure :D)


def main(user_name, file_prefix):
    user_page_url = "{}/users/{}/videos".format(IWARA_HOME, requests.utils.quote(user_name))
    print("{} {}".format(user_name, user_page_url))
    video_list = list()
    page_list = [0]
    for page_index in page_list:
        print("Reading Page No.{} ...".format(page_index + 1))
        page = requests.get(
            user_page_url,
            params={
                "page": page_index,
            },
            proxies=PROXIES
        ).text

        if page_index == 0:
            pager = re.search(r"<li class=\"pager-last last\">.+?</li>", page)
            if pager is not None:
                page_num = re.search(r"<li class=\"pager-last last\">.+?</li>", page) \
                    .group().split('\"')[-2].split("page=")[-1]
                page_list += range(1, int(page_num) + 1)

        a_list = re.findall(r"<a href=\"/videos/[a-z0-9?=]+\">.+?</a>", page)
        for a in a_list:
            if "img" not in a:
                continue
            video_list.append((a.split("\"")[1], a.split("\"")[-2], ))
        time.sleep(1)
    video_list.reverse()
    print("Video List:")
    for i, video in enumerate(video_list):
        print(u"{} {}".format(i + 1, video[1]))
    print("-" * 80)

    error_list = list()
    for i, video in enumerate(video_list):
        if len(TARGET_INDEX) > 0 and i + 1 not in TARGET_INDEX:
            continue
        print(u"{} {} {}".format(i + 1, video[1], IWARA_HOME + video[0]))
        video_info = requests.get(
            IWARA_HOME + "/api" + video[0].replace("/videos/", "/video/"),
            proxies=PROXIES
        ).json()
        if len(video_info) == 0:
            print("This one is Private.")
        else:
            for info in video_info:
                if info["resolution"] == "Source":
                    print("Source: https:{}".format(info["uri"]))
                    status = download_file_with_progress(
                        u"{}{}.{:03d}.{}.mp4".format(
                            file_prefix.decode("utf-8"),
                            user_name.decode("utf-8"),
                            (i + 1),
                            video[1].replace("/", " ").replace("?", " ")),
                        "https:{}".format(info["uri"]))
                    if status is not True:
                        error_list.append(i + 1)
                    break
        time.sleep(1)
    if len(error_list):
        print(error_list)


def download_file_with_progress(file_name, url):
    retry = 0

    local_length = 0
    if os.path.exists(file_name):
        local_length = os.path.getsize(file_name)

    try:
        total_length = int(requests.head(
            url,
            proxies=PROXIES
        ).headers.get("Content-Length", 1))
        time.sleep(1)
        print(u"Downloading to {}({})".format(file_name, size_display(total_length)))
        while local_length < total_length:
            if retry > 0:
                if retry > MAX_RETRY:
                    print("Too many retry. Aborted.")
                    break
                print("Connection Broken. Retry in {} seconds ...".format(retry * 5))
                time.sleep(retry * 5)
            headers = dict()
            if local_length > 0:
                headers = {
                    "Range": "bytes={}-".format(local_length)
                }
            with open(file_name, "ab" if local_length > 0 else "wb") as f:
                def process_data(_current_length):
                    if last_data is not None:
                        f.write(last_data)
                        _current_length += len(last_data)
                        progress = min(int(50 * (local_length + _current_length) / total_length), 50)
                        speed = _current_length * 1.0 / (time.clock() - start)
                        etc = (total_length - (local_length + _current_length)) * 1.0 / speed
                        sys.stdout.write("\r[{}{}] {}/{} {}/s ETC:{}".format(
                            "=" * progress, " " * (50 - progress),
                            size_display(local_length + _current_length), size_display(total_length),
                            size_display(speed), time_display(etc)
                        ))
                        sys.stdout.flush()
                    return _current_length

                current_length = 0
                last_data = None
                start = time.clock()
                with requests.get(
                        url,
                        stream=True,
                        headers=headers,
                        proxies=PROXIES
                ) as response:
                    if response.status_code == 416:  # Range Not Satisfiable
                        pass
                    else:
                        for data in response.iter_content(chunk_size=4096):
                            current_length = process_data(current_length)
                            last_data = data
                if local_length + current_length + len(last_data) == total_length:
                    process_data(current_length)
                sys.stdout.write("\n")
            local_length = os.path.getsize(file_name)
            retry += 1
        if local_length == total_length:
            print("Completed.")
            return True
        elif local_length > total_length:
            print("Tail {}".format(local_length - total_length))
            # os.remove(file_name)
            # print("Removed.")
        time.sleep(1)
    except requests.exceptions.SSLError:
        traceback.print_exc()
    except requests.exceptions.ConnectionError:
        traceback.print_exc()


def size_display(size):
    if size < 1024:
        return str(int(size)) + "B"
    elif size < 1024 * 1024:
        return str(round(size * 1.0 / 1024, 3)) + "K"
    elif size < 1024 * 1024 * 1024:
        return str(round(size * 1.0 / 1024 / 1024, 3)) + "M"
    else:
        return str(round(size * 1.0 / 1024 / 1024 / 1024, 3)) + "G"


def time_display(t):
    if t < 60:
        return str(round(t * 1.0, 1)) + "s"
    elif t < 60 * 60:
        return str(round(t * 1.0 / 60, 1)) + "m"
    else:
        return str(round(t * 1.0 / 60 / 60, 1)) + "h"


if __name__ == "__main__":
    for user in USER_INFO:
        main(user["user_name"], user["file_prefix"])
