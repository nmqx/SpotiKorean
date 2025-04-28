# spotikorean

A tool that lets you, by simply looking up a song, download the MP3 and automatically tag it with full metadata from Spotify.

---

## 📦 Requirements

- **Python** 3.8+
- **ffmpeg** installed and in your `PATH` (download the full build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/))
- **Python packages** (as pinned in `requirements.txt`):
  - `spotipy==2.23.0`
  - `yt-dlp==2023.9.24`
  - `mutagen==1.45.1`
  - `requests==2.31.0`
  - `colorama==0.4.6`
- **Additional package**:
  - `keyboard` (for ESC-to-exit support)
- **Spotify Developer Credentials** (client ID & secret)

---

## 🛠️ Installation

```bash
# Clone the repo
git clone https://github.com/nmqx/spotikorean.git
cd spotikorean

# Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install the keyboard listener
pip install keyboard
```

---

## ⚙️ Configuration

1. Open `spotikorean.py`.  
2. At the top, replace the empty placeholders with your Spotify credentials:

   ```python
   CLIENT_ID = 'your_spotify_client_id'
   CLIENT_SECRET = 'your_spotify_client_secret'
   ```

---

## 🚀 Usage

```bash
python spotikorean.py
```

1. **Output folder prompt**  
   - You’ll be asked to **“Specify output folder”** (default: `~/Music`).  
2. **Search prompt**  
   - Enter a **song name**, **keywords**, or a **full Spotify URL**.  
3. **Download & Tag**  
   - The script uses `yt-dlp` to search YouTube and download the best audio as MP3.  
   - It then queries Spotify to find the matching track (or uses your provided link), extracts metadata (title, artist(s), album, release date, track number, genre, cover art), and writes ID3 tags into the MP3 via `mutagen`.  
4. **Exit**  
   - Press **ESC** at any time to quit the program gracefully.

All downloaded and tagged files will appear in your chosen folder.

---

## ⚠️ Troubleshooting

- **ffmpeg not found**: Ensure `ffmpeg` binaries are in your system `PATH`.  
- **Keyboard listener issues**: On some systems, `keyboard` requires elevated privileges. Run the script as administrator/root or remove the ESC-check loop if unnecessary.  
- **No results found**: Check your search terms or try a direct Spotify URL.

---

## 🤝 Contributing

1. Fork this repository  
2. Create a feature branch: `git checkout -b feature/my-awesome-feature`  
3. Commit your changes: `git commit -m "Add some feature"`  
4. Push to your branch: `git push origin feature/my-awesome-feature`  
5. Open a Pull Request  

---

## 📄 License

This project does not include a license file. Please refer to the repository owner for usage permissions.
