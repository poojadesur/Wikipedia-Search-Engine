import re
import json
import string
import sys
import Stemmer
import math
import collections
import time

QUERY = ""
OUTPUT_FILE = open("./2019101112_queries_op.txt","w")

stopwords = ['i','me','my','myself','we','our','ours','ourselves','you',"you're","you've","you'll","you'd",'your','yours','yourself','yourselves','he','him','his','himself','she',"she's",'her','hers','herself','it',"it's",'its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that',"that'll",'these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the','and','but','if','or','because','as','until','while','of','at','by','for','with','about','against','between','into','through','during','before','after','above','below','to','from','up','down','in','out','on','off','over','under','again','further','then','once','here','there','when','where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','s','t','can','will','just','don',"don't",'should',"should've",'now','d','ll','m','o','re','ve','y','ain','aren',"aren't",'couldn',"couldn't",'didn',"didn't",'doesn',"doesn't",'hadn',"hadn't",'hasn',"hasn't",'haven',"haven't",'isn',"isn't",'ma','mightn',"mightn't",'mustn',"mustn't",'needn',"needn't",'shan',"shan't",'shouldn',"shouldn't",'wasn',"wasn't",'weren',"weren't",'won',"won't",'wouldn',"wouldn't"]

def clean_text(queries):

  tokens = []

  for text in queries:

    text = text.replace('\t', '').replace('\n', '')
    text = re.sub(r'https?:\/\/\S+ ' , '' , text)
    
    for punctuation in string.punctuation:
        text = text.replace(punctuation, '')  

    text = re.sub("[^A-Za-z0-9]","", text)

    text = text.lower()

    # print(text)
    # removing stop words and Stemming the remaining words in the text

    if text in stopwords: 
      tokens.append('')
      continue
    
    stemmer = Stemmer.Stemmer("english")

    text = stemmer.stemWord(text)

    tokens.append(text)

  return tokens 

def binary_disc_search(f, x):

  x = x.rstrip('\n')
  if not x: return 0 

  f.seek(0, 2)  # Seek to EOF.

  size = f.tell()
  if size <= 0: return 0  # Shortcut.

  lo, hi, mid = 0, size - 1, 1
  while lo < hi:
    mid = (lo + hi) >> 1
    if mid > 0:
      f.seek(mid - 1) 
      f.readline()  
      midf = f.tell()
    else:
      midf = 0
      f.seek(midf)

    line = f.readline()  
    linetoken = line.rstrip('\n')
    linetoken = re.search(r"^[^:]*",linetoken).group(0)

    if not line or x <= linetoken:
      hi = mid
    else:
      lo = mid + 1

  if mid == lo: return midf  # Shortcut.
  if lo <= 0: return 0

  f.seek(lo - 1)
  f.readline()
  return f.tell()

def getTitle(titleidx, linenumber):

  track = 0

  fp = open("../titles/titles"+str(titleidx)+".txt", 'r')
  line = fp.readline()

  while(line):
    track += 1
    if track == linenumber: return line.strip()
    line = fp.readline()

  fp.close()
  return ""

def getRelevantResults(top10docs):

  titles = []
  for doc in top10docs:
      docid = int(doc[0], 16)
      titleidx = int(docid / 50000) + 1
      linenumber = docid%50000
      titles.append( getTitle(titleidx, linenumber) )

  for i in titles:
    OUTPUT_FILE.write(str(docid) +", " + i+"\n")

    # print(str(docid) +", " + i)

def searchQuery(QUERY):

  isField = True

  startime = time.time()

  FieldQueries = {}

  iter = re.finditer(r"[ticlrb]:+", QUERY)
  indices = [m.start(0) for m in iter]
  # print(indices)

  if(len(indices) == 0): 
    isField = False
    FieldQueries['G'] = QUERY.split()
  else:
    queries = [QUERY[i:j] for i,j in zip(indices, indices[1:]+[None])]
    for fq in queries:
        FieldQueries[fq[:1]] = fq[2:].split()

  ranking = {}
  weights = {'T':300,'I':75,'C':50,'L':0.5,'R':0.5,'B':1}

  for fq in FieldQueries.keys():

    if isField:
      prev_weight = weights[fq.upper()]
      weights[fq.upper()] = 1000

    # same len as queries - stopwords replaced by ''
    tokens = clean_text(FieldQueries[fq])

    for i in range(len(tokens)):

      if tokens[i] == '': continue

      INVERTED_INDEX_PATH = "../my_index/index_file_"+tokens[i][0]+".txt"
      f = open(INVERTED_INDEX_PATH,'r')

      f.seek(binary_disc_search(f, tokens[i]))
      line = f.readline()
      line = line[:-1]

      linetoken = re.search(r"^[^:]*",line).group(0)
      if linetoken != tokens[i]: continue

      docs = line.replace(':',' ').replace('D',' ').split()
      docs = docs[1:]

      n = 21384756
      IDF = math.log(n/len(docs))

      for doc in docs:
        data = re.findall('[0-9a-zA-Z][^A-Z]*', doc)
        docid = data[0]
        fields = {"T","I","C","L","R","B"}
        tfdict = {k:0 for k in fields}
        for fieldData in data[1:]:
            field = fieldData[0]
            freq = fieldData[1:]
            tfdict[field] = int(freq,16)

        tf = weights['T']*tfdict["T"] + weights['I']*tfdict["I"] + weights['C']*tfdict["C"] + weights['L']*tfdict["L"] + weights['R']*tfdict["R"] + weights['B']*tfdict["B"]
        tfidf = math.log(1+tf) * IDF
        if docid in ranking.keys(): ranking[docid] += tfidf
        else: ranking[docid] = tfidf

    if isField: weights[fq.upper()] = prev_weight


  ordered_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
  top10docs = ordered_ranking[:10]
  # print(top10docs)
  getRelevantResults(top10docs)
  endtime = time.time()
  OUTPUT_FILE.write(str(endtime - startime)+"\n")
  OUTPUT_FILE.write("\n\n")

  # print(endtime - startime)
  # print("\n\n")


if __name__ == "__main__":

  QUERY_FILE = sys.argv[1]

  queryfp = open(QUERY_FILE,'r')
  query = queryfp.readline()
  queries_input = []
  queries_input.append(query)

  while(query):
    query = queryfp.readline()
    queries_input.append(query.strip())
  queryfp.close()

  for q in queries_input:
    print("Searching for ", q)
    searchQuery(q)

  