#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import getopt
import urllib

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import requests

URL_RANDOM = "http://www.metal-archives.com/band/random"

"""
General functions
"""

def usage():
    print ("     __                 _                   _        _ ")
    print ("    /__\ __ _ _ __   __| | ___   /\/\   ___| |_ __ _| |")
    print ("   / \/// _` | '_ \ / _` |/ _ \ /    \ / _ \ __/ _` | |")
    print ("  / _  \ (_| | | | | (_| | (_) / /\/\ \  __/ || (_| | |")
    print ("  \/ \_/\__,_|_| |_|\__,_|\___/\/    \/\___|\__\__,_|_|")
    print ("")
    print ("|--------------------------------------------------------|")
    print ("    A little script to randomly play a song taken ")
    print ("         from 'metal-archives.com' | Zar - 2016")
    print ("|--------------------------------------------------------|")
    print (" Option : ")
    print ("   -y [--youtube]: Try to find and play song only on Youtube.\n")

def get_name_id(html):
    """
    Function who take a html code and return the name of the band and his id in metal-archive.com.
    """
    
    raw_data = BeautifulSoup(html, "html.parser").find('h1', {"class": 'band_name'})
    raw_data = raw_data.find('a').get('href')
    raw_data = str(raw_data).split('/', 5)
    name = raw_data[4]
    ide = raw_data[5] 
    
    return name, ide
    
def get_cd(ide):
    """
    Function who take a id and return the name of the newest album/demo/single of a band.
    """

    cd = None
    raw_data  = []
    class_word = ["demo", "single", "album", "other"]
    url_cd = "http://www.metal-archives.com/band/discography/id/"+str(ide)+"/tab/all"
    
    html = requests.get(url_cd).content
    for i in range(len(class_word)):
        raw_data += BeautifulSoup(html, "html.parser").findAll('a', {"class" :class_word[i]})
    
    try:    
        cd = ''.join(raw_data[(len(raw_data))-1].findAll(text=True))
    except IndexError:
        print ("[!!] No album for the band\n")
    
    return cd

def decode_url(word):
    """ Function who fix url char (%..) => A,B,... """    
    
    try:
        word = urllib.unquote(word).decode('utf8')
    except UnicodeEncodeError:
        pass
    
    word = word.replace('_', ' ')
    
    return word

"""
Functions about Youtube
"""

def get_url_youtube(html):
    """
    Function who take the first video link of a html of youtube.
    """    

    url = None    
    raw_data = BeautifulSoup(html, "html.parser").find('a', {"dir": "ltr"})
    if raw_data is not None:
        url = str(raw_data['href'])
    else:
        print ("[!!] No video clip of the band in Youtube\n")

    return url

def request_youtube(name, cd):
    """"
    Function who make a request to youtube and return the first link.
    """

    if cd is None:
        url_yt = "https://www.youtube.com/results?search_query="+name+"+metal"
    else:
        url_yt = "https://www.youtube.com/results?search_query="+name+"+-+"+cd

    html_yt = requests.get(url_yt).content

    link_yt = get_url_youtube(html_yt)
    
    return link_yt
    
def only_youtube(name, ide, first):
    """
    Function who try to play the song.
    """

    if first:
        html = requests.get(URL_RANDOM).content
        name, ide = get_name_id(html)
        print ("\n[#] Band: "+name+", ID: "+ide)

    cd = get_cd(ide)

    link = request_youtube(name, cd)

    if link is not None:
        driver = webdriver.Firefox()
        driver.maximize_window()
        driver.get("https://www.youtube.com"+link)
    
"""
Function for other site.
"""

def get_related_links(html):
    """
    Function who take the link in the 'Related links' onglet of archive-metal.
    """

    url = None
    raw_data = BeautifulSoup(html, "lxml").find('a', {"title": "Related links"})
    
    if raw_data is not None:
        url = str(raw_data['href'])
    else:
        print ("[!!] No related link for this band\n")
        
    return url


def get_music_link(html, name):
    """
    Function who extract link 
    """

    i = 0
    raw_data = []
    music_link = []
    title_list = ["Go to: Myspace", "Go to: Myspace Page", "Go to: Soundcloud", "Go to: Youtube", "Go to: Youtube Page", "Go to: Bandcamp", "Go to: MySpace", "Go to: MySpace Page", "Go to: SoundCloud", "Go to: YouTube", "Go to: YouTube Page", "Go to: YouTube Channel", "Go to: BandCamp", "Go to: "+name+" @ Myspace", "Go to: "+name+" @ Soundcloud", "Go to: "+name+" @ youtube", "Go to: "+name+" @ Bandcamp", "Go to: "+name+" @ MySpace", "Go to: "+name+" @ SoundCloud", "Go to: "+name+" @ youTube", "Go to: "+name+" @ BandCamp"]

    while (raw_data is None) or (i < (len(title_list))):
        raw_data += BeautifulSoup(html, "lxml").findAll('a', {"title": title_list[i]})        
        i+= 1        
    
    for j in range(len(raw_data)):
        music_link.append(raw_data[j].get('href')) 
        
    
    return music_link

def chose_link(list_link):
    """
    Function who return musical link
    """

    link = list_link[0]
    site = ""
    temp = link.split('/')
    temp2 = link.split('.')
    if "bandcamp" in temp2:
        site = "bandcamp"
        return link, site
    elif "soundcloud.com" in temp:
        site = "soundcloud"
        return link, site
    if "youtube" in temp2:
        site = "youtube"
        return link, site
    else:
        if "myspace.com" in temp:
            site = "myspace"
            return link, site
    
def open_site(link, site):
    """
    Function who launch the song depending of the site we get.
    """
    
    driver = webdriver.Firefox()
    driver.maximize_window()
    
    if site == "bandcamp":
        driver.get(link)
        try:
            driver.find_element_by_class_name('playbutton').click()
        except:
            pass
        
    elif site == "myspace":
        driver.get(link)
        try:
            element = driver.find_element_by_css_selector('button.playBtn.play_25.song')
            hover = ActionChains(driver).move_to_element(element)
            hover.perform()
        except:
            pass
        try:
            driver.find_element_by_css_selector('button.playBtn.play_25.song').click()
        except:
            pass
        
    elif site == "soundcloud":
        driver.get(link)
        try:
            driver.find_element_by_css_selector('button.sc-button-play.sc-button.sc-button-large').click()
        except:
            pass
        
    elif site == "youtube":
        driver.get(link+"/videos")
        try:
            driver.find_element_by_css_selector('a.yt-uix-sessionlink.yt-uix-tile-link.spf-link.yt-ui-ellipsis.yt-ui-ellipsis-2').click()
        except:
            pass

"""
Main
"""

def main(argv):

    try:                                
        opts, args = getopt.getopt(argv, "hy", ["help", "youtube"])
    except getopt.GetoptError:
        print("[!!] Unhandled option.")
        usage()
        sys.exit(2)
            
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit() 
        elif opt in ("-y", "--youtube"):
            only_youtube(name, ide)
            sys.exit() 
        else:
            assert False, "[!!] Unhandled option."

    html = requests.get(URL_RANDOM).content
    name, ide = get_name_id(html)
    name = decode_url(name)

    print ("\n[#] Band: "+name+", ID: "+ide)

    url = get_related_links(html)
    
    html2 = requests.get(url).content
    list_link = get_music_link(html2, name)

    if list_link:
        link, site = chose_link(list_link)
        open_site(link, site)
    else:
        print ("[!!] No musical link for this band.")
        print ("     Trying on youtube.")
        only_youtube(name, ide, False)
    

if __name__ == "__main__":
    main(sys.argv[1:])

