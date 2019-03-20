import sys
import os
import requests
import private
import django
sys.path.append("ktube")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktube.settings")
django.setup()


class YouTube:
    API_BASE_URI = 'https://www.googleapis.com/youtube/v3/'
    API_KEY = private.API_KEY
    RESOURCE = 'videos'
    DEFAULT_PARAMS = {
        'key': API_KEY,
        'part': 'snippet',
        'maxResults': 50
    }

    def __init__(self, params={}):
        self.items = []
        self.united_items = []
        self.uri = self.API_BASE_URI+self.RESOURCE
        self.params = dict(self.DEFAULT_PARAMS)
        if params != {}:
            self.params.update(params)
        self.has_remaining_data = True

    def fetch_data(self):
        res = self.fetch_json()
        remaining_data_count = res['pageInfo']['totalResults']-res['pageInfo']['resultsPerPage']
        try:
            self.params['pageToken'] = res['nextPageToken']
        except KeyError:
            pass
        while remaining_data_count > 0:
            additional_res = self.fetch_json()
            res['items'] += additional_res['items']
            remaining_data_count -= res['pageInfo']['resultsPerPage']
            try:
                self.params['pageToken'] = additional_res['nextPageToken']
            except KeyError:
                pass
        return res['items']

    def fetch_items(self):
        res = self.fetch_json()
        if len(res['items']) != 0:
            self.items = res['items']
            self.has_remaining_data = True if len(res['items']) == self.params['maxResults'] else False
            if self.has_remaining_data:
                try:
                    self.params['pageToken'] = res['nextPageToken']
                except KeyError:
                    self.has_remaining_data = False
            return True
        else:
            return False

    def iterate_data(self):
        while self.fetch_items():
            for i in self.items:
                yield i
            if not self.has_remaining_data:
                break

    def fetch_json(self):
        res = requests.get(self.uri, params=self.params)
        return res.json()


class Videos(YouTube):
    RESOURCE = 'videos'

    def fetch_statistics(self, video_id):
        params = {
            'id': video_id,
            'part': 'snippet,statistics',
            'fields': 'items(snippet(channelId,channelTitle),statistics(viewCount,likeCount,dislikeCount,commentCount))'
        }
        self.params.update(params)
        res = self.fetch_json()
        return res['items'][0]


class Search(YouTube):
    RESOURCE = 'search'


class Playlists(YouTube):
    RESOURCE = 'playlists'


class PlaylistItems(YouTube):
    RESOURCE = 'playlistItems'


class Main:
    PLAYLISTS = private.PLAYLISTS

    def __init__(self):
        self.videos = []

    def fetch_data(self):
        for playlist in self.PLAYLISTS:
            params = {
                'playlistId': playlist,
                'part': 'snippet',
                'fields': 'pageInfo,nextPageToken,items(snippet(title,resourceId(videoId)))'
            }
            ytp = PlaylistItems(params)
            pi = ytp.fetch_data()
            for j in pi:
                jt = j['snippet']['title']
                if 'MV' in jt or 'M/V' in jt:
                    vi = j
                    ytv = Videos(params)
                    st = ytv.fetch_statistics(j['snippet']['resourceId']['videoId'])
                    vi['statistics'] = st['statistics']
                    vi['snippet'].update(st['snippet'])
                    self.videos.append(vi)
            print('Fetched '+playlist)

    def register_data(self):
        from vuefois.models import Video
        Video.objects.all().delete()
        print('Deleted old data.')
        for video in self.videos:
            Video.objects.create(video_id=video['snippet']['resourceId']['videoId'],
                                 title=video['snippet']['title'],
                                 channel_id=video['snippet']['channelId'],
                                 channel_name=video['snippet']['channelTitle'],
                                 view_count=int(video['statistics']['viewCount']))
        print('Registered new data.')

    def main(self):
        self.fetch_data()
        self.register_data()


def main():
    instance = Main()
    instance.main()


if __name__ == '__main__':
    main()
