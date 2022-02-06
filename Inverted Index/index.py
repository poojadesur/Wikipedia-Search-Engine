import xml.sax
import json
import re
import collections
import nltk
import Stemmer
import string
import sys 
import os

stopwords = ['jpg','png','reflist','i','me','my','myself','we','our','ours','ourselves','you',"you're","you've","you'll","you'd",'your','yours','yourself','yourselves','he','him','his','himself','she',"she's",'her','hers','herself','it',"it's",'its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that',"that'll",'these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the','and','but','if','or','because','as','until','while','of','at','by','for','with','about','against','between','into','through','during','before','after','above','below','to','from','up','down','in','out','on','off','over','under','again','further','then','once','here','there','when','where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','s','t','can','will','just','don',"don't",'should',"should've",'now','d','ll','m','o','re','ve','y','ain','aren',"aren't",'couldn',"couldn't",'didn',"didn't",'doesn',"doesn't",'hadn',"hadn't",'hasn',"hasn't",'haven',"haven't",'isn',"isn't",'ma','mightn',"mightn't",'mustn',"mustn't",'needn',"needn't",'shan',"shan't",'shouldn',"shouldn't",'wasn',"wasn't",'weren',"weren't",'won',"won't",'wouldn',"wouldn't"]


INVERTED_INDEX_PATH = ""
WIKI_DUMP_PATH = ""
STAT_PATH = ""

DICT_DIR = "./blocks"
os.mkdir(DICT_DIR)

# os.mkdir("../inverted_indexes")

# dict with preprocessed tokens as keys, processed token counter calculated while merging
PREPROCESSED = {}

def clean_text(text):

    cleaned_text = []

    text = text.replace('\t', ' ').replace('\n', ' ')
    text = re.sub(r'https?:\/\/\S+ ' , '' , text)
    
    for punctuation in string.punctuation:
        text = text.replace(punctuation, ' ')  

    text = re.sub("[^A-Za-z0-9]"," ", text)

    preprocessedtokens = text.split()
    for pptoken in preprocessedtokens:
        if(pptoken.lower() not in PREPROCESSED.keys()): PREPROCESSED[pptoken.lower()] = 1

    text = text.split()

    

    # print(text)
    no_stop_words = set(text) - set(stopwords)
    no_stop_words = [word.lower() for word in no_stop_words if not word.isdigit() or (word.isdigit() and len(word) == 4)]
    # removing stop words and Stemming the remaining words in the text
    stemmer = Stemmer.Stemmer("english")

    cleaned_text = stemmer.stemWords(no_stop_words)
    cleaned_text = ' '.join(cleaned_text)

    return cleaned_text 
  
def preprocessing(egtext):
    egtext = re.sub("\n", "", egtext)
    egtext = re.sub(' +', ' ', egtext)
    return egtext

def getTitleTokens(title):
    title = clean_text(title)
    title = title.split()
    return title

# Infobox
def getInfoboxTokens(egtext):

    infobox = ""

    totallen = len(egtext)

    iter = re.finditer(r"{{Infobox", egtext)
    indices = [m.start(0) for m in iter]

    # print((indices))

    infobox_End_idx = 0

    for i in indices:
        # print(type(i))
        vp = []
        vp.append('open')
        it = i+2
        while(len(vp) != 0):
            # print(egtext[it])
            if(egtext[it] == "{" and egtext[it+1] == "{"): 
                # print("pushing")
                # print(len(vp))
                vp.append("open")

            elif(egtext[it] == "}" and egtext[it+1] == "}"): 
                # print("popping")
                vp.pop()

            elif(len(vp) == 1): infobox += egtext[it]
            it += 1

            infobox_End_idx = it


            if(it+1 > totallen): break

    infobox = re.sub("Infobox", "", infobox)

    iter = re.finditer(r" \| ", infobox)
    indices = [m.start(0) for m in iter]
    indices

    infoboxx = ""

    start = 0

    for i in indices:
        equal = 0
        end = i
        # print(start+1,end)
        for j in range(start,end+1):
            if(equal == 1): infoboxx += infobox[j]
            elif(infobox[j] == "="): equal = 1
        start = i

    infoboxx = clean_text(infoboxx)

    infobox = infoboxx.split()  
    # print("\nINFOBOX", infobox,"\n")

    return infobox,infobox_End_idx

# Category
def getCategoryTokens(egtext):

    pattern = "\[\[Category:(.*?)\]\]"
    substring = re.findall(pattern, egtext)

    iter = re.finditer(pattern, egtext)
    indices = [m.start(0) for m in iter]
    if(len(indices) == 0): indices = [0]

    substring = [clean_text(ss) for ss in substring]

    substring = [ss.split() for ss in substring]
    substring = [s for a in substring for s in a ]

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

    links = extlinks.split('*')
    # print(links)

    l = []

    for link in links:
        # print("link ", link)
        link = re.sub(r'https?:\/\/\S+' , '' , link)
        link = re.sub(r'{{(.*?)}}' , '' , link)
        link = clean_text(link)
        l.append(link.split())
        # print("link ", link)
    l = [word for eachlink in l for word in eachlink]
    return l, start_index

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

    refs = refs.split()
    # print(refs)

    return refs, start_index

def getBodyTokens(egtext):
    egtext = clean_text(egtext)
    return egtext.split()

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
        self.prev_dict = {}

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
            iiformat += docid + "-"
            for f in token_dict[docid].keys():
                iiformat += str(f)
                iiformat += str(token_dict[docid][f])
            
            iiformat += "|"
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
            self.text = preprocessing(self.text)

            # if self.docid%1000 == 0:print("doc id is ", self.docid)

            self.cur_page['t'] = getTitleTokens(self.title)
            self.cur_page['i'],infobox_end_idx = getInfoboxTokens(self.text)

            self.cur_page['c'],cat_start_idx = getCategoryTokens(self.text)
            if cat_start_idx == 0: cat_start_idx =  len(self.text)

            self.cur_page['l'], link_start_idx = getExternalLinkTokens(self.text)
            if link_start_idx == 0: link_start_idx =  len(self.text)

            self.cur_page['r'], ref_start_idx = getReferenceTokens(self.text)
            if ref_start_idx == 0: ref_start_idx =  len(self.text)

            min_end_idx = min(cat_start_idx, link_start_idx, ref_start_idx)

            self.cur_page['b'] = getBodyTokens(self.text[infobox_end_idx:min_end_idx])

            self.addToDict()
            
            self.page += 1

            if(self.page > 5000):
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
           
def merge():

    l = os.listdir(DICT_DIR) # dir is your directory path
    number_files = len(l)
    # print ("number of files ",number_files)

    # creating inverted index file
    f = open(INVERTED_INDEX_PATH,'+w')

    NUM_CHUNKS = number_files + 1

    reached_eof = [False for i in range(1,NUM_CHUNKS)]
    
    filelines = []
    files = []
    lastpos = []
    tokens = []
    prevpos = 0

    processed = 0

    for i in range(1,NUM_CHUNKS):
        files.append(DICT_DIR + '/dictionary' + str(i) + '.txt')

    filepointers = [open(f,'r') for f in files]

    for fi in filepointers:

        line = fi.readline()
        filelines.append(line)

        token = re.search(r"^[^:]*",line).group(0)
        tokens.append(token)

        # print(f.tell())
        lastpos.append(fi.tell())

    filepointers.append(open(INVERTED_INDEX_PATH,'+w'))

    while(not all(reached_eof)):

        mintoken = min(tokens)
        fileno = tokens.index(mintoken)

        # reached eof
        if(mintoken == ''): 
            # print("this file is empty ", fileno)
            reached_eof[fileno] = True
            tokens[fileno] = "~~~~~~~~~~~~"
            continue

        # reading new line from file with min token atm to replace the one being compared
        filepointers[fileno].seek(lastpos[fileno])
        newline = filepointers[fileno].readline()
        lastpos[fileno] = filepointers[fileno].tell()

        # if min word read is last token in inverted index, merge
        filepointers[NUM_CHUNKS-1].seek(prevpos)
        indexline = filepointers[NUM_CHUNKS-1].readline()
        lastTokenpos = prevpos
        prevpos = filepointers[NUM_CHUNKS-1].tell()

        indextoken = str(re.search(r"^[^:]*",indexline).group(0))

        if mintoken == indextoken:
            prevpos = lastTokenpos
            s1 = indexline[:-1]
            s2 = filelines[fileno].replace(mintoken + ":","")
            s1 = (s1 + s2)
            filepointers[NUM_CHUNKS-1].seek(prevpos)
            filepointers[NUM_CHUNKS-1].write(s1)

        if mintoken != indextoken:
            processed += 1
            filepointers[NUM_CHUNKS-1].seek(prevpos)
            filepointers[NUM_CHUNKS-1].write(filelines[fileno])
        
        filelines[fileno] = newline
        token = re.search(r"^[^:]*",newline).group(0)
        tokens[fileno] = token
    
    os.walk(DICT_DIR)
    for root, dirs, files in os.walk(DICT_DIR, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
    
    os.rmdir(DICT_DIR)

    return processed

if(__name__ == "__main__"):

    WIKI_DUMP_PATH = sys.argv[1]
    INVERTED_INDEX_PATH = sys.argv[2] + '/index.txt'
    STAT_PATH = sys.argv[3]

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces,0)
    Handler = WikiHandler()
    parser.setContentHandler(Handler)
    parser.parse(WIKI_DUMP_PATH)

    processed = merge()

    f = open(STAT_PATH,"+w")
    f.write(str(len(PREPROCESSED)))
    f.write('\n')
    f.write(str(processed))



  