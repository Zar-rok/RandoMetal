#!/usr/bin/env python3
# -*- coding: utf8 -*-

import sys
import urllib
import webbrowser
import argparse

from bs4 import BeautifulSoup
import requests

URL_RANDOM = "https://www.metal-archives.com/band/random"
glob_verbose = False
glob_print_page = False

def clean_name(name):
  """ Clean the caracters who are not decoded.  """
  
  name = urllib.parse.unquote(name)
  name = name.replace('_', ' ')
  return name  

def get_name_id(html):
  """
  Get the name and the id of the band corresponding to the html page.
  """

  raw_data = BeautifulSoup(html, "html.parser").find('h1', {"class": 'band_name'})
  raw_data = raw_data.find('a').get('href')
  raw_data = str(raw_data).split('/', 5)
  name = raw_data[4]
  ide = raw_data[5]

  return name, ide

def get_cd(ide):
  """
  Take an id and return the name of the newest album/demo/single of a band.
  """

  cd = None
  raw_data  = []
  class_word = ["demo", "single", "album", "other"]
  url_cd = "https://www.metal-archives.com/band/discography/id/" + str(ide) + "/tab/all"

  html = requests.get(url_cd).content
  for i in range(len(class_word)):
    raw_data += BeautifulSoup(html, "html.parser").findAll('a', {"class" :class_word[i]})

  try:    
    cd = ''.join(raw_data[(len(raw_data))-1].findAll(text=True))
  except IndexError:
    print("[!] No album for the band.", file=sys.stderr)

  return cd

def get_related_links(html):
  """
  Take the link in the 'Related links' onglet of archive-metal.
  """

  url = None
  raw_data = BeautifulSoup(html, "html.parser").find('a', {"title": "Related links"})

  if raw_data is not None:
    url = str(raw_data['href'])
  else:
    print("[!] No related link for this band.", file=sys.stderr)

  return url


def get_music_link(html, name):
  """
  Extract links
  """

  i = 0
  raw_data = []
  music_link = []
  title_list = ["Go to: Myspace", "Go to: Myspace Page", "Go to: Soundcloud", "Go to: Youtube", "Go to: Youtube Page", "Go to: Bandcamp", "Go to: MySpace", "Go to: MySpace Page", "Go to: SoundCloud", "Go to: YouTube", "Go to: YouTube Page", "Go to: YouTube Channel", "Go to: BandCamp", "Go to: "+name+" @ Myspace", "Go to: "+name+" @ Soundcloud", "Go to: "+name+" @ youtube", "Go to: "+name+" @ Bandcamp", "Go to: "+name+" @ MySpace", "Go to: "+name+" @ SoundCloud", "Go to: "+name+" @ youTube", "Go to: "+name+" @ BandCamp"]

  while (raw_data is None) or (i < (len(title_list))):
    raw_data += BeautifulSoup(html, "html.parser").findAll('a', {"title": title_list[i]})        
    i += 1        

  for j in range(len(raw_data)):
    music_link.append(raw_data[j].get('href'))

  return music_link

def chose_link(list_link):
  """
  Function who return musical link
  """

  site_order = ["bandcamp", "soundcloud", "youtube", "myspace"]

  for site in site_order:
    for link in list_link:
      if site in link:
        return link
  
  return None

def get_url_youtube(html):
  """
  Take the first video link of a html of Youtube.
  """    

  url = None    
  raw_data = BeautifulSoup(html, "html.parser").find('a', {"dir": "ltr"})
  if raw_data is not None:
    url = str(raw_data['href'])
  else:
    print("[!] No video clip of the band in Youtube.", file=sys.stderr)

  return url

def request_youtube(name, cd):
  """"
  Make a request to Youtube and return the first link.
  """
  
  YT_URL = "https://www.youtube.com/results?search_query="

  if cd is None:
    query = name + "+metal+music"
  else:
    query = name + "+-+" + cd
	
  if glob_verbose:
    print("[*] Query: " + query.replace('+', ' '))

  url_yt = YT_URL + query
  html_yt = requests.get(url_yt).content
  link_yt = get_url_youtube(html_yt)

  return link_yt

def only_youtube(name, ide, first):
  """
  Function who try to play the song.
  """

  cd = get_cd(ide)
  link = request_youtube(name, cd)

  if link is not None:
    yt_link = "https://www.youtube.com" + link
    webbrowser.open(yt_link)
    return yt_link


def find_band(only_yt):
  """ Find url for one band and display it. """
  
  html = requests.get(URL_RANDOM).content
  name, ide = get_name_id(html)
  name = clean_name(name)

  if glob_print_page:
    webbrowser.open("https://www.metal-archives.com/bands/" + name + "/" + ide)

  print("[#] Band: " + name + ", ID: " + ide)
  
  if only_yt:
    return only_youtube(name, ide, True)
  else:
    url = get_related_links(html)
    html = requests.get(url).content
    list_link = get_music_link(html, name)

    link = None
    if list_link:
      link = chose_link(list_link)
    
    if link:
      webbrowser.open(link)
      return link
    else:
      print("[!] No musical link for this band.\n    Trying on youtube.", file=sys.stderr)
      return only_youtube(name, ide, False)

"""
Main
"""

def main(argv):
  parser = argparse.ArgumentParser(
    prog='randometal',
    description='Randomly select bands from "metal-archives.com".',
    usage="""
       __                 _                   _        _ 
      /__\ __ _ _ __   __| | ___   /\/\   ___| |_ __ _| |
     / \/// _` | '_ \ / _` |/ _ \ /    \ / _ \ __/ _` | |
    / _  \ (_| | | | | (_| | (_) / /\/\ \  __/ || (_| | |
    \/ \_/\__,_|_| |_|\__,_|\___/\/    \/\___|\__\__,_|_|
  """) 
  parser.add_argument('-y', '--youtube', action='store_true', help='try to find an play songs only on YouTube')
  parser.add_argument('-v', '--verbose', action='store_true', help='display more informations')
  parser.add_argument('-p', '--page', action='store_true', help='open the archive-metal page of the band')
  parser.add_argument('-n', '--nbr', default=1, type=int, help='number of bands to search. One by default')

  args = parser.parse_args()

  global glob_verbose
  glob_verbose = args.verbose
  global glob_print_page
  glob_print_page = args.page

  links = []
  for i in range(args.nbr):
    links.append(find_band(args.youtube))
    if args.verbose:
      print("[*] Link : " + links[i] + "\n    ====")

if __name__ == "__main__":
  main(sys.argv[1:])
