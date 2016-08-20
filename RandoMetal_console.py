#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import time
import getopt
import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import requests
import urllib
from bs4 import BeautifulSoup

URL_RANDOM = "http://www.metal-archives.com/band/random"

def info():
    print ("   __                 _                   _        _ ")
    print ("  /__\ __ _ _ __   __| | ___   /\/\   ___| |_ __ _| |")
    print (" / \/// _` | '_ \ / _` |/ _ \ /    \ / _ \ __/ _` | |")
    print ("/ _  \ (_| | | | | (_| | (_) / /\/\ \  __/ || (_| | |")
    print ("\/ \_/\__,_|_| |_|\__,_|\___/\/    \/\___|\__\__,_|_|")
    print ("")
    print ("|--------------------------------------------------------|")
    print ("  Juste un petit programme inutile qui vas chercher,")
    print (" aleatoirement, un groupe de metal sur le site")
    print ("'metal-archives.com' et lance une musique de ce groupe.")
    print ("                        Zar - 2016")
    print ("|--------------------------------------------------------|")
    print (" Options : ")
    print ("   -y : recherche des musiques sur youtube uniquement.")
    print ("|--------------------------------------------------------|\n")

def get_name_id(html):
    """
    Function who take a html code and return the name of the band and his id.
    """
    
    raw_data = BeautifulSoup(html, "html.parser").find('h1', {"class": 'band_name'})
    raw_data = raw_data.find('a').get('href')
    raw_data = str(raw_data).split('/', 5)
    name = raw_data[4]
    ide = raw_data[5] 
    
    return name, ide
    
def get_cd(ide):
    """
    Function who take a id and return the newest album/demo/single of a band.
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

def get_url_youtube(html):
    """
    Function who take the first video in the html of youtube.
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
    
def only_youtube(name, ide):
    """
    Function who juste use youtube.
    """

    cd = get_cd(ide)

    link = request_youtube(name, cd)

    if link is not None:
        driver = webdriver.Firefox()
        driver.maximize_window()
        driver.get("https://www.youtube.com"+link)
    
        
def main(argv):
    
    try:                                
        opts, args = getopt.getopt(argv, "y", ["youtube"])
    except getopt.GetoptError:
        info()
        sys.exit(2)

    html = requests.get(URL_RANDOM).content
    name, ide = get_name_id(html)
    name = decode_url(name)
    print ("[#] Band: "+name+", ID: "+ide)
        
    for opt, arg in opts:
        if opt in ("-y", "--youtube"):
            only_youtube(name, ide)
            sys.exit() 
        else:
            assert False, "[!!] Unhandled option."
  
    only_youtube(name, ide)
    

if __name__ == "__main__":
    info()
    main(sys.argv[1:])

