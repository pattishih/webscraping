## HQ Game Python Automation Experiment
*See blog post [here](https://pattishih.com/project-a-nostalgic-look-back-at-hq-trivia-and-my-get-rich-quick-python-automation-experiment/).*

This was a proof-of-concept python script that I worked on a little while ago to see if we can use the power of Google search for HQ trivia. All one would need to do is mirror the device onto the desktop and take screenshots or take screenshots from the device's end but have the file save directly onto the computer (doable from Xcode app).

The script (1) reads in the newest screenshot from disk, (2) applies OCR on the text with tesseract, (3) runs a google search using Selenium, and (4) parses the results to return the most likely answer. Details about how I ran the search and how the results were treated for selecting an answer are provided as comments within hq\_websearch\_clean.py

* _hq\_websearch\_practice.py_ - the script that I had used for trying various methods... sporadically commented throughout
* _hq\_websearch\_clean.py_ - the cleaned up script with extra stuff from \_practice removed... commented more thoroughly

As of April 25, 2018, it still works well after question 2/3, giving the correct answer approximately 80% of the time. The first 2-3 questions are usually easy with an obvious answer and, I suspect, are specifically formulated to weed out bots playing the game... 

I recently realized that other people have already tried something similar to what I have here and some were actually using these automated methods to cheat. **I have never used this code to cheat the game and would advise anyone against doing so.** I wrote it as a proof-of-concept, and it was an opportunity to play around with Selenium. I should also note that using automated means to scrape from Google's website was once against TOS. It might still be, but from a quick skim, I couldn't find its mention in their 2017 terms.
