import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
import requests
from spotifyFetch import getLyricsData
from sender import startLyricsDisplay

class SpotifyLyricsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Lyrics Display")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.access_token = None
        self.is_logged_in = False
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🎵 Spotify Lyrics Display", 
                               font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Login Section
        login_frame = ttk.LabelFrame(main_frame, text="Authentication", padding="10")
        login_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.login_btn = ttk.Button(login_frame, text="🔐 Login with Spotify", 
                                   command=self.spotify_login, style="Accent.TButton")
        self.login_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.login_status = ttk.Label(login_frame, text="Not logged in", 
                                     foreground="red")
        self.login_status.grid(row=0, column=1)
        
        # Track URL Section
        url_frame = ttk.LabelFrame(main_frame, text="Track Selection", padding="10")
        url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(url_frame, text="Spotify Track URL:").grid(row=0, column=0, sticky=tk.W)
        
        self.track_url_var = tk.StringVar()
        self.track_url_entry = ttk.Entry(url_frame, textvariable=self.track_url_var, width=50)
        self.track_url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Control Buttons Section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.fetch_btn = ttk.Button(control_frame, text="📥 Fetch Lyrics", 
                                   command=self.fetch_lyrics)
        self.fetch_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start Display", 
                                   command=self.start_display, state=tk.DISABLED)
        self.start_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop Display", 
                                  command=self.stop_display, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2)
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.status_text = tk.Text(status_frame, height=8, width=60)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.lyrics_data = None
        self.display_thread = None
        
        self.log_message("GUI initialized. Ready to connect to Spotify.", "INFO")
        
    def log_message(self, message, level="INFO"):
        """Add a message to the status text area"""
        self.status_text.insert(tk.END, f"[{level}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()
        
    def spotify_login(self):
        """Open browser to Spotify login"""
        try:
            # Check if Express server is running
            self.log_message("Checking if Express server is running...", "INFO")
            response = requests.get("http://127.0.0.1:8080/login", timeout=5)
            
            if response.status_code == 200:
                self.log_message("Express server is running. Opening login page...", "INFO")
                webbrowser.open("http://127.0.0.1:8080/login")
                
                # For now, we'll simulate a successful login
                # You can implement the callback handling here
                self.simulate_login_success()
            else:
                self.log_message("Express server responded but login failed", "ERROR")
                
        except requests.exceptions.ConnectionError:
            self.log_message("Express server not running! Please start it first:", "ERROR")
            self.log_message("cd express && node main.js", "INFO")
            messagebox.showerror("Server Error", 
                               "Express server not running!\n\nPlease run:\ncd express\nnode main.js")
        except Exception as e:
            self.log_message(f"Error connecting to server: {str(e)}", "ERROR")
            
    def simulate_login_success(self):
        """Simulate successful login (you'll implement OAuth callback handling)"""
        # This is where you'll implement the real OAuth token exchange
        self.is_logged_in = True
        self.login_status.config(text="✅ Logged in", foreground="green")
        self.login_btn.config(state=tk.DISABLED)
        self.log_message("Login successful! (Using existing token for now)", "SUCCESS")
        
    def fetch_lyrics(self):
        """Fetch lyrics from the provided track URL"""
        track_url = self.track_url_var.get().strip()
        
        if not track_url:
            messagebox.showerror("Error", "Please enter a Spotify track URL")
            return
            
        if not track_url.startswith("https://open.spotify.com/track/"):
            messagebox.showerror("Error", "Please enter a valid Spotify track URL")
            return
            
        try:
            self.log_message(f"Fetching lyrics for: {track_url[:50]}...", "INFO")
            self.lyrics_data = getLyricsData(track_url)
            
            if self.lyrics_data:
                self.log_message(f"Successfully fetched {len(self.lyrics_data)} lyric lines", "SUCCESS")
                self.start_btn.config(state=tk.NORMAL)
                
                # Show preview of first few lyrics
                preview = "Preview:\n"
                for i, line in enumerate(self.lyrics_data[:3]):
                    preview += f"  {line['startTime']:.1f}s: {line['words'][:30]}...\n"
                self.log_message(preview, "INFO")
            else:
                self.log_message("No lyrics found for this track", "WARNING")
                
        except Exception as e:
            self.log_message(f"Error fetching lyrics: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to fetch lyrics:\n{str(e)}")
            
    def start_display(self):
        """Start the lyrics display in a separate thread"""
        if not self.lyrics_data:
            messagebox.showerror("Error", "Please fetch lyrics first")
            return
            
        try:
            self.log_message("Starting lyrics display...", "INFO")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start lyrics display in a separate thread to prevent GUI freezing
            self.display_thread = threading.Thread(target=self.run_lyrics_display)
            self.display_thread.daemon = True
            self.display_thread.start()
            
        except Exception as e:
            self.log_message(f"Error starting display: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to start display:\n{str(e)}")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
    def run_lyrics_display(self):
        """Run the lyrics display (called in separate thread)"""
        try:
            startLyricsDisplay(self.lyrics_data)
            self.log_message("Lyrics display completed successfully!", "SUCCESS")
        except Exception as e:
            self.log_message(f"Error during lyrics display: {str(e)}", "ERROR")
        finally:
            # Re-enable buttons (must be done in main thread)
            self.root.after(0, self.reset_display_buttons)
            
    def reset_display_buttons(self):
        """Reset button states (called in main thread)"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def stop_display(self):
        """Stop the lyrics display"""
        # This is a simple implementation - you might want to add proper thread stopping
        self.log_message("Stop button pressed. Display will finish current lyrics.", "INFO")
        self.stop_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = SpotifyLyricsGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user")


if __name__ == "__main__":
    main()