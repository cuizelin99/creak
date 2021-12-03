import json
import sys

true_file = open(sys.argv[1])
true_lines = true_file.readlines()
false_file = open(sys.argv[2])
false_lines = false_file.readlines()
out_file = sys.argv[3]

all_lines = True

count = 10175

with open(out_file, "a") as outfile:
	for i in range(len(true_lines)):
		true_line = ""
		false_line = ""
		if all_lines:
			true_line = true_lines[i]
			false_line = false_lines[i]
		else:
			if i % 2 == 0:
				true_line = true_lines[i]
				false_line = ""
			else:
				true_line = ""
				false_line = false_lines[i]

		if true_line != "":
			count += 1
			true_id = "train_{}".format(count)
			true_statement = true_line.split("\"question_statement_text\": \"")[1].split("\", \"")[0]
			true_label = "true"
			true_line = "{{\"ex_id\": \"{}\", \"sentence\": \"{}\", \"explanation\": \"\", \"label\": \"{}\", \"entity\": \"\", \"en_wiki_pageid\": \"\", \"entity_mention_loc\": [[]]}}\n".format(true_id, true_statement, true_label)
			outfile.write(true_line)
		if false_line != "":
			count += 1
			false_id = "train_{}".format(count)
			false_statement = false_line.split("\"question_statement_text\": \"")[1].split("\", \"")[0]
			false_label = "false"
			false_line = "{{\"ex_id\": \"{}\", \"sentence\": \"{}\", \"explanation\": \"\", \"label\": \"{}\", \"entity\": \"\", \"en_wiki_pageid\": \"\", \"entity_mention_loc\": [[]]}}\n".format(false_id, false_statement, false_label)
			#outfile.write(false_line)
