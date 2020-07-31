#!/usr/bin/env python3
# -*- coding: utf8 -*-

# TODO: Use a dict with all information about bands.
# TODO: Add args for WEBSITE_TO_TARGET

import sys
import urllib
import webbrowser
import argparse

from bs4 import BeautifulSoup
import requests

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'}

URL_RANDOM = "https://www.metal-archives.com/band/random"
URL_BAND_PAGE = "https://www.metal-archives.com/bands/{name:s}/{id:s}"
URL_CD = "https://www.metal-archives.com/band/discography/id/{id:s}/tab/all"
URL_YT = "https://www.youtube.com/results?search_query={query:s}"

WEBSITE_TO_TARGET = ['bandcamp', 'soundcloud', 'youtube', 'spotify', 'myspace']

PRED_MUSIC_LINK = lambda tag: tag.name == 'a' and tag.get('title') is not None and tag['title'].find('Go to:') != -1

def get_html_content(url):
  """Get html content from a url."""
  response = requests.get(url, headers=HEADERS)
  return response.ok, response.content

def clean_name(name):
  """Clean the caracters who are not decoded."""
  name = urllib.parse.unquote(name)
  name = name.replace('_', ' ')
  return name  

def get_name_id(parser):
  """Get the name and the id of the band corresponding to the html page."""
  band_name_tag = parser.find('h1', {"class": 'band_name'})
  url_band_page = band_name_tag.find('a').get('href')
  name, ide = url_band_page.split('bands/')[1].split('/')
  return name, ide

def get_cd(ide):
  """
  Take an id and return the name of the newest album/demo/single of a band.
  """

  cd = None
  raw_data  = []
  class_word = ["demo", "single", "album", "other"]
  url_cd = URL_CD.format(id=ide)

  html = get_html_content(url_cd)
  for i in range(len(class_word)):
    raw_data += BeautifulSoup(html, "html.parser").findAll('a', {"class" :class_word[i]})

  try:    
    cd = ''.join(raw_data[(len(raw_data))-1].findAll(text=True))
  except IndexError:
    print("[!] No album for the band.", file=sys.stderr)

  return cd

def get_related_links(parser):
  """Take the link in the 'Related links' onglet of archive-metal"""
  related_links_tag = parser.find('a', {'title': 'Related links'})
  if related_links_tag is not None:
    return related_links_tag['href']
  else:
    print("[!] No related link for this band.", file=sys.stderr)
    return None

def get_music_link(html, name):
  """Extract links to music websites"""
  parser = BeautifulSoup(html, "html.parser")
  a_tags = parser.findAll(PRED_MUSIC_LINK)
  return [a_tag['href'] for a_tag in a_tags]

def chose_link(list_link):
  """Find the most interesting musical link"""
  for site in WEBSITE_TO_TARGET:
    for link in list_link:
      if site in link:
        return link
  return ''

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

def request_youtube(args, name, cd):
  """"
  Make a request to Youtube and return the first link.
  """

  if cd is None:
    query = "{name:s}+metal+music".format(name=name)
  else:
    query = "{name:s}+-+{cd:s}".format(name=name, cd=cd)

  if args.verbose:
    print("[*] YouTube query: " + query.replace('+', ' '))

  url_yt = URL_YT.format(query=query)
  html_yt = get_html_content(url_yt)
  link_yt = get_url_youtube(html_yt)

  return link_yt

def only_youtube(args, name, ide):
  """
  Function who try to play the song.
  """

  cd = get_cd(ide)
  link = request_youtube(args, name, cd)

  if link is not None:
    yt_link = "https://www.youtube.com" + link
    webbrowser.open(yt_link)
    return yt_link

def find_band(args):
  """ Find url for one band and display it. """
 
  response = requests.get(URL_RANDOM, headers=HEADERS)
  if not response.ok:
    print("[!] Cannot get a random band (status code {status:d}).".format(status=response.status_code), file=sys.stderr)
    return

  parser = BeautifulSoup(response.content, "html.parser")
  name, ide = get_name_id(parser)
  name = clean_name(name)

  if args.page:
    webbrowser.open(URL_BAND_PAGE.format(name=name, id=ide))

  print("[#] Band: {name:s}, ID: {id:s}".format(name=name, id=ide))
  
  if args.youtube:
    return only_youtube(args, name, ide)
  else:
    related_links_url = get_related_links(parser)
    response = requests.get(related_links_url, headers=HEADERS)
    if not response.ok:
      print("[!] Cannot access the 'related links' page (status code {status:d}).".format(status=response.status_code), file=sys.stderr)
      return

    list_link = get_music_link(response.content, name)
    if len(list_link) > 0:
      link = chose_link(list_link)
      if len(link) > 0:
        webbrowser.open(link)
        return link
      else:
        print("[!] No music links related to one of the following site: {sites:s}.".format(sites=join(', ', WEBSITE_TO_TARGET)), file=sys.stderr)
    else:
      print("[!] No related links for this band", file=sys.stderr)

    print("[!] No musical link for this band.\n    Trying on youtube.", file=sys.stderr)
    return only_youtube(args, name, ide)

def main(args):
  for i in range(args.nbr):
    link = find_band(args)
    if args.verbose and link is not None:
      print("[*] Link : " + link + "\n    ====")

if __name__ == "__main__":
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

  main(args)
