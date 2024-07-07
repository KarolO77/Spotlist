from datetime import datetime
import sys
import requests
from time import sleep
from bs4 import BeautifulSoup


def get_artist_id(artist):
    url = "https://www.setlist.fm/search?query=" + artist.replace(' ','+')
    search_for_artist_page = requests.get(url)
    search_for_artist_html = BeautifulSoup(search_for_artist_page.content, "html.parser")
    
    r = search_for_artist_html.find_all("div", {"class": "details"})
    r = r[0].find_all("a")[0]['href']
    artist_id = r[9:-5]

    return artist_id
    
def get_artists_setlist(artist_id, year=None):
    if year:
        present_year = year
    else:
        present_year = datetime.now().year

    url = f"https://www.setlist.fm/stats/average-setlist/{artist_id}.html?year={present_year}"

    setlist_page = requests.get(url)
    setlist_html = BeautifulSoup(setlist_page.content, "html.parser")

    r = setlist_html.find_all("div", {"class": "songPart"})
    setlist = []
    for i in r:
        song = i.contents[1]
        title = song.text
        setlist.append(title)
        
    if len(setlist) < 6:
        return get_artists_setlist(artist_id, year=present_year-1)
    return setlist
 
def save_artists_setlist(setlist, artist):
    with open("setlist.txt", "w", encoding="UTF-8") as f:
        f.write(f"{artist}\n")
        for title in setlist:
            f.write(f"{title}\n")

if __name__ == "__main__":
    artist = sys.argv[1]
    artist_id = get_artist_id(artist=artist)
    setlist = get_artists_setlist(artist_id)
    save_artists_setlist(setlist, artist)