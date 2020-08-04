#!/usr/bin/env python3
# -*- coding: utf8 -*-

# TODO: Add band's country to improve YouTube results accuracy

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

PRED_MUSIC_LINK = lambda tag: tag.name == 'a' and tag.get('title') is not None and tag['title'].find('Go to:') != -1
PATTERN_YT_JSON_VIDEO_DATA = re.compile('window\["ytInitialData"\] = ')

def get_html_content(args, url, error_msg):
  """Get the HTML content of a Web page"""
  if args.verbose:
    print(f"[#] GET: {url}")

  response = requests.get(url, headers=HEADERS)
  if response.ok:
    return response.content
  else:
    print((f"[!] {error_msg}\n"
           f"    Status code: {response.status_code})."), file=sys.stderr)

def clean_name(band_name):
  """Clean the caracters who are not decoded."""
  band_name = urllib.parse.unquote(band_name)
  return band_name.replace('_', ' ')

def get_name_id(parser):
  """Get the name and the id of the band corresponding to the html page."""
  band_name_tag = parser.find('h1', {"class": 'band_name'})
  url_band_page = band_name_tag.find('a').get('href')
  return url_band_page.split('bands/')[1].split('/')

def get_last_discography(args, band_id):
  """Get the name of the newest album/demo/single of a band"""
  url_disco = URL_DISCOGRAPHY.format(id=band_id)
  content = get_html_content(args, url_disco, "Cannot get the band's discography")
  if content:
    parser = BeautifulSoup(content, 'lxml')
    for cls in args.discography:
      discos = parser.findAll('a', {'class': cls})
      if discos:
        # The last entry is the newest
        return discos[-1].text

    print("[!] No discography for the band.", file=sys.stderr)

def get_related_links(parser):
  """Take the link in the 'Related links' onglet of metal-archives"""
  related_links_tag = parser.find('a', {'title': 'Related links'})
  if related_links_tag:
    return related_links_tag['href']
  else:
    print("[!] No related link for this band.", file=sys.stderr)

def get_music_link(html):
  """Extract links to music websites"""
  parser = BeautifulSoup(html, 'lxml')
  a_tags = parser.findAll(PRED_MUSIC_LINK)
  if a_tags:
    return [a_tag['href'] for a_tag in a_tags]
  print("[!] No related links for this band.", file=sys.stderr)

def chose_link(args, list_link):
  """Find the most interesting musical link"""
  for site in args.website:
    for link in list_link:
      if site in link:
        return link
  print(("[!] No music links related to one of the following\n"
        f"    site: {', '.join(args.website)}."), file=sys.stderr)

def get_key_youtube(html):
  """Get the key of the first vband_ido in the result page."""
  parser = BeautifulSoup(html, 'lxml')
  script_content = parser.findAll('script', text=PATTERN_YT_JSON_VIDEO_DATA)
  script_content = script_content[0]
  for m in re.finditer('watch\?v=(.{11})",', script_content.text):
      return m.group(1)

def request_youtube(args, band_name, last_disco):
  """"Make a request to Youtube and return the first link."""
  if last_disco:
    query = f'"{band_name} - {last_disco}"'
  else:
    query = f'"{band_name}" metal music'

  url_yt = URL_YT_SEARCH.format(query=urllib.parse.quote_plus(query, safe=''))
  content = get_html_content(args, url_yt, "Cannot make the query on YouTube")
  if content:
    return get_key_youtube(content)

def only_youtube(args, band_name, band_id):
  """Search band last album/ep/demo/... on YouTube"""
  last_disco = get_last_discography(args, band_id)
  if last_disco:
    key = request_youtube(args, band_name, last_disco)
    if key:
      yt_link = URL_YT_VIDEO.format(key=key)
      webbrowser.open(yt_link)
      return yt_link

def search_music(args, band_name, band_id, parser):
  """Search band's music via the 'Related links' of metal-archives or on YouTube"""
  if args.youtube:
    return only_youtube(args, band_name, band_id)
  else:
    related_links_url = get_related_links(parser)
    content = get_html_content(args, related_links_url, "Cannot access the 'related links' page")
    if content:
      list_link = get_music_link(content)
      if list_link:
        link = chose_link(args, list_link)
        if link:
          webbrowser.open(link)
          return link

      print("[!] Trying on YouTube.", file=sys.stderr)
      return only_youtube(args, band_name, band_id)

def find_band(args):
  """ Find url for one band and display it. """
  content = get_html_content(args, URL_RANDOM, "Cannot get a random band")
  if content:
    parser = BeautifulSoup(content, 'lxml')
    band_name, band_id = get_name_id(parser)
    band_name = clean_name(band_name)

    if args.open_page:
      webbrowser.open(URL_BAND_PAGE.format(name=band_name, id=band_id))

    print(f"[*] Band: {band_name}, ID: {band_id}")

    search_music(args, band_name, band_id, parser)

def main(args):
  for _ in range(args.number):
    link = find_band(args)
    if args.verbose and link is not None:
      print(f"[#] Link: {link}\n    ====")

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
  parser.add_argument('-v', '--verbose', action='store_true', help='display more informations')
  parser.add_argument('-n', '--number', default=1, type=int, help='number of bands to search')
  parser.add_argument('-o', '--open-page', action='store_true', help='open the metal-archives page of bands')
  parser.add_argument('-y', '--youtube', action='store_true', help='try to find an play songs on YouTube')

  WEBSITE_TO_TARGET = ['bandcamp', 'soundcloud', 'youtube', 'spotify']
  parser.add_argument('-w', '--website', nargs='+', default=WEBSITE_TO_TARGET, type=str, help=f'define the priority between websites in a decreasing order. The values correspond to the domain name of the Web sites. The default sites and order is: {", ".join(WEBSITE_TO_TARGET)}')
  DISCOGRAPHY_CLASSES = ['album', 'single', 'other', 'demo']
  parser.add_argument('-d', '--discography', nargs='+', default=DISCOGRAPHY_CLASSES, type=str, help=f'define the priority between classes of discography in a decreasing order. The values comes from the HTML content of the "Discography" onglet in metal-archives. The default classes and order is: {", ".join(DISCOGRAPHY_CLASSES)}')

  args = parser.parse_args()

  main(args)