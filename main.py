from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from random import choices, random

import requests, lxml, re, urllib.parse, base64
import random
import pathlib
import sys
import os


default_percentages = ["33", "33", "34"]
default_memes = [
    "fornite",
    "sus",
    "minecraft",
    "cheese",
    "among us",
    "super mario movie",
    "reddit meme",
    "the bee movie"
]

'''setup args and make sure that the args provided are valid'''
def main():
    print("Start")
    operations = {"-s":"--simple", "-cm": "--custom-memes", "-cr": "--custom-ratio", "-cmr": "--custom-memes_ratio", "-h": "--help"}
    operation = ""
    config_file = ""
    texture_folder = ""
    sys_args = sys.argv
    operation = sys_args[1]
    
    ### check sys_args[1] | should be one of the operations listed above ###
    for k, v in operations.items():
        if operation == k or operation == v:
            operation = k
            break
    
    ### if the operation is -h or invalid show help ###
    if operation == "-h" or operation == "":
        print_help()
    
    ### make sure that a folder is provided in sys_args[2] and save it ###
    if len(sys_args) == 3 and operation == "-s":
        if Path(sys_args[2]).is_dir():
            texture_folder = Path(sys_args[2])
    ### if the option is not -s and there are 4 sys_args ###
    elif len(sys_args) == 4 and operation != "-s":
        ### save config file location if is_file otherwise print error ###
        config_file = Path(sys_args[2]) if Path(sys_args[2]).is_file() else print("invalid config location")
        ### save texture path if is_dir otherwise print error ###
        texture_folder = Path(sys_args[3]) if Path(sys_args[3]).is_dir() else print("invalid texture folder")
    else:
        ### if not all arguments are provided print -h ###
        print("please make sure you have provided all arguments")
        print_help()
        
    run_args(operation, config_file, texture_folder)

'''check args and run'''
def run_args(operation, config_file, texture_folder):
    print("run args")
    # sys.argv[]
    #   0: main.py
    #   1: options -s -cm -cr -cmr -h
    #   2: either the $file for -cm -cr -cmr or the $texture_path
    #   3: the $texture_path if using -s
    #
    #   Please add the path to customization text file
    #
    # usage: python3 main [option] [?text file?] [textures path]
    # -cm --custom-memes == prechpsem memes
    # -cr --custom-ratio == prechosen ratio
    # -cmr --custom-memes_ratio == prechosen ratio
    # -h --help == print help message
    # -s --simple == simple prechosen memes and ratio
    print(operation, config_file, texture_folder)
    
    percentages = []
    memes = []
    if config_file:
        with open(config_file, 'r') as file:
            lines = file.readlines()
            lines = [line.rstrip() for line in lines]
            percentages = lines[0]
            for i in range(1, len(lines)):
                memes.append(lines[i])
    else:
        percentages = default_percentages
        memes = default_memes
    
    get_new_textures(memes, percentages, texture_folder)

'''handels downloading / resizing / and replacing of textures'''
def get_new_textures(memes, percentages, texture_folder):
    print("geting new textures")
    texture_names = get_texture_files(texture_folder)
    
    # 0 = $filename
    # 1 = $filename + $meme
    # 2 = $meme
    options = [0, 1, 2]
    weights = get_weights(percentages)    
    for texture in texture_names:
        choice = choices(options, weights)[0]
        new_image = ""
        image_location = os.path.join(texture_folder, texture)
        texture_name = os.path.splitext(texture)[0]
        meme = memes[random.randrange(len(memes))]
        search_term = ""
        if choice == 0:
            search_term = texture_name
        elif choice == 1:
            search_term = texture_name + " " + meme
        elif choice == 2:
            search_term = meme
        print(image_location)
        old_image = Image.open(image_location)        
        new_image = download_google_image(search_term)
        new_image = resize_to_match(new_image, old_image)
        
        os.remove(os.path.join(texture_folder, texture))
        ext = pathlib.Path(image_location).suffix.replace(".", "").upper()
        if ext == "JPG":
            ext = "JPEG" 
        new_image.save(os.path.join(texture_folder, texture), ext)
        
def resize_to_match(new, old):
    w, h = old.size
    return new.resize((w, h))

def get_weights(percentages):
    print("geting weights for ", percentages)
    weights = []
    for p in percentages:
        weights.append(1 / float(p))
    return weights
    

'''get texture file names and make sure they are .png, .jpg, or .jpeg'''
def get_texture_files(texture_folder):
    print("geting texture files from", texture_folder)
    files = []
    for file in os.listdir(texture_folder):
        ext = pathlib.Path(file).suffix
        if valid_ext(ext):
            files.append(file)
    return files

'''check texture file extention and make sure it is .png, .jpg, or .jpeg'''
def valid_ext(ext):
    print("checking valid extentions against", ext)
    valid = [
        ".png",
        ".jpg",
        ".jpeg"
    ]
    for v in valid:
        if ext == v:
            return True
    print("invalid extention ", ext)
    print("must be ", valid)
    return False

# bassed on https://medium.com/geekculture/scrape-google-inline-images-with-python-85837af2fe17
'''downloads and returns a google images from the search results'''
def download_google_image(search_term):
    print("downloading google image - ", search_term)
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
    }
    params = {
        "q": search_term,
        "sourceid": "chrome",
    }
    
    #get html from BeautifulSoup
    html = requests.get("https://www.google.com/search", params=params, headers=headers)
    soup = BeautifulSoup(html.text, 'lxml')
    
    for result in soup.select('div[jsname=dTDiAc]'):
        link = f"https://www.google.com{result.a['href']}"
        being_used_on = result['data-lpage']
        print(f'Link: {link}\nBeing used on: {being_used_on}\n')
    
    # finding all script (<script>) tags
    script_img_tags = soup.find_all('script')
        
    img_matches = re.findall(r"s='data:image/jpeg;base64,(.*?)';", str(script_img_tags))
    image = ""
    for index, image in enumerate(img_matches):
        try:
            image = Image.open(BytesIO(base64.b64decode(str(image))))
            break
        except:
            pass
        
    return image

def print_help():
    print("usage: main [option] [?text file?] [textures path]")
    mst = "meme search terms"
    rfs = "ratios for searching"
    print("-cm  | --custom-memes    : use a custom %s and default %s" % (mst, rfs))
    print("-cr  | --custom-ratio    : use a custom %s and default %s" % (rfs, mst))
    print("-cmr | --custom-memes-ratio    : use a custom %s and custom %s" % (rfs, mst))
    print("         | put the ratios of searches at the top (filename%, filename+meme%, meme%) for example\" 25, 25, 50 \"")
    print("         | and serperate the memes one per line (like so)")
    print("         | ------------------------------------")
    print("         | 25 25 50")
    print("         | fornite")
    print("         | among us")
    print("         | cheese")
    print("-h   | --help              : print this help message")
    print("-s   | --simple            : uses a predfinded %s and the %s" % (mst, rfs))
    happy_exit()
    
def happy_exit():
    print()
    print("i hope u have an amazing day ur so cute 😃")
    print("i hope everying worked out")
    exit()

if __name__ == "__main__":
    main()