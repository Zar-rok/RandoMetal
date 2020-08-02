#!/usr/bin/env python3
# -*- coding: utf8 -*-

# TODO: Add args for WEBSITE_TO_TARGET

import re
import sys
import urllib
import webbrowser

from bs4 import BeautifulSoup
import requests

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'}

URL_RANDOM = "https://www.metal-archives.com/band/random"
URL_BAND_PAGE = "https://www.metal-archives.com/bands/{name:s}/{id:s}"
URL_DISCOGRAPHY = "https://www.metal-archives.com/band/discography/id/{id:s}/tab/all"
URL_YT_SEARCH = "https://www.youtube.com/results?search_query={query:s}"
URL_YT_VIDEO = "https://www.youtube.com/watch?v={key:s}"

# From the most interesting type of disco./website to the least one.
DISCOGRAPHY_CLASSES = ['album', 'single', 'other', 'demo']
WEBSITE_TO_TARGET = ['bandcamp', 'soundcloud', 'youtube', 'spotify', 'myspace']

PRED_MUSIC_LINK = lambda tag: tag.name == 'a' and tag.get('title') is not None and tag['title'].find('Go to:') != -1
PATTERN_YT_JSON_VIDEO_DATA = re.compile('window\["ytInitialData"\] = ')

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

def get_last_discography(ide):
  """Get the name of the newest album/demo/single of a band"""
  url_disco = URL_DISCOGRAPHY.format(id=ide)
  response = requests.get(url_disco, headers=HEADERS)
  if not response.ok:
    print("[!] Cannot get the band's discography (status code {status:d})."
        .format(status=response.status_code), file=sys.stderr)
    return ''

  parser = BeautifulSoup(response.content, "html.parser")
  for cls in DISCOGRAPHY_CLASSES:
    discos = parser.findAll('a', {'class': cls})
    if discos:
      return discos[-1].text

  print("[!] No discography for the band.", file=sys.stderr)
  return ''

def get_related_links(parser):
  """Take the link in the 'Related links' onglet of archive-metal"""
  related_links_tag = parser.find('a', {'title': 'Related links'})
  if related_links_tag:
    return related_links_tag['href']
  else:
    print("[!] No related link for this band.", file=sys.stderr)
    return ''

def get_music_link(html, name):
  """Extract links to music websites"""
  parser = BeautifulSoup(html, "html.parser")
  a_tags = parser.findAll(PRED_MUSIC_LINK)
  if a_tags:
    return [a_tag['href'] for a_tag in a_tags]
  print("[!] No related links for this band.", file=sys.stderr)

def chose_link(list_link):
  """Find the most interesting musical link"""
  for site in WEBSITE_TO_TARGET:
    for link in list_link:
      if site in link:
        return link
  print("[!] No music links related to one of the following site: {sites:s}."
      .format(sites=', '.join(WEBSITE_TO_TARGET)), file=sys.stderr)
  return ''

def get_key_youtube(html):
  """Get the key of the first video in the result page."""    
  parser = BeautifulSoup(html, "html.parser")
  script_content = parser.findAll('script', text=PATTERN_YT_JSON_VIDEO_DATA)[0]
  for m in re.finditer('watch\?v=(.{11})",', script_content.text):
      return m.group(1)
  return ''

def request_youtube(args, name, last_disco):
  """"Make a request to Youtube and return the first link."""
  if last_disco:
    query = '"{name:s}+-+{disco:s}"'.format(name=name, disco=last_disco)
  else:
    query = '"{name:s}"+metal+music'.format(name=name)

  if args.verbose:
    print("[*] YouTube query: " + query.replace('+', ' '))

  url_yt = URL_YT_SEARCH.format(query=query)
  response = requests.get(url_yt, headers=HEADERS)
  if not response.ok:
    print("[!] Cannot make the query on YouTube (status code {status:d})."
        .format(status=response.status_code), file=sys.stderr)
    return ''

  return get_key_youtube(response.content)

def only_youtube(args, name, ide):
  """Search band last album/ep/demo/... on YouTube"""
  last_disco = get_last_discography(ide)
  if last_disco:
    key = request_youtube(args, name, last_disco)
    if key:
      yt_link = URL_YT_VIDEO.format(key=key)
      webbrowser.open(yt_link)
      return yt_link

def search_music(args, name, ide, parser):
  """Search band's music via the 'Related links' of archive-metal or on YouTube"""
  if args.youtube:
    return only_youtube(args, name, ide)
  else:
    related_links_url = get_related_links(parser)
    response = requests.get(related_links_url, headers=HEADERS)
    if not response.ok:
      print("[!] Cannot access the 'related links' page (status code {status:d})."
          .format(status=response.status_code), file=sys.stderr)
      return ''

    list_link = get_music_link(response.content, name)
    if list_link:
      link = chose_link(list_link)
      if link:
        webbrowser.open(link)
        return link

    print("[!] Trying on youtube.", file=sys.stderr)
    return only_youtube(args, name, ide)

def find_band(args):
  """ Find url for one band and display it. """
  response = requests.get(URL_RANDOM, headers=HEADERS)
  if not response.ok:
    print("[!] Cannot get a random band (status code {status:d})."
        .format(status=response.status_code), file=sys.stderr)
    return ''

  parser = BeautifulSoup(response.content, "html.parser")
  name, ide = get_name_id(parser)
  name = clean_name(name)

  if args.page:
    webbrowser.open(URL_BAND_PAGE.format(name=name, id=ide))

  print("[#] Band: {name:s}, ID: {id:s}".format(name=name, id=ide))

  search_music(args, name, ide, parser)

def main(args):
  for _ in range(args.nbr):
    link = find_band(args)
    if args.verbose and link is not None:
      print("[*] Link : " + link + "\n    ====")

if __name__ == "__main__":
  import argparse
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
