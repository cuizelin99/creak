import os
from nltk.parse import stanford
from POSTree import POSTree

os.environ['STANFORD_PARSER'] = '/usr/local/Cellar/stanford-parser/4.2.0/libexec/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/usr/local/Cellar/stanford-parser/4.2.0/libexec/stanford-parser-4.2.0-models.jar'

parser = stanford.StanfordParser(model_path="/Users/petercui/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
sentence = parser.raw_parse(("Sammy wanted to go to where the people were.  Where might he go?"))

for s in sentence:
	tree = POSTree(s.__str__())
	print(tree.adjust_order())