## IRE Mini Project Phase 1
### Pooja Desur 2019101112

----
Description: Python code to create an inverted index, and then fetch posting lists for all fields when searching for a query.
* To create the inverted index run -
```
bash index.sh <path_to_wiki_dump> <path_to_inverted_index> invertedindex_stat.txt
```
* To search for queries - 
    *   General query - "Happiness is elusive"
    *   field queries - "t:Football i:2018"
```
bash search.sh <path_to_inverted_index> "query"
```
* Dependencies (Python Packages used) - 
    * Stemmer
    * re (regex)
    * collections
    * json
    * xml.sax
    * os
    * sys
    * string