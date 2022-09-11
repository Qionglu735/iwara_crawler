
# -*- coding: utf-8 -*-

import HTMLParser
import os
import re
import requests
import sys
import time
import traceback

# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn virtualenv
# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn requests


USER_INFO = [
    # {
    #   "user_name": The name of iwara user, 
    #   "file_prefix": Add a prefix for all video files if needed,
    #   "download_index": Download the video by index in this list only. Leave it blank for all
    # }
    {"user_name": "Forget Skyrim.", "file_prefix": "Forget Skyrim", "download_index": [-1]},
    {"user_name": "嫖阿姨", "file_prefix": "P嫖阿姨", "download_index": [-1]},
    {"user_name": "491033063", "file_prefix": "S神经觉醒", "download_index": [-1]},
    {"user_name": "和颐雪", "file_prefix": "H和颐雪", "download_index": [-1]},
    # {"user_name": "miraclegenesismmd", "file_prefix": "MiracleGenesisMMD", "download_index": [-1]},
    {"user_name": "嫚迷GirlFans", "file_prefix": "M嫚迷GirlFans", "download_index": [-1]},
    {"user_name": "JUSWE", "file_prefix": "AlZ", "download_index": [-1]},
    # {"user_name": "三仁月饼", "file_prefix": "S三仁月饼", "download_index": [-1]},
    # {"user_name": "LTDEND", "file_prefix": "", "download_index": [-1]},
    # {"user_name": "Mister Pink", "file_prefix": "", "download_index": [29]},
    # {"user_name": "qimiaotianshi", "file_prefix": "", "download_index": [-1]},
    # {"user_name": "jvmpdark", "file_prefix": "", "download_index": [3]},
    # {"user_name": "EcchiFuta", "file_prefix": "", "download_index": [-1]},
    {"user_name": "水水..", "file_prefix": "S水水..", "download_index": [-1]},
    # {"user_name": "慕光", "file_prefix": "M慕光", "download_index": [-1]},
    {"user_name": "煜喵", "file_prefix": "Y煜喵", "download_index": [-1]},
    # {"user_name": "113458", "file_prefix": "Y113458", "download_index": [-1]},
    {"user_name": "腿 玩 年", "file_prefix": "T腿玩年", "download_index": [-1]},
    # {"user_name": "sugokunemui", "file_prefix": "sugokunemui", "download_index": [-1]},
    # {"user_name": "mister-pink", "file_prefix": "mister-pink", "download_index": [-1]},
    {"user_name": "二两牛肉面jd", "file_prefix": "E二两牛肉面", "download_index": [-1]},
    # {"user_name": "hisen", "file_prefix": "Hisen", "download_index": [-1]},
    {"user_name": "MMD_je", "file_prefix": "mmdje", "download_index": [-1, -2, -3]},
]

PROXIES = {
    # "https": "http://127.0.0.1:8080",
}
MAX_RETRY = 5  # Maximum retry time if download progress is broke. Try to change network or use a proxy instead.

IWARA_HOME = "https://ecchi.iwara.tv"  # Change to www for normal video (Are you sure :D)

success_list = list()
error_list = list()


def main(user_name, file_prefix, download_index):
    user_page_url = "{}/users/{}/videos".format(IWARA_HOME, requests.utils.quote(user_name))
    print(u"{} {}".format(user_name.decode("utf-8"), user_page_url))
    video_list = list()
    page_list = [0]
    html_parser = HTMLParser.HTMLParser()  # for unescape html charter, such as "&#039;"
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
            video_list.append((a.split("\"")[1], html_parser.unescape(a.split("\"")[-2]), ))
        time.sleep(1)
    video_list.reverse()
    print("Video List:")
    for i, video in enumerate(video_list):
        print(u"{} {}".format(i + 1, video[1]))
        video_list[i] += (i + 1,)
    print("-" * 80)

    download_list = list()
    if len(download_index) > 0:
        for index in download_index:
            if index > 0:
                download_list.append(video_list[index - 1])
            else:
                download_list.append(video_list[index])
    else:
        download_list = video_list[:]
        download_list.reverse()
    for i, video in enumerate(download_list):
        print(u"{} {} {}".format(video[2], video[1], IWARA_HOME + unicode(video[0])))
        video_info = requests.get(
            IWARA_HOME + "/api" + unicode(video[0]).replace("/videos/", "/video/"),
            proxies=PROXIES
        ).json()
        if len(video_info) == 0:
            print(u"Private.")
        else:
            for info in video_info:
                if info["resolution"] == "Source":
                    print("Source: https:{}".format(info["uri"]))
                    _file_prefix = u"{}.{:03d}.".format(
                        file_prefix.decode("utf-8") if file_prefix != "" else user_name.decode("utf-8"),
                        video[2],
                    )
                    _file_name = u"{}.mp4".format(
                        unicode(video[1]).replace("/", " ").replace("?", " ").replace("*", " "),
                    )
                    status = download_file_with_progress(_file_prefix, _file_name, "https:{}".format(info["uri"]))
                    if status is False:
                        error_list.append(_file_prefix + _file_name)
                    elif status == 2:
                        success_list.append(_file_prefix + _file_name)
                    break
        time.sleep(1)


def download_file_with_progress(file_prefix, file_name, url):
    total_length = -1
    retry = 0
    while total_length < 0:
        if retry > 0:
            if retry > MAX_RETRY:
                print("Too many retry. Aborted.")
                return False
            print("Connection Broken. Retry in {} seconds ...".format(retry * 5))
            time.sleep(retry * 5)
        try:
            total_length = int(requests.head(
                url,
                proxies=PROXIES
            ).headers.get("Content-Length", 1))
            time.sleep(1)
        except requests.exceptions.SSLError:
            # traceback.print_exc()
            retry += 1
        except requests.exceptions.ConnectionError:
            # traceback.print_exc()
            retry += 1

    print(u"Downloading to {}({})".format(file_prefix + file_name, size_display(total_length)))
    local_length = 0
    if os.path.exists(file_prefix + file_name):
        local_length = os.path.getsize(file_prefix + file_name)
        if local_length == total_length:
            print("Completed.")
            return 1
    else:
        # for some reason, file index is changed
        duplicated = [x.decode("gbk") for x in os.listdir(".") if x.decode("gbk").startswith(file_prefix)]
        for d in duplicated:
            print(u"Duplicated: {}".format(d))
            if "(duplicated)" not in d:
                os.rename(d, d.replace(".mp4", "(duplicated).mp4"))

    try:
        retry = 0
        while local_length < total_length:
            if retry > 0:
                if retry > MAX_RETRY:
                    print("Too many retry. Aborted.")
                    return False
                print("Connection Broken. Retry in {} seconds ...".format(retry * 5))
                time.sleep(retry * 5)
            headers = dict()
            if local_length > 0:
                headers = {
                    "Range": "bytes={}-".format(local_length)
                }
            with open(file_prefix + file_name, "ab" if local_length > 0 else "wb") as f:
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
            local_length = os.path.getsize(file_prefix + file_name)
            retry += 1
        if local_length == total_length:
            print("Completed.")
            return 2
        elif local_length > total_length:
            print("Tail {}".format(local_length - total_length))
            # os.remove(file_prefix + file_name)
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
        main(user["user_name"], user["file_prefix"], user["download_index"])
    if len(success_list):
        print(u"Success:\n{}".format("\n".join(success_list)))
    if len(error_list):
        print(u"Error:\n{}".format("\n".join(error_list)))
