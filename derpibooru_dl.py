#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      new
#
# Created:     08/02/2014
# Copyright:   (c) new 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python



import time
import os
import sys
import re
import mechanize
import cookielib
import logging
import urllib2
import httplib
import random
import glob
import ConfigParser
import HTMLParser
import json
import shutil



# getwithinfo()
GET_REQUEST_DELAY = 2
GET_RETRY_DELAY = 30
GET_MAX_ATTEMPTS = 20




def setup_logging(log_file_path):
    # Setup logging (Before running any other code)
    # http://inventwithpython.com/blog/2012/04/06/stop-using-print-for-debugging-a-5-minute-quickstart-guide-to-pythons-logging-module/
    assert( len(log_file_path) > 1 )
    assert( type(log_file_path) == type("") )
    global logger
    log_file_folder =  os.path.split(log_file_path)[0]
    if not os.path.exists(log_file_folder):
        os.makedirs(log_file_folder)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logging.debug('Logging started.')
    # End logging setup


def deescape(html):
    # de-escape html
    # http://stackoverflow.com/questions/2360598/how-do-i-unescape-html-entities-in-a-string-in-python-3-1
    deescaped_string = HTMLParser.HTMLParser().unescape(html)
    return deescaped_string


def get(url):
    #try to retreive a url. If unable to return None object
    #Example useage:
    #html = get("")
    #if html:
    assert_is_string(url)
    deescaped_url = deescape(url)
    gettuple = getwithinfo(deescaped_url)
    if gettuple:
        reply, info = gettuple
        return reply


def getwithinfo(url):
    """Try to retreive a url. If unable to return None objects
    Example useage:
    html = get("")
        if html:
    """
    attemptcount = 0
    while attemptcount < GET_MAX_ATTEMPTS:
        attemptcount = attemptcount + 1
        if attemptcount > 1:
            logging.debug( "Attempt" + str(attemptcount) )
        try:
            r = br.open(url)
            info = r.info()
            reply = r.read()
            delay(GET_REQUEST_DELAY)
            # Save html responses for debugging
            #print info
            #print info["content-type"]
            if "html" in info["content-type"]:
                #print "saving debug html"
                save_file("debug\\get_last_html.htm", reply, True)
            else:
                save_file("debug\\get_last_not_html.txt", reply, True)
            return reply,info
        except urllib2.HTTPError, err:
            logging.debug(str(err))
            if err.code == 404:
                logging.debug("404 error! " + str(url))
                return
            elif err.code == 403:
                logging.debug("403 error, ACCESS DENIED! url: "+str(url))
                return
            elif err.code == 410:
                logging.debug("410 error, GONE")
                return
            else:
                save_file("debug\\error.htm", err.fp.read(), True)
        except urllib2.URLError, err:
            logging.debug(str(err))
            if "unknown url type:" in err.reason:
                return
        except httplib.BadStatusLine, err:
            logging.debug(str(err))
        delay(GET_RETRY_DELAY)


def save_file(filenamein,data,force_save=False):
    if not force_save:
        if os.path.exists(filenamein):
            logging.debug("file already exists! "+str(filenamein))
            return
    sanitizedpath = filenamein# sanitizepath(filenamein)
    foldername = os.path.dirname(sanitizedpath)
    if len(foldername) >= 1:
        if not os.path.isdir(foldername):
            os.makedirs(foldername)
    file = open(sanitizedpath, "wb")
    file.write(data)
    file.close()



def delay(basetime,upperrandom=5):
    #replacement for using time.sleep, this adds a random delay to be sneaky
    sleeptime = basetime + random.randint(0,upperrandom)
    #logging.debug("pausing for "+str(sleeptime)+" ...")
    time.sleep(sleeptime)


def sanitizepath(pathin):
    #from pathsanitizer
    #sanitize a filepath for use on windows
    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247%28v=vs.85%29.aspx
    assert(type(pathin)==type(""))
    segments = []
    workingpath = pathin# make a copy for easier debugging
    #print "sanitizepathdebug! workingpath", workingpath
    #split the path into segments
    while True:
        workingpath, segment = os.path.split(workingpath)
        segments.append(segment)
        #print "sanitizepathdebug! segments, segment", segments, segment
        if len(workingpath) <= 1:
            break
    segments.reverse()
    #sanitize segments
    precessedsegments = []
    for segment in segments:
        s0 = re.sub('[^A-Za-z0-9\ \.\_]+', '-', segment)#remove all non-alphanumeric
        s1 = s0.strip()#strip whitespace so it doesn't get turned into hyphens
        s2 = re.sub('[<>:"/\|?*]+', '-',s1)#remove forbidden characters
        s3 = s2.strip()#strip whitespace
        s4 = s3.strip(".-")#strip characters that shouldn't be at ends of filenames
        s5 = re.sub(r"\ +", " ", s4)#remove repeated spaces
        s6 = re.sub(r"\-+", "-", s5)#remove repeated hyphens
        s7 = re.sub(r"\_+", "_", s6)#remove repeated underscores
        s8 = s7.strip()# Strip whitespace
        precessedsegments.append(s8)
    #join segments
    pathout = os.path.join(*precessedsegments)
    assert(type(pathout)==type(""))
    return pathout


def import_list(listfilename="ERROR.txt"):
    nameslist = []
    if os.path.exists(listfilename):#check if there is a list
        nameslist = []#make an empty list
        listfile = open(listfilename, 'rU')
        for line in listfile:
            if line[0] != '#' and line[0] != '\n':#skip likes starting with '#' and the newline character
                if line[-1] == '\n':#remove trailing newline if it exists
                    stripped_line = line[:-1]
                else:
                    stripped_line = line#if no trailing newline exists, we dont need to strip it
                replaced_line = re.sub(" ", '+', stripped_line)# Replace spaces with plusses
                nameslist.append(replaced_line)#add the username to the list
        listfile.close()
        return nameslist
    else:#if there is no list, make one
        listfile = open(listfilename, 'w')
        listfile.write('#add one tag per line, comments start with a #, nothing but tag on a lise that isnt a comment\n')
        listfile.close()
        return []


def append_list(lines,list_file_path="weasyl_done_list.txt",initial_text="# List of completed items.\n"):
    # Append a string or list of strings to a file; If no file exists, create it and append to the new file.
    # Strings will be seperated by newlines.
    # Make sure we're saving a list of strings.
    if ((type(lines) is type(""))or (type(lines) is type(u""))):
        lines = [lines]
    # Ensure file exists.
    if not os.path.exists(list_file_path):
        list_file_segments = os.path.split(list_file_path)
        list_dir = list_file_segments[0]
        if list_dir:
            if not os.path.exists(list_dir):
                os.makedirs(list_dir)
        nf = open(list_file_path, "w")
        nf.write(initial_text)
        nf.close()
    # Write data to file.
    f = open(list_file_path, "a")
    for line in lines:
        outputline = line+"\n"
        f.write(outputline)
    f.close()
    return


class config_handler():
    def __init__(self,settings_path="derpibooru_dl_config.cfg"):
        self.set_defaults()
        self.load_file(settings_path)
        self.save_settings(settings_path)

    def set_defaults(self):
        # Login
        self.api_key = ""
        # Download Settings
        self.reverse = False
        self.output_folder = "download"
        self.download_tags_list = True
        self.download_submission_ids_list = True
        self.filename_prefix = "derpi_"

    def load_file(self,settings_path):
        config = ConfigParser.RawConfigParser()
        if not os.path.exists(settings_path):
            return
        config.read(settings_path)
        # Login
        try:
            self.api_key = config.get('Login', 'api_key')
        except ConfigParser.NoOptionError:
            pass
        # Download Settings
        try:
            self.reverse = config.getboolean('Settings', 'reverse')
        except ConfigParser.NoOptionError:
            pass
        try:
            self.output_folder = config.get('Settings', 'output_folder')
        except ConfigParser.NoOptionError:
            pass
        try:
            self.download_tags_list = config.getboolean('Settings', 'download_tags_list')
        except ConfigParser.NoOptionError:
            pass
        try:
            self.download_submission_ids_list = config.getboolean('Settings', 'download_submission_ids_list')
        except ConfigParser.NoOptionError:
            pass

    def save_settings(self,settings_path):
        config = ConfigParser.RawConfigParser()
        config.add_section('Login')
        config.set('Login', 'api_key', self.api_key )
        config.add_section('Settings')
        config.set('Settings', 'reverse', str(self.reverse) )
        config.set('Settings', 'output_folder', self.output_folder )
        config.set('Settings', 'download_tags_list', str(self.download_tags_list) )
        config.set('Settings', 'download_submission_ids_list', str(self.download_submission_ids_list) )
        with open(settings_path, 'wb') as configfile:
            config.write(configfile)


def assert_is_string(object_to_test):
    """Make sure input is either a string or a unicode string"""
    if( (type(object_to_test) == type("")) or (type(object_to_test) == type(u"")) ):
        return
    logging.critical(str(locals()))
    raise(ValueError)


def decode_json(json_string):
    """Wrapper for JSON decoding"""
    assert_is_string(json_string)
    return json.loads(json_string)


def setup_browser():
    #Initialize browser object to global variable "br" using cokie jar "cj"
    # Browser
    global br
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    # User-Agent (this is cheating, ok?)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]


def search_for_query(settings,search_tag):
    """Perform search for a query on derpibooru.
    Return a lost of found submission IDs"""
    assert_is_string(search_tag)
    logging.debug("Starting search for tag: "+search_tag)
    page_counter = 0 # Init counter
    max_pages = 5000 # Saftey limit
    found_submissions = []
    last_page_items = []
    while page_counter <= max_pages:
        # Incriment page counter
        page_counter += 1
        logging.debug("Scanning page "+str(page_counter)+" for tag: "+search_tag)
        # Generate page URL
        search_url = "https://derpibooru.org/search.json?q="+search_tag+"&page="+str(page_counter)+"&key="+settings.api_key
        # Load page
        search_page = get(search_url)
        if search_page is None:
            break
        print search_page
        # Extract submission_ids from page
        # Convert JSON to dict
        search_page_list = decode_json(search_page)
        print search_page_list
        # Extract item ids
        this_page_item_ids = []
        for item_dict in search_page_list:
            item_id = item_dict["id_number"]
            this_page_item_ids.append(str(item_id))
        # Test if submissions seen are duplicates
        if this_page_item_ids == last_page_items:
            logging.debug("This pages items match the last pages, stopping search.")
            break
        last_page_items = this_page_item_ids
        # Append this pages item ids to main list
        found_submissions += this_page_item_ids
    # Return found items
    return found_submissions


def search_for_tag(settings,search_tag):
    """Perform search for a tag on derpibooru.
    Return a lost of found submission IDs"""
    assert_is_string(search_tag)
    logging.debug("Starting search for tag: "+search_tag)
    page_counter = 0 # Init counter
    max_pages = 5000 # Saftey limit
    found_submissions = []
    last_page_items = []
    while page_counter <= max_pages:
        # Incriment page counter
        page_counter += 1
        logging.debug("Scanning page "+str(page_counter)+" for tag: "+search_tag)
        # Generate page URL
        tag_url = "https://derpibooru.org/tags/"+search_tag+".json?page="+str(page_counter)+"&key="+settings.api_key
        # Load page
        search_page = get(tag_url)
        if search_page is None:
            break
        # Extract submission_ids from page
        # Convert JSON to dict
        search_page_dict = decode_json(search_page)
        # Extract item ids
        this_page_item_ids = []
        this_page_submissions = search_page_dict["images"]
        for item_dict in this_page_submissions:
            item_id = item_dict["id_number"]
            this_page_item_ids.append(str(item_id))
        # Test if submissions seen are duplicates
        if this_page_item_ids == last_page_items:
            logging.debug("This pages items match the last pages, stopping search.")
            break
        last_page_items = this_page_item_ids
        # Append this pages item ids to main list
        found_submissions += this_page_item_ids
    # Return found items
    return found_submissions


def copy_over_if_duplicate(settings,submission_id,output_folder):
    """Check if there is already a copy of the submission downloaded in the download path.
    If there is, copy the existing version to the suppplied output location then return True
    If no copy can be found, return False"""
    assert_is_string(submission_id)
    # Generate expected filename pattern
    expected_submission_filename = "*"+submission_id+".*"
    # Generate search pattern
    glob_string = os.path.join(settings.output_folder, "*", expected_submission_filename)
    print glob_string
    # Use glob to check for existing files matching the expected pattern
    glob_matches = glob.glob(glob_string)
    print glob_matches
    # Check if any matches, if no matches then return False
    if len(glob_matches) == 0:
        return False
    else:
        # If there is an existing version:
        for glob_match in glob_matches:
            # If there is an existing version in the output path, nothing needs to be copied
            if output_folder in glob_match:
                return True
            else:
                # Copy over submission file and metadata JSON
                print "copy to", output_folder
                # Check output folders exist
                # Build expected paths
                match_dir, match_filename = os.path.split(glob_match)
                expected_json_input_filename = submission_id+".json"
                expected_json_input_folder = os.path.join(match_dir, "json")
                expected_json_input_location = os.path.join(expected_json_input_folder, expected_json_input_filename)
                json_output_folder = os.path.join(output_folder, "json")
                json_output_filename = submission_id+".json"
                json_output_path = os.path.join(json_output_folder, json_output_filename)
                print json_output_path
                submission_output_path = os.path.join(output_folder,match_filename)
                # Ensure output path exists
                if not os.path.exists(json_output_folder):
                    os.makedirs(json_output_folder)
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                # Copy over files
                # Copy submission file
                shutil.copy2(glob_match, submission_output_path)
                # Copy JSON
                shutil.copy2(expected_json_input_location, json_output_path)
                return True




def download_submission(settings,search_tag,submission_id):
    """Download a submission from Derpibooru"""
    assert_is_string(search_tag)
    assert_is_string(submission_id)
    #logging.debug("Downloading submission:"+submission_id)
    # Build JSON paths
    json_output_filename = submission_id+".json"
    json_output_path = os.path.join(settings.output_folder,search_tag,"json",json_output_filename)
    # Check if download can be skipped
    # Check if JSON exists
    if os.path.exists(json_output_path):
        logging.debug("JSON for this submission already exists, skipping.")
        return
    # Check for dupliactes in download folder
    output_folder = os.path.join(settings.output_folder,search_tag)
    if copy_over_if_duplicate(settings, submission_id, output_folder):
        return
    # Build JSON URL
    json_url = "https://derpibooru.org/"+submission_id+".json?"+settings.api_key
    # Load JSON URL
    json_page = get(json_url)
    if json_page is None:
        return
    # Convert JSON to dict
    json_dict = decode_json(json_page)
    # Extract needed info from JSON
    image_url = json_dict["image"]
    image_filename = json_dict["file_name"]
    image_file_ext = json_dict["original_format"]
    # Build image output filenames
    image_output_filename = settings.filename_prefix+submission_id+"."+image_file_ext
    image_output_path = os.path.join(output_folder,image_output_filename)
    # Load image data
    authenticated_image_url = image_url+"?"+settings.api_key
    image_data = get(authenticated_image_url)
    if image_data is None:
        return
    # Save image
    save_file(image_output_path, image_data, True)
    # Save JSON
    save_file(json_output_path, json_page, True)
    return


def process_tag(settings,search_tag):
    """Download submissions for a tag on derpibooru"""
    assert_is_string(search_tag)
    #logging.info("Processing tag: "+search_tag)
    # Run search for tag
    submission_ids = search_for_tag(settings, search_tag)
    # Download all found items
    submission_counter = 0
    for submission_id in submission_ids:
        submission_counter+= 1
        logging.debug("Now working on submission "+str(submission_counter)+" of "+str(len(submission_ids) )+" : "+submission_id )
        download_submission(settings, search_tag, submission_id)
    return


def download_tags(settings,tag_list):
    for search_tag in tag_list:
        # remove invalid items
        if not re.search("[^\d]",search_tag):
            logging.debug("Only digits! skipping.")
            continue
        logging.info("Now processing tag "":"+search_tag)
        process_tag(settings, search_tag)
        append_list(search_tag, "config\\derpibooru_done_list.txt")


def download_submission_id_list(settings,submission_list):
    for submission_id in submission_list:
        # remove invalid items
        if re.search("[^\d]",submission_id):
            logging.debug("Not a submissionid")
            continue
        logging.info("Now trying submissionID: "+submission_id)
        download_submission(settings, "from_list", submission_id)


def main():
    # Load settings
    settings = config_handler("config\\derpibooru_dl_config.cfg")
    if len(settings.api_key) < 5:
        logging.warning("No API key set, weird things may happen.")
    # Load tag list
    tag_list = import_list("config\\derpibooru_dl_tag_list.txt")
    submission_list = tag_list #import_list("config\\derpibooru_dl_submission_id_list.txt")
    # DEBUG
    #download_submission(settings,"DEBUG","44819")
    #print search_for_tag(settings,"test")
    #process_tag(settings,"test")
    #copy_over_if_duplicate(settings,"134533","download\\flitterpony")
    #return
    # /DEBUG
    # Process each submission_id on tag list
    if settings.download_tags_list:
        download_tags(settings,tag_list)
    # Download individual submissions
    if settings.download_submission_ids_list:
        download_submission_id_list(settings,submission_list)



if __name__ == '__main__':
    # Setup logging
    setup_logging("debug\\derpibooru_dl_log.txt")
    try:
        cj = cookielib.LWPCookieJar()
        setup_browser()
        main()
    except Exception, e:
        # Log exceptions
        logger.critical("Unhandled exception!")
        logging.exception(e)
    logging.info( "Program finished.")
    #raw_input("Press return to close")
