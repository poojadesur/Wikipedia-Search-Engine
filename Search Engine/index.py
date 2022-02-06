import xml.sax
import json
import re
import collections
import Stemmer
import string
import sys 
import os
import heapq
import time

startime = time.time()

stopwords = ['jpg','png','reflist','i','me','my','myself','we','our','ours','ourselves','you',"you're","you've","you'll","you'd",'your','yours','yourself','yourselves','he','him','his','himself','she',"she's",'her','hers','herself','it',"it's",'its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that',"that'll",'these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the','and','but','if','or','because','as','until','while','of','at','by','for','with','about','against','between','into','through','during','before','after','above','below','to','from','up','down','in','out','on','off','over','under','again','further','then','once','here','there','when','where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','s','t','can','will','just','don',"don't",'should',"should've",'now','d','ll','m','o','re','ve','y','ain','aren',"aren't",'couldn',"couldn't",'didn',"didn't",'doesn',"doesn't",'hadn',"hadn't",'hasn',"hasn't",'haven',"haven't",'isn',"isn't",'ma','mightn',"mightn't",'mustn',"mustn't",'needn',"needn't",'shan',"shan't",'shouldn',"shouldn't",'wasn',"wasn't",'weren',"weren't",'won',"won't",'wouldn',"wouldn't"]

INVERTED_INDEX_PATH = ""
WIKI_DUMP_PATH = ""
STAT_PATH = ""

TITLE_PATH = "./titles.txt"
titlefile = open(TITLE_PATH,'+w')

DICT_DIR = "./blocks"
if(not os.path.exists(DICT_DIR)): os.mkdir(DICT_DIR)

# dict with preprocessed tokens as keys, processed token counter calculated while merging
PREPROCESSED = {}

# takes string, returns list of tokens
def clean_text(text):

    cleaned_text = []

    #removing hyperlink of urls
    text = re.sub(r'https?:\/\/\S+ ' , '' , text)

    #removing non alphanumeric characters, replacing by space
    text = re.sub("[^A-Za-z0-9]"," ", text)

    preprocessedtokens = text.split()
    for pptoken in preprocessedtokens:
        if(pptoken.lower() not in PREPROCESSED.keys()): PREPROCESSED[pptoken.lower()] = 1

    text = text.split()

    # print(text)

    #removing stop words and lower casing words
    no_stop_words = set(text) - set(stopwords)
    no_stop_words = [word.lower() for word in no_stop_words if not word.isdigit() or (word.isdigit() and len(word) == 4)]
    
    # Stemming the remaining words in the text
    stemmer = Stemmer.Stemmer("english")
    cleaned_text = stemmer.stemWords(no_stop_words)

    return cleaned_text 
  
def preprocessing(egtext):
    egtext = re.sub("\n", "", egtext)
    egtext = re.sub(' +', ' ', egtext)
    return egtext

def getTitleTokens(title):
    title = clean_text(title)
    return title

# Infobox - returns body of text without infoboxes, infobox list of tokens
def getInfoboxTokens(egtext):
    # print(egtext)
    infobox = ""

    totallen = len(egtext)

    iter = re.finditer(r"{{Infobox", egtext)
    indices = [m.start(0) for m in iter]

    if(len(indices) != 0): infobox_start_idx = indices[0] + 2
    else: infobox_start_idx = 0
    infobox_End_idx = 0

    egtextremoved = []

    for i in indices:
        stack = 2
        it = i+2
        infobox_start_idx = it

        while(stack != 0):
            if(egtext[it] == "{"): 
                stack += 1
            elif(egtext[it] == "}"): 
                stack -= 1
            elif(stack == 2): infobox += egtext[it]
            it += 1
            infobox_End_idx = it
            if(it+1 > totallen): break

        egtextremoved.append(egtext[infobox_start_idx:infobox_End_idx])

    for i in egtextremoved:
        egtext = egtext.replace(i," ")

    infobox = re.sub("Infobox", "", infobox)

    iter = re.finditer(r"\| ", infobox)
    indices = [m.start(0) for m in iter]

    infoboxx = ""

    start = 0

    for i in indices:
        equal = 0
        end = i
        for j in range(start,end+1):
            if(equal == 1): infoboxx += infobox[j]
            elif(infobox[j] == "="): equal = 1
        start = i

    infoboxx = clean_text(infoboxx)

    return egtext,infoboxx

# Category
def getCategoryTokens(egtext):

    pattern = "\[\[Category:(.*?)\]\]"
    substring = re.findall(pattern, egtext)
    substring = ' '.join(substring)
    substring = clean_text(substring)

    iter = re.finditer(pattern, egtext)
    indices = [m.start(0) for m in iter]
    if(len(indices) == 0): indices = [0]

    # print("\nCategory: ", substring,"\n")
    return substring,indices[0]

# External Links
def getExternalLinkTokens(egtext):

    extlinks = re.search(r'=+External [l,L]inks?=+(.*?)==+',egtext)
    if extlinks is not None: 
        start_index = extlinks.start()
        extlinks = extlinks.group(1)

    else: 
        extlinks = re.search(r'=+External [l,L]inks?=+(.*?)\[\[Category',egtext)
        if (extlinks) is not None: 
            start_index = extlinks.start()
            extlinks = extlinks.group(1)
            
        else: return "",0

        # print(extlinks)

    links = ' '.join(extlinks.split('*'))
    links = re.sub(r'{{(.*?)}}' , '' , links)
    links = clean_text(links)
    # print(links)

    return links, start_index

def getReferenceTokens(egtext):

    refs = re.search(r'=+[R,r]eferences=+(.*?)==+',egtext)
    if (refs) is not None: 
        start_index = refs.start()
        refs = refs.group(1)

    else: 
        refs = re.search(r'=+[R,r]eferences=+(.*?)\[\[Category',egtext)
        if refs is not None: 
            start_index = refs.start()
            refs = refs.group(1)
        
        else:
            return "",0
        
    refs = re.sub(r'[\{\{\}\}]' , ' ' , refs)
    refs = re.sub(r' +' , ' ' , refs)
    refs = re.sub(r'[r,R]eflist' , ' ' , refs)
    refs = clean_text(refs)

    # print(refs)

    return refs, start_index

def getBodyTokens(egtext):
    egtext = clean_text(egtext)
    return egtext

class WikiHandler(xml.sax.handler.ContentHandler):
    
    def __init__(self):
        self.tag = ""
        self.title = ""
        self.text = ""
        self.iptext = []
        self.id = ""
        self.docid = -1

        self.chunkid = 1
        self.page = 0

        self.cur_page = {}
        self.cur_dict = {}

    def addToDict(self):

        for field in self.cur_page.keys():
            for token in self.cur_page[field]:
                # initialising word dict - word: docid : field : frequency
                docidkey = "d" + str(self.docid)
                if(token not in self.cur_dict.keys()): 
                    self.cur_dict[token] = {}
                    self.cur_dict[token][docidkey] = {}
                else:
                    if docidkey not in self.cur_dict[token].keys(): self.cur_dict[token][docidkey] = {}

                if(field in self.cur_dict[token][docidkey].keys()): self.cur_dict[token][docidkey][field] += 1
                else: self.cur_dict[token][docidkey][field] = 1

    def getInvertedIndexFormat(self,token,token_dict):

        iiformat = token + ":"

        for docid in token_dict.keys():
            # iiformat += docid + "-"
            iiformat += hex(docid)
            for f in token_dict[docid].keys():
                iiformat += str(f)
                iiformat += str(hex(token_dict[docid][f]))
            
            # iiformat += "|"
        return iiformat

    # Call when an element starts
    def startElement(self, name, attrs):

        self.tag = name
        if name == "page": 
            self.docid += 1

    # Call when an elements ends
    def endElement(self, name):
            
        if name == "text":
            
            self.text = "".join(self.iptext)
            titlefile.write(self.title)

            self.text = preprocessing(self.text)

            if self.docid%1000 == 0:print("doc id is ", self.docid,flush=True)

            self.cur_page['T'] = getTitleTokens(self.title)
            self.text,self.cur_page['I'] = getInfoboxTokens(self.text)

            self.cur_page['C'],cat_start_idx = getCategoryTokens(self.text)
            if cat_start_idx == 0: cat_start_idx =  len(self.text)

            self.cur_page['L'], link_start_idx = getExternalLinkTokens(self.text)
            if link_start_idx == 0: link_start_idx =  len(self.text)

            self.cur_page['R'], ref_start_idx = getReferenceTokens(self.text)
            if ref_start_idx == 0: ref_start_idx =  len(self.text)

            min_end_idx = min(cat_start_idx, link_start_idx, ref_start_idx)

            self.cur_page['B'] = getBodyTokens(self.text[:min_end_idx])

            self.addToDict()
            
            self.page += 1

            if(self.page > 10000):

                current_time = time.time()
                print("Time running for " + str((current_time - startime)/60) + " minutes",flush=True)

                ordered_dict = collections.OrderedDict(sorted(self.cur_dict.items()))

                with open(DICT_DIR + '/dictionary' + str(self.chunkid) + '.txt','+a') as f:

                    for t,v in ordered_dict.items():
                        iiformat = self.getInvertedIndexFormat(t,v) + "\n"
                        f.write(iiformat)
                
                ordered_dict.clear()
                self.chunkid += 1
                self.cur_dict.clear()
                self.page = 0

            self.text = ""
            self.iptext.clear()
            self.title = ""

       # Call when a character is read
    
    def characters(self, content):
        if self.tag == "title":
            self.title += content
        if self.tag == "text":
            self.iptext.append(content)
           
class Word:

    def __init__(self, word, line, fileno):
        self.word = word
        self.line = line
        self.fileno = fileno
    
    def __lt__(self,nxt):
        
        if self.word != nxt.word : 
            return self.word < nxt.word
        else : return self.fileno < nxt.fileno

def merge():

    mergetime = time.time()
    print("Started merge after" + str(mergetime - startime) + " minutes",flush=True)

    l = os.listdir(DICT_DIR) # dir is your directory path
   
    number_files = len(l)
    NUM_CHUNKS = number_files + 1

    # print ("number of files ",number_files)

    if(not os.path.exists(INVERTED_INDEX_DIR)): os.mkdir(INVERTED_INDEX_DIR)

    # creating inverted index file
    indexname = ['0123456789abcdefghijklmnopqrstuvwxyz']
    indexFiles = [open(INVERTED_INDEX_DIR + "/index_file_" + i + ".txt",'+w') for i in indexname]
    indexFileno = 0
    
    files = []
    tokens = []

    processed = 0

    for i in range(1,NUM_CHUNKS):
        files.append(DICT_DIR + '/dictionary' + str(i) + '.txt')

    filepointers = [open(f,'r') for f in files]

    fileno = 0

    for fi in filepointers:

        line = fi.readline().strip('\n')
        data = line.split(":")
        token = Word(data[0],data[1],fileno)
        tokens.append(token)

        fileno += 1

    heapq.heapify(tokens)

    while len(tokens):

        # print(len(tokens))

        mintoken = tokens[0].word
        fileno = tokens[0].fileno
        line = ""
        processed += 1
        # print(mintoken)

        if(mintoken == ''): 
            continue
        
        if mintoken[0].isdigit(): indexFileno = 0
        else: indexFileno = ord(mintoken[0]) - 96

        while len(tokens) and mintoken == tokens[0].word:

            line += tokens[0].line
            fileno = tokens[0].fileno
            heapq.heappop(tokens)

            newline = filepointers[fileno].readline().strip('\n')
            newdata = newline.split(":")
            if newdata[0] != '':
                newtoken = Word(newdata[0],newdata[1],fileno)
                heapq.heappush(tokens,newtoken)
        try:
            indexFiles[indexFileno].write(mintoken+":"+line+"\n")
        except:
            print(indexFileno,flush=True)

    os.walk(DICT_DIR)
    for root, dirs, files in os.walk(DICT_DIR, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
    
    os.rmdir(DICT_DIR)

    mergeendtime = time.time()
    print("Ended merge after " + str((mergeendtime - mergetime)/60) + " minutes",flush=True)

    return processed

if(__name__ == "__main__"):

    WIKI_DUMP_PATH = sys.argv[1]
    INVERTED_INDEX_DIR = sys.argv[2]
    STAT_PATH = "./stats.txt"

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces,0)
    Handler = WikiHandler()
    parser.setContentHandler(Handler)
    parser.parse(WIKI_DUMP_PATH)

    processed = merge()

    f = open(STAT_PATH,"+w")
    # f.write(str(len(PREPROCESSED)))
    # f.write('\n')
    f.write(str(processed))



  