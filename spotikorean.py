import os
import re
import sys
import requests
import spotipy
import yt_dlp
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC, TRCK, TYER, error
from spotipy.oauth2 import SpotifyClientCredentials
from colorama import init, Fore, Style
import keyboard
import difflib
import threading

init(autoreset=True)

CLIENT_ID = 'fb2c1a715c394bfd9df77f91df996f72'
CLIENT_SECRET = '759c548fe96847669dba7eb35e8fa0d9'

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

stop_program = False
default_output_path = os.path.join(os.path.expanduser("~"), "Music")

def search_and_download_mp3(query, output_path):
    if not output_path:
        output_path = default_output_path

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        {
            'actions': [
                (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer, 'title', r'[/\\:*?"<>|]', '-'),
                (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer, 'title', r'(?i)\s*(lyrics?|color\s*coded)\s.*$', ''),
                (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer, 'title', r'(?i)\s*prod\.?\s.*$', ''),
                (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer, 'title', r'(?i)\s*(official\s*)?((performance\s*)?video|(music\s*)?video|mv|m-v|clip\s*(officiel\s*)?|(lifestyle\s*)?visualizer)\s*.*$', ''),
                (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer, 'title', r'(?i)\s*(feat\.?|featuring|ft\.?)\s.*$', ''),
                (yt_dlp.postprocessor.metadataparser.MetadataParserPP.replacer, 'title', r'(?i)\s*[\(\[]\s*$', ''),
            ],
            'key': 'MetadataParser',
            'when': 'pre_process',
        }],
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
    }

    manual_spotify_link = None
    youtube_search_query = query

    spotify_track_pattern = r"(https://open\.spotify\.com/(?:[^/]+/)?track/([a-zA-Z0-9]+))"
    spotify_track_match = re.search(spotify_track_pattern, query)

    if spotify_track_match:
        manual_spotify_link = spotify_track_match.group(1)
        track_id_from_regex = spotify_track_match.group(2)
        print(Fore.MAGENTA + f"Spotify link detected: {manual_spotify_link} (ID: {track_id_from_regex})")
        try:
            track_info = sp.track(track_id_from_regex)
            if track_info and track_info.get('name'):
                song_name = track_info['name']
                artists = " ".join([artist['name'] for artist in track_info['artists']])
                youtube_search_query = f"{song_name} {artists}"
                print(Fore.MAGENTA + f"Using Spotify info for YouTube search: '{youtube_search_query}'")
            else:
                print(Fore.YELLOW + f"Could not fetch Spotify track info for ID: {track_id_from_regex}. Using original query '{query}' for YouTube.")
        except spotipy.exceptions.SpotifyException as se:
            print(Fore.RED + f"Spotify API error for track ID {track_id_from_regex}: {se}. Using original query '{query}'.")
        except Exception as e:
            print(Fore.RED + f"Error processing Spotify link: {e}. Using original query '{query}'.")
    
    with YoutubeDL(options) as ydl:
        print(Fore.CYAN + f"Searching YouTube and downloading '{youtube_search_query}' as MP3...")
        try:
            info = ydl.extract_info(f"ytsearch1:{youtube_search_query}", download=True)
            if 'entries' in info and info['entries']:
                video_title_cleaned = info['entries'][0]['title']
                mp3_path = os.path.join(output_path, f"{video_title_cleaned}.mp3")

                if not os.path.exists(mp3_path):
                    print(Fore.RED + f"MP3 file {mp3_path} not found after download. Check yt-dlp logs or output directory.")
                    return None, None, None, manual_spotify_link
                return mp3_path, video_title_cleaned, info['entries'][0].get('channel'), manual_spotify_link
            else:
                print(Fore.RED + f"No results found on YouTube for '{youtube_search_query}'.")
                return None, None, None, manual_spotify_link
        except yt_dlp.utils.DownloadError as e:
            print(Fore.RED + f"yt-dlp download error for '{youtube_search_query}': {e}")
            return None, None, None, manual_spotify_link
        except Exception as e:
            print(Fore.RED + f"Unexpected error during YouTube download for '{youtube_search_query}': {e}")
            return None, None, None, manual_spotify_link

def format_spotify_release_date(sp_release_date, sp_release_date_precision):
    if not sp_release_date: return None
    if sp_release_date_precision == 'year':
        return sp_release_date[:4]
    elif sp_release_date_precision == 'month':
        return sp_release_date[:7]
    return sp_release_date

def extract_spotify_metadata(track_obj, provided_url=None):
    if not track_obj or not track_obj.get('name'):
        return None

    main_artist_id = track_obj['artists'][0]['id'] if track_obj.get('artists') else None
    main_artist_info = sp.artist(main_artist_id) if main_artist_id else None
    
    genres = main_artist_info.get('genres', []) if main_artist_info else []
    
    album_info = track_obj.get('album', {})
    release_date_raw = album_info.get('release_date')
    release_date_precision = album_info.get('release_date_precision')
    formatted_release_date = format_spotify_release_date(release_date_raw, release_date_precision)

    track_number = track_obj.get('track_number', 0)
    total_tracks = album_info.get('total_tracks', 0)
    
    cover_url = album_info['images'][0]['url'] if album_info.get('images') else None

    metadata = {
        'title': track_obj['name'],
        'artists_list': [artist['name'] for artist in track_obj.get('artists', [])],
        'artists': ';'.join(artist['name'] for artist in track_obj.get('artists', [])),
        'album': album_info.get('name', 'Unknown Album'),
        'release_date': formatted_release_date,
        'year': formatted_release_date.split('-')[0] if formatted_release_date else None,
        'track_number_on_total': f"{track_number:02d}/{total_tracks:02d}" if total_tracks > 0 else f"{track_number:02d}",
        'cover_url': cover_url,
        'track_id': track_obj['id'],
        'track_url': provided_url or track_obj.get('external_urls', {}).get('spotify'),
        'genres': ';'.join(g for g in genres)
    }
    print(Fore.GREEN + f"Spotify metadata found: {metadata['title']} by {metadata['artists']}")
    if metadata.get('track_url'): print(f"Track URL: {metadata['track_url']}")
    return metadata

def search_song_on_spotify(query_or_video_title, channel_if_no_link, manual_spotify_link):
    if manual_spotify_link:
        print(Fore.YELLOW + f"Using provided Spotify link: {manual_spotify_link}")
        if "track/" in manual_spotify_link:
            track_id = manual_spotify_link.split("track/")[1].split("?")[0]
            try:
                track = sp.track(track_id)
                return extract_spotify_metadata(track, manual_spotify_link)
            except spotipy.exceptions.SpotifyException as e:
                print(Fore.RED + f"Spotify API error for track ID {track_id}: {e}")
            except Exception as e:
                print(Fore.RED + f"Error fetching track {track_id} from Spotify API: {e}")
            return None
        else:
            print(Fore.RED + "Invalid Spotify track link format.")
            return None
    else:
        search_term = f'{query_or_video_title} {channel_if_no_link if channel_if_no_link else ""}'.strip()
        if not search_term:
            print(Fore.YELLOW + "Cannot search Spotify: No title/channel info from YouTube.")
            return None
            
        print(Fore.CYAN + f"Searching Spotify for: '{search_term}'")
        try:
            results = sp.search(q=search_term, type='track', limit=5)
        except spotipy.exceptions.SpotifyException as e:
            print(Fore.RED + f"Spotify API search error: {e}")
            return None
        except Exception as e:
            print(Fore.RED + f"Error during Spotify search: {e}")
            return None

        if results and results['tracks']['items']:
            tracks = results['tracks']['items']
            best_match, best_score = None, 0.0
            for track_item in tracks:
                similarity = difflib.SequenceMatcher(None, query_or_video_title.lower(), track_item['name'].lower()).ratio()
                score = similarity
                spotify_artists = [a['name'].lower() for a in track_item['artists']]
                channel_lower = channel_if_no_link.lower() if channel_if_no_link else ""
                if channel_lower and any(channel_lower in sa or sa in channel_lower for sa in spotify_artists):
                    score += 0.1 
                if score > best_score:
                    best_score, best_match = score, track_item
            
            if best_match and best_score > 0.5:
                print(Fore.BLUE + f"Best Spotify match (score: {best_score:.2f}): {best_match['name']}")
                return extract_spotify_metadata(best_match)
            else:
                print(Fore.YELLOW + f"No suitable match on Spotify for '{query_or_video_title}' (best score: {best_score:.2f}).")
        else:
            print(Fore.RED + f"No results found on Spotify for '{search_term}'.")
        return None

def add_metadata_to_mp3(mp3_path, metadata):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None: audio.add_tags()

        for tag_key in ['TIT2', 'TPE1', 'TALB', 'TDRC', 'TYER', 'TCON', 'TRCK', 'APIC']:
            audio.tags.delall(tag_key)

        if metadata.get('title'): audio.tags.add(TIT2(encoding=3, text=metadata['title']))
        if metadata.get('artists'): audio.tags.add(TPE1(encoding=3, text=metadata['artists']))
        if metadata.get('album'): audio.tags.add(TALB(encoding=3, text=metadata['album']))
        
        if metadata.get('release_date'):
            try:
                audio.tags.add(TDRC(encoding=3, text=str(metadata['release_date'])))
            except Exception as e:
                print(Fore.YELLOW + f"Warning: Could not set TDRC tag for release date '{metadata['release_date']}': {e}")
        
        if metadata.get('year'):
             try:
                audio.tags.add(TYER(encoding=3, text=str(metadata['year'])))
             except Exception as e:
                print(Fore.YELLOW + f"Warning: Could not set TYER tag for year '{metadata['year']}': {e}")

        if metadata.get('genres'): audio.tags.add(TCON(encoding=3, text=metadata['genres']))
        if metadata.get('track_number_on_total'): audio.tags.add(TRCK(encoding=3, text=metadata['track_number_on_total']))

        if metadata.get('cover_url'):
            try:
                print(Fore.BLUE + f"Downloading cover art from {metadata['cover_url']}...")
                response = requests.get(metadata['cover_url'], timeout=10)
                response.raise_for_status()
                mime_type = response.headers.get('Content-Type', 'image/jpeg')
                if not mime_type.startswith('image/'): mime_type = 'image/jpeg'
                
                audio.tags.add(APIC(encoding=3, mime=mime_type, type=3, desc='Cover', data=response.content))
                print(Fore.GREEN + "Cover art successfully added.")
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"Failed to download cover art: {e}")
            except Exception as e:
                print(Fore.RED + f"Error adding cover art: {e}")
        else:
            print(Fore.YELLOW + "No cover URL in metadata.")

        audio.save(v2_version=3)
        print(Fore.GREEN + "Metadata successfully updated in MP3 file.")
    except error as e:
        print(Fore.RED + f"Mutagen error processing MP3 tags: {e}")
    except Exception as e:
        print(Fore.RED + f"Unexpected error adding metadata: {e}")

def check_exit():
    global stop_program
    keyboard.wait("esc") 
    if not stop_program:
        stop_program = True
        print(Fore.RED + "\nEsc detected. Exiting after current operation or next prompt...")

def main_loop(current_output_path):
    global stop_program
    while not stop_program:
        print(Fore.YELLOW + "____________________________________________")
        try:
            query = input(Fore.YELLOW + "Enter song, keywords, YouTube/Spotify URL (or 'quit' to exit):\n").strip()
        except (EOFError, KeyboardInterrupt):
            print(Fore.RED + "\nInput interrupted. Exiting.")
            stop_program = True; break

        if stop_program: break
        if not query: print(Fore.RED + "Search cannot be empty."); continue
        if query.lower() == 'quit': stop_program = True; print(Fore.MAGENTA + "Quitting."); break

        mp3_path, video_title, channel, manual_spotify_link = search_and_download_mp3(query, current_output_path)
        
        if stop_program: break

        if mp3_path and os.path.exists(mp3_path):
            metadata = search_song_on_spotify(video_title, channel, manual_spotify_link)
            if metadata:
                add_metadata_to_mp3(mp3_path, metadata)
                print(Fore.GREEN + "MP3 downloaded and metadata applied successfully!")
            else:
                print(Fore.YELLOW + "MP3 saved. Spotify metadata not found/matched.")
        elif mp3_path:
            print(Fore.RED + f"Error: MP3 path ({mp3_path}) returned but file not found. Download might have failed.")
        else:
            print(Fore.RED + "Download failed or no video found.")
        
        if stop_program: break
    print(Fore.CYAN + "Program finished.")

if __name__ == "__main__":
    print(Fore.CYAN + Style.BRIGHT + "Spotify YouTube MP3 Downloader by khmertrap and nmqx")
    print(Fore.YELLOW + "Press 'Esc' (then Enter if at prompt) or 'Ctrl+C' to exit.")
    
    output_path_input = input(Fore.YELLOW + f"Output folder (default: {default_output_path}):\n").strip()
    chosen_output_path = os.path.expanduser(output_path_input) if output_path_input else default_output_path

    if not os.path.exists(chosen_output_path):
        try:
            os.makedirs(chosen_output_path)
            print(Fore.GREEN + f"Created output directory: {chosen_output_path}")
        except OSError as e:
            print(Fore.RED + f"Could not create {chosen_output_path}: {e}. Using default.")
            chosen_output_path = default_output_path
            if not os.path.exists(chosen_output_path): os.makedirs(chosen_output_path)

    print(Fore.CYAN + f"Downloads saved to: {chosen_output_path}")

    exit_thread = threading.Thread(target=check_exit, daemon=True)
    exit_thread.start()

    try:
        main_loop(chosen_output_path)
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"Critical error in main execution: {e}")
    finally:
        print(Fore.MAGENTA + "Exiting program...")