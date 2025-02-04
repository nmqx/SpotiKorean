import os
import re
import requests
import spotipy
import yt_dlp
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC, TRCK, error
from spotipy.oauth2 import SpotifyClientCredentials
from colorama import init, Fore, Style
import keyboard
import difflib
import threading

init(autoreset=True)

# Spotify API credentials remplacez avec les votres
CLIENT_ID = ''
CLIENT_SECRET = ''

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

stop_program = False

def search_and_download_mp3(query, output_path):
    if not output_path:
        output_path = default_output_path

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'cookiefile': 'cookies.txt'if os.path.exists('cookies.txt') else None,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        # crampté regex (merci chat gpt)
        {
            'actions': [
                        (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer,
                        'title',
                        r'[/\\:*?"<>|]',
                        '-'),
                        (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer,
                        'title',
                        r'(?i)\s*(lyrics?|color\s*coded)\s.*$',
                        ''),
                        (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer,
                        'title',
                        r'(?i)\s*prod\.?\s.*$',
                        ''),
                        (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer,
                        'title',
                        r'(?i)\s*(official\s*)?((performance\s*)?video|(music\s*)?video|mv|m-v|clip\s*(officiel\s*)?|(lifestyle\s*)?visualizer)\s*.*$',
                        ''),
                        (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer,
                        'title',
                        r'(?i)\s*(feat\.?|featuring|ft\.?)\s.*$',
                        ''),
                        (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer,
                        'title',
                        r'(?i)\s*[\(\[]\s*$',
                        ''),
                        ],
            'key': 'MetadataParser',
            'when': 'pre_process',
        }
        ],
    }

    with YoutubeDL(options) as ydl:
        manual_spotify_link = None
        if "https://open.spotify.com/" in query:
            parts = query.split()
            for part in parts:
                if part.startswith("https://open.spotify.com/"):
                    manual_spotify_link = part
                    query = query.replace(part, "").strip()
        print(Fore.CYAN + f"Searching and downloading '{query}' as MP3 from YouTube...")
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        if 'entries' in info and info['entries']:
            video_title = info['entries'][0]['title']
            mp3_path = os.path.join(output_path, f"{video_title}.mp3")
            return mp3_path, video_title, info['entries'][0]['channel'], manual_spotify_link
        else:
            print(Fore.RED + "No results found on Youtube.")
            return None, None, None, None

def search_song_on_spotify(query, video_title, channel, manual_spotify_link):
    if not manual_spotify_link:
        results = sp.search(q=f'{video_title} {channel}', type='track', limit=3)
        if 'tracks' in results and 'items' in results['tracks'] and results['tracks']['items']:
            tracks = results['tracks']['items']
            best_match = None
            best_similarity = 0
            for track in tracks:
                track_title = track['name']
                similarity = difflib.SequenceMatcher(None, video_title.lower(), track_title.lower()).ratio() #because sometimes spotify take a song which has nothing to do with what you look for by searching in the lyri
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = track

            if best_match:
                track = best_match
                main_artist_id = track['artists'][0]['id']
                main_artist_info = sp.artist(main_artist_id)
                track_number = track['track_number']
                total_tracks = track['album']['total_tracks']
                genres = main_artist_info.get('genres', []) #we actually get the genres of the main artist songs because spotify links genres to artists and not a specific song
                metadata = { #you can add other metadata if you want
                    'title': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'artists': ';'.join(artist['name'] for artist in track['artists']),
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date'],
                    'release_date': track['album']['release_date'],
                    'track_number_on_total': f"{track_number:02d}/{total_tracks:02d}",
                    'cover_url': track['album']['images'][0]['url'],
                    'track_id': track['id'],
                    'track_url': track['external_urls']['spotify'],
                    'genres': ';'.join(genres for genres in genres)
                }
                print(Fore.GREEN + f"Found on Spotify: {metadata['title']} by {metadata['artists']}")
                print(f"Track URL: {metadata['track_url']}")
                return metadata
        else:
            print(Fore.RED + "No results found on Spotify.")
            return None
    else:
        print(Fore.YELLOW + f"Spotify link detected: {manual_spotify_link}.")
        if "track/" in manual_spotify_link:
            track_id = manual_spotify_link.split("track/")[1].split("?")[0]
            track = sp.track(track_id)
            if track['name']:
                main_artist_id = track['artists'][0]['id']
                main_artist_info = sp.artist(main_artist_id)
                track_number = track['track_number']
                total_tracks = track['album']['total_tracks']
                genres = main_artist_info.get('genres', [])
                metadata = {
                    'title': track['name'],
                    'artists': [artist['name'] for artist in track['artists']],
                    'artists': ';'.join(artist['name'] for artist in track['artists']),
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date'],
                    'track_number': track['track_number'],
                    'total_tracks': track['album']['total_tracks'],
                    'track_number_on_total': f"{track_number:02d}/{total_tracks:02d}",
                    'cover_url': track['album']['images'][0]['url'],
                    'track_id': track_id,
                    'track_url': manual_spotify_link,
                    'genres': ';'.join(genres for genres in genres)
            }
                print(Fore.GREEN + f"Found on Spotify: {metadata['title']} by {metadata['artists']}")
                return metadata
        else:
            print(Fore.RED + "No results found on Spotify.")
            return None


def add_metadata_to_mp3(mp3_path, metadata):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=metadata['title']))
        audio.tags.add(TPE1(encoding=3, text=metadata['artists']))
        audio.tags.add(TALB(encoding=3, text=metadata['album']))
        audio.tags.add(TDRC(encoding=3, text=metadata['release_date']))
        audio.tags.add(TCON(encoding=3, text=metadata['genres']))
        audio.tags.add(TRCK(encoding=3, text=metadata['track_number_on_total']))

        response = requests.get(metadata['cover_url'])
        if response.status_code == 200:
            audio.tags.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=response.content
            ))
        else:
            print(Fore.RED + "Failed to download cover.")

        audio.save()
        print(Fore.GREEN + "Metadata successfully added to the MP3 file.")
    except error as e:
        print(Fore.RED + f"An error occurred while processing the MP3 file: {e}")
        exit()

def check_exit():
    global stop_program
    while not stop_program:
        if keyboard.is_pressed("esc"):
            stop_program = True
            print(Fore.RED + "\nEsc detected. Exiting the program...")
            break
    
def main():
    while True:
        exit_thread = threading.Thread(target=check_exit, daemon=True)
        exit_thread.start()
        while not stop_program: #bugué répare wollah c'est chiant gros
            query = input(Fore.YELLOW + "____________________________________________\nEnter a song name, keywords or URL to search (optional: manually choose the spotify link):\n").strip()
            if query:
                mp3_path, video_title, channel, manual_spotify_link = search_and_download_mp3(query, output_path)
                if os.path.exists(mp3_path):  
                    metadata = search_song_on_spotify(query, video_title, channel, manual_spotify_link)
                    if metadata:
                        add_metadata_to_mp3(mp3_path, metadata)
                        print(Fore.GREEN + "All done! Your MP3 file has been updated with metadata and renamed.")
                    else:
                        print(Fore.RED + "Metadata not found on Spotify. Skipping metadata addition.")
                else:
                    print(f"File not found at {mp3_path}")
            else:
                print(Fore.RED + "Error: Search cannot be empty.")
                return
        sys.exit(0)
    #except Exception as e:
            #print(Fore.RED + f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + "Welcome to the Spotify YouTube MP3 Downloader CLI v1 by Nmqx & khmertrap")
    default_output_path = os.path.join(os.path.expanduser("~"), "Music")
    output_path = input(Fore.YELLOW + f"Specify output folder (default: {default_output_path}):\n").strip()
    main()
