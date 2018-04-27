#!/usr/bin/env python3
# In[]
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import warnings
warnings.filterwarnings("ignore")

# Set option(s):
option = webdriver.ChromeOptions()
# Use incognito, otherwise results will be biased by search history
option.add_argument("--incognito")

# Create new instance of chrome in incognito mode
browser = webdriver.Chrome(executable_path='/Library/Application Support/Google/chromedriver', chrome_options=option)

# In[]
import re, os
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
# Grab the newest screenshot from disk located in this directory
screenshot_dir = '/Users/pshih/Desktop/'

# Combine the filenames of screenshots in dir and the modified date into a list
screenshots = [[filename, os.path.getmtime(screenshot_dir+filename)] for filename in os.listdir(screenshot_dir) if 'Screen Shot' in filename]

# Assume that the newest one has the most recent modified date...
# Sort descending by the 2nd column which contains modified date using get_key() defined above
screenshots_sorted = sorted(screenshots, key=get_key, reverse=True)
# Save full path to image in a variable
imagefile = screenshot_dir + screenshots_sorted[0][0]

# In[]
# Load the image file
img = Image.open(imagefile)

# First crop the image to exclude the OS bar at the top and chat box at the bottom
img = img.crop((0, int(img.height*0.18), img.width, int(img.height*0.7)))

# Apply OCR on the screenshot to get the text
hqtext = pytesseract.image_to_string(img)

# Clean the text of new lines \n and then split questions and answers into
# separate elements in an array
hqtext_split = clean_text(hqtext)

# Get the question text and 3 answers text
for i, text in enumerate(hqtext_split):
    if '?' in text:
        startIdx = i
        break
 
hq_question = hqtext_split[startIdx]
hq_answers = hqtext_split[startIdx+1:startIdx+4]
print(hq_question)
print(hq_answers)

# In[]
# Query using google, exclude the '?' char in the question
query_str = '(' + hq_question[:-1] + ') AND (' + ' OR '.join(hq_answers) + ')'
browser.get('https://www.google.com/search?q=' + query_str)

# Wait up to T seconds for page to load
T = 4
try: 
    # Search results are dynamically populated on the page, so this CSS selector
    # targets the div container for each returned page
    WebDriverWait(browser, T).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div#search div.g')))
except TimeoutException:
    print("Timed out waiting for page to load")
    browser.quit()

# In[]
# Get search results
search_title_elements = browser.find_elements_by_css_selector('div[data-hveid]>div.rc>h3.r>a')
search_summaries_elements = browser.find_elements_by_css_selector('div[data-hveid]>div.rc>div.s>div>span.st')
search_similar_elements = browser.find_elements_by_css_selector('div.card-section a')

search_results = list()

# Append the title string with the summary string for one long paragraph
for title, summary in zip(search_title_elements, search_summaries_elements):
    search_results.append(title.text + ' ' + summary.text)

# Also include any suggested similar search queries
for sim in search_similar_elements:
    search_results.append(sim.text)

# Create a 2D array to store instance count of each answer in returned search
results = np.zeros([len(search_results), len(hq_answers)])

for i, result in enumerate(search_results):
    for j, answer in enumerate(hq_answers):
        # First, pick the longest word in the answer to use for substring match
        # (relevant for multi-word answers)
        ans_split = re.split(' ',answer)
        wordLength = [len(w) for w in ans_split]
        longestWord_idx = np.array(wordLength).argmax()

        # Quick-n-dirty way to remove plural suffixes...
        if ans_split[longestWord_idx][-3:] == 'ies':
            ans = ans_split[longestWord_idx][:-3]
        elif ans_split[longestWord_idx][-1] == 's':
            ans = ans_split[longestWord_idx][:-1]
        else:
            ans = ans_split[longestWord_idx]
        
        # Find any instance of the answer in each returned search result
        # (case insensitive)
        results[i][j] = any(re.findall(r'(?i)\b'+ans, result))
        
        # Weigh wiki results more
        if 'Wikipedia' in result:
            results[i][j] *= 2 

# Down-weigh search result instances that contain more than one answer option...
# This is bc there can only be one correct answer!
R = results/(results>0).sum(axis=1)[:,None]

# Replace NaN elements with 0
R[np.isnan(R)] = 0

if R.sum() == 0:
    print('dunno')
elif ' NOT ' in hq_question or 'except' in hq_question:
    # If this is an inversion-type question, then we want the minimum
    print(hq_answers[np.dot(R.T,R).diagonal().argmin()]) #lowest "variance"
else:
    print(hq_answers[np.dot(R.T,R).diagonal().argmax()]) #highest "variance"

