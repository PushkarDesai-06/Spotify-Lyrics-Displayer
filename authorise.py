import requests
import base64
import urllib.parse
from datetime import datetime, timedelta
import json
import os
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SpotifyAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        
    def get_auth_url(self, scopes=None):
        """Generate the Spotify authorization URL"""
        if scopes is None:
            scopes = ['user-read-private', 'user-read-email', 'user-read-currently-playing']
            
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'state': 'spotify-lyrics-display'  # You might want to generate a random state
        }
        
        auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(params)
        return auth_url
    
    def exchange_code_for_token(self, authorization_code):
        """Exchange authorization code for access token"""
        token_url = 'https://accounts.spotify.com/api/token'
        
        # Prepare the authorization header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)
            self.expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Save token to file for persistence
            self.save_token_to_file()
            return True
        else:
            print(f"Error exchanging code: {response.status_code} - {response.text}")
            return False
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return False
            
        token_url = 'https://accounts.spotify.com/api/token'
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Update refresh token if provided
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
                
            # Calculate new expiration time
            expires_in = token_data.get('expires_in', 3600)
            self.expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self.save_token_to_file()
            return True
        else:
            print(f"Error refreshing token: {response.status_code} - {response.text}")
            return False
    
    def is_token_valid(self):
        """Check if the current token is valid"""
        if not self.access_token or not self.expires_at:
            return False
        return datetime.now() < self.expires_at
    
    def get_valid_token(self):
        """Get a valid access token, refreshing if necessary"""
        if self.is_token_valid():
            return self.access_token
            
        if self.refresh_token and self.refresh_access_token():
            return self.access_token
            
        return None
    
    def save_token_to_file(self, filename='spotify_tokens.json'):
        """Save tokens to a file for persistence"""
        token_data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(token_data, f)
            print(f"Tokens saved to {filename}")
        except Exception as e:
            print(f"Error saving tokens: {e}")
    
    def load_token_from_file(self, filename='spotify_tokens.json'):
        """Load tokens from file"""
        if not os.path.exists(filename):
            return False
            
        try:
            with open(filename, 'r') as f:
                token_data = json.load(f)
                
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            expires_at_str = token_data.get('expires_at')
            if expires_at_str:
                self.expires_at = datetime.fromisoformat(expires_at_str)
                
            print(f"Tokens loaded from {filename}")
            return True
            
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False
    
    def get_user_profile(self):
        """Get current user's profile (for testing authentication)"""
        token = self.get_valid_token()
        if not token:
            return None
            
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting user profile: {response.status_code} - {response.text}")
            return None

    def login_interactive(self, scopes=None, token_file='spotify_tokens.json'):
        """Full interactive OAuth login flow."""
        if os.path.exists(token_file):
            self.load_token_from_file(token_file)
            token = self.get_valid_token()
            if token:
                print("Loaded saved token.")
                return token

        if scopes is None:
            scopes = [
                'user-read-private',
                'user-read-email',
                'user-read-playback-state',
                'user-read-currently-playing',
            ]
        auth_url = self.get_auth_url(scopes)

        # 3. Start local callback server to capture the code
        auth_code_holder = [None]
        server_done = threading.Event()

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # silence server logs

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                if 'code' in params:
                    auth_code_holder[0] = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<h2>Login successful! You can close this tab.</h2>')
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'<h2>Login failed : no code received.</h2>')
                server_done.set()

        parsed_redirect = urllib.parse.urlparse(self.redirect_uri)
        port = parsed_redirect.port or 8080
        server = HTTPServer(('127.0.0.1', port), CallbackHandler)

        # 4. Open browser and wait
        print(f"\nOpening Spotify login in your browser...")
        print(f"If it doesn't open, visit:\n  {auth_url}\n")
        webbrowser.open(auth_url)

        server_thread = threading.Thread(target=server.handle_request)
        server_thread.start()
        server_done.wait(timeout=120)
        server.server_close()

        code = auth_code_holder[0]
        if not code:
            print("Login timed out or was cancelled.")
            return None

        # 5. Exchange code for token
        if self.exchange_code_for_token(code):
            print("Login successful!")
            return self.access_token
        return None

# Credentials are loaded from .env — do not hardcode here
import dotenv as _dotenv
_dotenv.load_dotenv()

SPOTIFY_CLIENT_ID     = os.environ.get("CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI  = os.environ.get("REDIRECT_URI", "http://127.0.0.1:8080/callback")

def create_spotify_auth():
    """Create and return a SpotifyAuth instance"""
    return SpotifyAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI
    )

# For testing
if __name__ == "__main__":
    auth = create_spotify_auth()
    
    # Try to load existing tokens
    auth.load_token_from_file()
    
    if auth.is_token_valid():
        print("Valid token found!")
        profile = auth.get_user_profile()
        if profile:
            print(f"Logged in as: {profile['display_name']}")
    else:
        print("No valid token found. You need to complete the OAuth flow.")
        print("Authorization URL:")
        print(auth.get_auth_url())
