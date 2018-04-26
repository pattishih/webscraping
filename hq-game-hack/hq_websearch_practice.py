#!/usr/bin/env python3
# In[]
from selenium import webdriver
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import warnings
warnings.filterwarnings("ignore")

# Set option(s):
option = webdriver.ChromeOptions()
option.add_argument("--incognito")

# Create new instance of chrome in incognito mode
browser = webdriver.Chrome(executable_path='/Library/Application Support/Google/chromedriver', chrome_options=option)

# In[]
import re, os, time
#import bs4, urilib2
#from bs4 import BeautifulSoup
#from nltk import word_tokenize
import numpy as np
from PIL import Image
import pytesseract


# Set path to tesseract command for wrapper to work
#   Note to self: Find out why it isn't already in PATH
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

# In[]
def clean_text (text_in):
    text_split = re.split('\n\n', text_in)
    return [re.sub('\n',' ',text) for i, text in enumerate(text_split)]

def get_key(row):
    return row[1]

# In[]
# Grab the screenshot from disk
screenshot_dir = '/Users/pshih/Desktop/'

# Get the filenames of screenshots and also the modified date
# Assume that the newest one has the most recent modified date...
screenshots = [[filename, os.path.getmtime(screenshot_dir+filename)] for filename in os.listdir(screenshot_dir) if 'Screen Shot' in filename]
screenshots_sorted = sorted(screenshots, key=get_key, reverse=True)
imagefile = screenshot_dir + screenshots_sorted[0][0]

  
# Get the question from the screenshot
img = Image.open(imagefile)
img = img.crop((0, int(img.height*0.18), img.width, int(img.height*0.7)))
hqtext = pytesseract.image_to_string(img)

hqtext_split = clean_text(hqtext)

# Get the question text and 3 answers
for i, text in enumerate(hqtext_split):
    if '?' in text:
        startIdx = i
        break
 
hq_question = hqtext_split[startIdx]
hq_answers = hqtext_split[startIdx+1:startIdx+4]

'''
#------------
# The following block is used for running OCR on screenshots after having lost.
# The answers options have low contrast so tesseract does not perform well without
# some image contrast/brightness manipulation

import cv2
from pylab import array

# Get the 3 answer options
grayimage = cv2.cvtColor(cv2.imread(imagefile), cv2.COLOR_BGR2GRAY)
dim = grayimage.shape

#cv2.startWindowThread()
#cv2.namedWindow("preview")

# Parameters for manipulating image data
maxIntensity = 255.0
phi = 1.0
theta = 100

grayimage_adjusted = (maxIntensity/phi) * (grayimage[int(dim[0]*.18):-int(dim[0]*.30),:]/(maxIntensity/theta))**0.35
grayimage_adjusted = array(grayimage_adjusted,dtype='uint8')

#grayimage_adjusted = cv2.threshold(grayimage_adjusted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

#cv2.imshow('preview', grayimage_adjusted)
#cv2.destroyAllWindows()

imagefile_tmp = "{}.png".format(os.getpid())
cv2.imwrite(imagefile_tmp, grayimage_adjusted)

hqtext = pytesseract.image_to_string(Image.open(imagefile_tmp))
os.remove(imagefile_tmp)  

hqtext_split = clean_text(hqtext)
hq_answers = hqtext_split[-3:]
'''
#------------------------------------------------------------------------------
# Query using google, exclude the '?' in the question
query_str = '(' + hq_question[:-1] + ') AND (' + ' OR '.join(hq_answers) + ')'
browser.get('https://www.google.com/search?q=' + query_str)
#inputElement = browser.find_element_by_id('lst-ib')
#inputElement.send_keys('(' + hq_question + ') AND (' + ' OR '.join(hq_answers) + ')')
#inputElement.send_keys(Keys.ENTER)

time.sleep(.2)

# Wait up to T seconds for page to load
#T = 3
#try: 
#    WebDriverWait(browser, T).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div#search div.g')))
#except TimeoutException:
#    print("Timed out waiting for page to load")
#    browser.quit()

#------------------------------------------------------------------------------
# Get search results
#searchterms = browser.find_element_by_xpath("//input[@id='lst-ib']").get_attribute('value')
#searchterms_split = re.split('\(|\)',searchterms)[0:-1]
#hq_question = searchterms_split[0]
#hq_answers = re.split(' or ',searchterms_split[-1])
print(hq_question)
print(hq_answers)

search_title_elements = browser.find_elements_by_css_selector('div[data-hveid]>div.rc>h3.r>a')
search_summaries_elements = browser.find_elements_by_css_selector('div[data-hveid]>div.rc>div.s>div>span.st')
search_similar_elements = browser.find_elements_by_css_selector('div.card-section a')
search_results = list()

for title, summary in zip(search_title_elements, search_summaries_elements):
    search_results.append(title.text + ' ' + summary.text)

for sim in search_similar_elements:
    search_results.append(sim.text)

results = np.zeros([len(search_results), len(hq_answers)])
    
for i, result in enumerate(search_results):
    for j, answer in enumerate(hq_answers):
        #print(hq_answers[j], search_summaries_elements[i].text)
        #print()
        ans_split = re.split(' ',answer)
        wordLength = [len(w) for w in ans_split]
        longestWord_idx = np.array(wordLength).argmax()
        '''
        # Gerunds suck. They are usually short verbs that are not often meaningful,
        # but made long with -ing
        if ans_split[longestWord_idx][-3:] == 'ing' and len(wordLength) > 1:
            longestWord_idx = sorted(zip(wordLength,list(range(3))), reverse=True)[1][1]
        '''

        # Crude way to remove plural suffixes...
        if ans_split[longestWord_idx][-3:] == 'ies':
            ans = ans_split[longestWord_idx][:-3]
        elif ans_split[longestWord_idx][-1] == 's':
            ans = ans_split[longestWord_idx][:-1]
        else:
            ans = ans_split[longestWord_idx]
        
        # Find an instance of the answer in each returned search result
        # (case insensitive)
        results[i][j] = any(re.findall(r'(?i)\b'+ans, result))
        
        if 'Wikipedia' in result:
            results[i][j] *= 2 #weigh wiki results more

# Down-weigh search result instances that contain more than one answer
R = results/(results>0).sum(axis=1)[:,None]
R[np.isnan(R)] = 0
if R.sum() == 0:
    print('dunno')
elif ' NOT ' in hq_question or 'except' in hq_question:
    print(hq_answers[np.dot(R.T,R).diagonal().argmin()]) #variance
#    print(hq_answers[R.sum(axis=0).argmin()]) #sum
else:
    print(hq_answers[np.dot(R.T,R).diagonal().argmax()]) #variance
#    print(hq_answers[R.sum(axis=0).argmax()]) #sum
