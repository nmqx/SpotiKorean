import os
import re
import requests
import spotipy
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC, error
from spotipy.oauth2 import SpotifyClientCredentials
from colorama import init, Fore, Style

init(autoreset=True)

# Spotify API credentials
CLIENT_ID = ''
CLIENT_SECRET = ''

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

def search_and_download_mp3(query, output_path="downloads"):
    options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    with YoutubeDL(options) as ydl:
        print(Fore.CYAN + f"Searching and downloading '{query}' as MP3 from YouTube...")
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        downloaded_title = info['entries'][0]['title']
        downloaded_mp3_path = os.path.join(output_path, f"{downloaded_title}.mp3")
        print(Fore.GREEN + f"Download complete. MP3 saved as '{downloaded_title}.mp3'")
        return downloaded_mp3_path

def search_song_on_spotify(query):
    results = sp.search(q=query, type='track', limit=1)
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        metadata = {
            'title': track['name'],
            'artist': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'cover_url': track['album']['images'][0]['url'],
            'track_id': track['id']
        }
        print(Fore.GREEN + f"Found on Spotify: {metadata['title']} by {metadata['artist']}")
        return metadata
    else:
        print(Fore.RED + "No results found on Spotify.")
        exit()

def download_cover_art(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

def add_metadata_to_mp3(mp3_path, metadata, cover_filename):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()

        audio.tags.add(TIT2(encoding=3, text=metadata['title']))
        audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
        audio.tags.add(TALB(encoding=3, text=metadata['album']))
        audio.tags.add(TDRC(encoding=3, text=metadata['release_date']))

        with open(cover_filename, 'rb') as cover:
            audio.tags.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=cover.read()
            ))

        audio.save()
        print(Fore.GREEN + "Metadata successfully added to the MP3 file.")
    except error as e:
        print(Fore.RED + f"An error occurred while processing the MP3 file: {e}")
        exit()

def rename_mp3_file(mp3_path, new_title):
    folder, old_name = os.path.split(mp3_path)
    new_name = f"{new_title.replace(' ', '_')}.mp3"
    new_path = os.path.join(folder, new_name)
    os.rename(mp3_path, new_path)
    print(Fore.CYAN + f"MP3 file renamed to: {new_name}")
    return new_path

def main():
    print(Fore.CYAN + Style.BRIGHT + "Welcome to the Spotify YouTube MP3 Downloader CLI v1 by Nmqx")
    query = input(Fore.YELLOW + "Enter the song name or keywords to search: ")
    
    mp3_path = search_and_download_mp3(query)
    metadata = search_song_on_spotify(query)
    
    cover_filename = f"cover_{metadata['track_id']}_{metadata['title'].replace(' ', '_')}.jpg"
    download_cover_art(metadata['cover_url'], cover_filename)
    
    add_metadata_to_mp3(mp3_path, metadata, cover_filename)
    rename_mp3_file(mp3_path, metadata['title'])

    print(Fore.GREEN + "All done! Your MP3 file has been updated with metadata and renamed.")

if __name__ == "__main__":
    main()
