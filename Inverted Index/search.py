import re
import json
import string
import sys
import Stemmer

INVERTED_INDEX_PATH = ""
QUERY = ""

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

if __name__ == "__main__":

  INVERTED_INDEX_PATH = sys.argv[1] + "/index.txt"
  QUERY = sys.argv[2]

  # queries = re.findall("[a-zA-Z:]+", QUERY)
  QUERY = QUERY.split()
  queries = []
  for query in QUERY: 
    queries.append(re.sub(r"^[^:]*:","",query))

  # print(queries)

  f = open(INVERTED_INDEX_PATH,'r')
  output = {}

  # same len as queries - stopwords replaced by ''
  tokens = clean_text(queries)

  # print(tokens)

  for i in range(len(tokens)):

    output[queries[i]] = {}
    output[queries[i]]['title'] = []
    output[queries[i]]['body'] = []
    output[queries[i]]['infobox'] = []
    output[queries[i]]['categories'] = []
    output[queries[i]]['references'] = []
    output[queries[i]]['links'] = []

    if tokens[i] == '': continue

    f.seek(binary_disc_search(f, tokens[i]))
    line = f.readline()
    line = line[:-1]
    # print("line: ",line)

    linetoken = re.search(r"^[^:]*",line).group(0)

    # print(linetoken)

    if linetoken != tokens[i]: continue

    idfields = line.replace(':',' ').replace('|',' ').split()
    idfields = idfields[1:]


    for j in idfields:

      docid = j.replace('-',' ').split()[0]
      fields = j.replace('-',' ').split()[1]  
      fields = fields.replace('b','body')
      fields = fields.replace('i','infobox') 
      fields = fields.replace('l','links')
      fields = fields.replace('t','title')  
      fields = fields.replace('r','ref')
      fields = fields.replace('c','categories')
      fields = fields.replace('ref','references')

      fields = re.findall("[a-zA-Z]+", fields)

      # print(fields)

      for field in fields:
        output[queries[i]][field].append(docid[1:])

  json_object = json.dumps(output, indent = 2) 
  print(json_object)


