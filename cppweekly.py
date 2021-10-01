import re
import io
import os
import matplotlib.pyplot as plt
import urllib.request
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from PIL import Image


class YouTube:
    def __init__(self, api_key):
        self.yt = build('youtube', 'v3', developerKey=api_key)

    def load_user_playlist(self, username):
        request = self.yt.channels().list(
            part='statistics,contentDetails',
            forUsername=username
        )
        return request.execute()

    def load_playlist_items(self, playlist_id, page_token):
        params = {
            'part': 'snippet,contentDetails',
            'maxResults': 50,
            'playlistId': playlist_id
        }
        if page_token:
            params['pageToken'] = page_token
        request = self.yt.playlistItems().list(**params)
        return request.execute()

    def load_all_playlist_items(self, playlist_id):
        items = []
        page_token = None
        while True:
            response = self.load_playlist_items(playlist_id, page_token)
            items.extend(response['items'])
            page_token = response.get('nextPageToken')
            if not page_token:
                return items

    def load_videos(self, ids):
        request = self.yt.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(ids)
        )
        return request.execute()

    def load_all_videos(self, ids):
        videos = []
        for batch in partition(ids, 50):
            videos.extend(self.load_videos(batch)['items'])
        return videos


def partition(items, size):
    result = []
    for i in range(0, len(items), size):
        result.append(items[i:i + size])
    return result


def parse_duration(dur):
    if m := re.match(r'^PT(\d+)M$', dur):
        return 60 * int(m.group(1))
    elif m := re.match(r'^PT(\d+)S$', dur):
        return int(m.group(1))
    elif m := re.match(r'^PT(\d+)M(\d+)S$', dur):
        return 60 * int(m.group(1)) + int(m.group(2))


def filter_episodes(videos):
    c = re.compile(r'C\+\+ Weekly - Ep ([0-9]+).*')
    episodes = []
    for v in videos:
        title = v['snippet']['title']
        m = c.match(title)
        if m:
            episodes.append((int(m.group(1)), v))
    episodes.sort(key=lambda v: v[0])
    return episodes


def linear_regression(x, y):
    coef = np.polyfit(x, y, 1)
    return np.poly1d(coef)


def plot_episode_durations(episodes, file_name):
    x = [e[0] for e in episodes]
    y = [parse_duration(e[1]['contentDetails']['duration']) for e in episodes]
    print_plot(x, y)
    fn = linear_regression(x, y)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x, y, 'bo', x, fn(x), '--k')
    ax.grid(True)
    ax.set(xlabel="Episode", ylabel="Seconds", title="C++ Weekly Episode Duration")
    plt.savefig(file_name)


def average_green(im):
    sum = 0
    cnt = 0
    rgb = im.convert('RGB')
    for x in range(im.width):
        for y in range(im.height):
            sum += rgb.getpixel((x, y))[1]
            cnt += 1
    return sum / cnt


def load_image_green(url):
    with urllib.request.urlopen(url) as f:
        im = Image.open(io.BytesIO(f.read()))
        return average_green(im)


def load_image_rgbs(urls, threads):
    futures = []
    with ThreadPoolExecutor(max_workers=threads) as exec:
        for url in urls:
            futures.append(exec.submit(load_image_green, url))
    return [f.result() for f in futures]


def print_plot(x, y):
    for n in range(len(x)):
        print(x[n], y[n])


def plot_episode_green_channels(episodes, rgbs, file_name):
    x = [e[0] for e in episodes]
    y = [rgb for rgb in rgbs]
    print_plot(x, y)
    fn = linear_regression(x, y)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x, y, 'bo', x, fn(x), '--k')
    ax.grid(True)
    ax.set(xlabel="Episode", ylabel="Green Channel", title="C++ Weekly Thumbnail Green Color Channel")
    plt.savefig(file_name)


def main():
    youtube = YouTube(os.environ['YT_API_KEY'])

    # get user upload playlist
    playlist = youtube.load_user_playlist('lefticus1')
    playlist_id = playlist['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # load all playlist items
    items = youtube.load_all_playlist_items(playlist_id)
    video_ids = [i['contentDetails']['videoId'] for i in items]

    # load playlist video
    videos = youtube.load_all_videos(video_ids)

    # filter to C++ Weekly episodes
    episodes = filter_episodes(videos)

    # remove 13-hour doom stream
    del episodes[213]

    # download episode thumbnails and sample rgb at pixel (0, height/5)
    urls = [e[1]['snippet']['thumbnails']['default']['url'] for e in episodes]
    rgbs = load_image_rgbs(urls, 10)

    # plots
    plot_episode_durations(episodes, 'cw_durations.png')
    plot_episode_green_channels(episodes, rgbs, 'cw_green.png')


if __name__ == '__main__':
    main()
