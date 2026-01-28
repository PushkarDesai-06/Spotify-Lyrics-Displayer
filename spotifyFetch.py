from syrics.api import Spotify

def getLyricsData(trackUrl):
    sp = Spotify("AQAyiamOfjWxd8VAfAqrFqbB6HhKtudV9cjqALDeLNDVdpbzl2z3P75h_iOAsliO6-PlHW11EWNss2vkHlD0K3kTq10qxjTUsFYpL2a7Vc4gIDauIITHJ4tAFBbiRX7EU9EON-vpnLe5AqH5kCOyiNwC6rQuMzPo3LaEeQabcnKym_fb76kH_ZO1J_TIkP13QapnnKyOcOd-LrhVdaE")
    lyrics = sp.get_lyrics(trackUrl[31:])
    lines = lyrics['lyrics']['lines']

    TimeValues = []
    for i in lines:
        startTime = float(i['startTimeMs']) / 1000.0  # absolute time in seconds
        words = i['words']
        TimeValues.append({'startTime': startTime, 'words': words})

    # Sanity check: make sure times are in order
    TimeValues = sorted(TimeValues, key=lambda x: x['startTime'])

    return TimeValues
