import json
import sys

pred_file = open(sys.argv[1])
pred_lines = pred_file.readlines()
pred_lines = pred_lines[1:]

json_file = open(sys.argv[2])
creak_lines = json_file.readlines()
out_file = sys.argv[3]

with open(out_file, "w") as outfile:
	for i in range(len(creak_lines)):
		example = creak_lines[i]
		pred = pred_lines[i]
		data = json.loads(example)
		label = data['label']
		if label not in pred:
			outfile.write(example)