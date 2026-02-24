# Spotify Lyrics Display GUI

A simple GUI application to fetch and display Spotify lyrics on an external device via serial communication.

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Spotify App Credentials
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app or use existing one
3. Add your client secret to `authorise.py` (line 78)
4. Make sure your redirect URI is set to `http://127.0.0.1:8080/callback`

### 3. Start the Express Server (for OAuth)
```bash
cd express
node main.js
```

### 4. Run the GUI
```bash
python gui.py
```

## Features

### Current Features ✅
- **Simple GUI**: Clean interface with Spotify branding
- **Login Button**: Opens browser for Spotify authentication
- **Track URL Input**: Paste Spotify track URLs
- **Lyrics Fetching**: Uses existing `syrics` library
- **Serial Communication**: Sends lyrics to hardware device
- **Real-time Status**: Shows what's happening in the status area

### Next Steps to Implement 🚀

1. **Complete OAuth Flow**:
   - Update `express/main.js` to handle the callback properly
   - Extract authorization code from callback
   - Exchange code for access token using `authorise.py`

2. **Replace Hardcoded Token**:
   - Update `spotifyFetch.py` to use OAuth tokens instead of hardcoded token
   - Implement token refresh when needed

3. **Enhanced Features**:
   - Currently playing track detection
   - Automatic lyric synchronization with Spotify playback
   - Multiple device support (different COM ports)
   - Playlist support
   - Lyrics preview in GUI

4. **Error Handling**:
   - Better serial port detection
   - Network error handling
   - Invalid URL validation

## File Structure

- `gui.py` - Main GUI application
- `authorise.py` - Spotify OAuth authentication
- `spotifyFetch.py` - Lyrics fetching (currently uses hardcoded token)
- `sender.py` - Serial communication to hardware
- `main.py` - Original main application
- `express/main.js` - OAuth server

## Usage

1. Start the Express server: `node express/main.js`
2. Run the GUI: `python gui.py`
3. Click "Login with Spotify" (will open browser)
4. Paste a Spotify track URL
5. Click "Fetch Lyrics"
6. Click "Start Display" to send lyrics to device

## Hardware Requirements

- Arduino or compatible device connected via serial
- COM11 port (update in `main.py` and `sender.py` if different)
- 16x2 LCD or similar display device

## Next Implementation Steps

To complete the full OAuth integration:

1. **Update Express callback handler**:
```javascript
app.get('/callback', (req, res) => {
  const code = req.query.code;
  // Send this code back to Python GUI
  // You can use file system, HTTP endpoint, or WebSocket
});
```

2. **Connect GUI to OAuth flow**:
   - Use the `authorise.py` `SpotifyAuth` class
   - Handle the authorization code exchange
   - Update GUI to show real login status

3. **Replace syrics token**:
   - Modify `spotifyFetch.py` to use OAuth tokens
   - May need to switch to official Spotify Web API

Would you like me to implement any of these next steps? 🎵