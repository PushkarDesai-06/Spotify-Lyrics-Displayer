from syrics.api import Spotify

def getLyricsData(trackUrl):
    sp = Spotify("AQAyiamOfjWxd8VAfAqrFqbB6HhKtudV9cjqALDeLNDVdpbzl2z3P75h_iOAsliO6-PlHW11EWNss2vkHlD0K3kTq10qxjTUsFYpL2a7Vc4gIDauIITHJ4tAFBbiRX7EU9EON-vpnLe5AqH5kCOyiNwC6rQuMzPo3LaEeQabcnKym_fb76kH_ZO1J_TIkP13QapnnKyOcOd-LrhVdaE")
    lyrics = sp.get_lyrics(trackUrl[31:])
    TimeValues = []
    
    data = lyrics['lyrics']['lines']
    
    for i in data:
        startTime = float(i['startTimeMs']) / 1000.00 #float
        words = i['words'] #string
        tempObj = {'startTime' : startTime , 'words' : words } 
        TimeValues.append(tempObj)
    
    for i in range(len(TimeValues) - 1 , 1 , -1):
        TimeValues[i]['startTime'] -= TimeValues[i-1]['startTime']
        
    return TimeValues
    
    
    # for i in lyrics['lyrics']['lines']:
    #     TIME_VALUES.append(i['startTimeMs'])
    
    # print(lyrics['lyrics'])
    # return [ TIME_VALUES , lyrics['lyrics'] ]


# getLyricsData()

