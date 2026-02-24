from syrics.api import Spotify

def getLyricsData(trackUrl):
    sp_dc = "AQCU1mSpcpMymn8hKXVOqJW5aXE_f6zIGBMZO_lw3bBIt1lfbvcJDgw3e7OnkxCdnSQLR2WXwY8cpcPMc_XOP-aEvLh-r6nWJSX88YI1A9X-hgy8aIVtAtJ446BlN6bLerVZkw9DmZTjhsdVLtTrkipqnCtzWirm5AiY8HLn3NJvTlXy9nqt64doYZmRB_IRWHeW6CjVxn7VOEZTbg"
    sp = Spotify(sp_dc)
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
