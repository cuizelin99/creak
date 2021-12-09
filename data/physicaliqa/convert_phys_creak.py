import csv
import sys

csv_file = sys.argv[1]
creak_true = sys.argv[2]
creak_false = sys.argv[3]
question_true = sys.argv[4]
question_false = sys.argv[5]

with open(creak_true, "w") as ct_file:
	with open(creak_false, "w") as cf_file:
		with open(question_true, "w") as qt_file:
			with open(question_false, "w") as qf_file:
				with open(csv_file) as csvfile:
					csv_reader = csv.reader(csvfile, delimiter=',')
					line_count = 0
					for row in csv_reader:
						if line_count == 0:
							line_count += 1
						else:
							uid = row[0]
							inputs = row[1]
							statement = inputs.split("<goal>")[1].split("</goal>")[0]
							ans1 = inputs.split("<sol1>")[1].split("</sol1>")[0]
							ans1 = ans1[0].lower() + ans1[1:]
							ans2 = inputs.split("<sol2>")[1].split("</sol2>")[0]
							ans2 = ans2[0].lower() + ans2[1:]
							answers = [ans1, ans2]
							answer_idx = int(row[2])
							if statement.endswith("?") or statement.startswith("How") or statement.startswith("how") or statement.startswith("What") or statement.startswith("what") or statement.startswith("Where") or statement.startswith("where") or statement.startswith("Who") or statement.startswith("who") or statement.startswith("Which") or statement.startswith("which") or statement.startswith("Why") or statement.startswith("why") or statement.startswith("When") or statement.startswith("when") or statement.startswith("Whose") or statement.startswith("whose"):
								if not statement.endswith("?"):
									if statement.endswith("."):
										statement = statement[:-1] + "?"
									else:
										statement = statement + "?"
								if "\"" not in statement and "\"" not in ans1 and "\"" not in ans2 and ";" not in statement and ";" not in ans1 and ";" not in ans2 and "," not in statement and "," not in ans1 and "," not in ans2 and "." not in statement and "." not in ans1 and "." not in ans2:
									true_line = "{{\"example_id\": {}, \"title_text\": \"\", \"paragraph_text\": \"\", \"answer_sent_text\": \"\", \"question_text\": \"{}\", \"question_statement_text\": \"\", \"has_gold\": false, \"is_correct\": false, \"answer_text\": \"{}\", \"decontext_answer_sent_text\": \"\", \"decontextualized_sentence\": \"\", \"category\": \"\", \"answer_score\": 0.0, \"answer_scores\": [], \"kamath_score\": 0.0, \"f1\": 0, \"gold_answers\": []}}\n".format(uid, statement, answers[answer_idx])
									false_line = "{{\"example_id\": {}, \"title_text\": \"\", \"paragraph_text\": \"\", \"answer_sent_text\": \"\", \"question_text\": \"{}\", \"question_statement_text\": \"\", \"has_gold\": false, \"is_correct\": false, \"answer_text\": \"{}\", \"decontext_answer_sent_text\": \"\", \"decontextualized_sentence\": \"\", \"category\": \"\", \"answer_score\": 0.0, \"answer_scores\": [], \"kamath_score\": 0.0, \"f1\": 0, \"gold_answers\": []}}\n".format(uid, statement, answers[1 - answer_idx])
									qt_file.write(true_line)
									qf_file.write(false_line)
							else:
								true_statement = statement + " " + answers[answer_idx]
								false_statement = statement + " " + answers[1 - answer_idx]
								if "\"" not in true_statement and "\"" not in false_statement and ";" not in true_statement and ";" not in false_statement:
									true_line = "{{\"ex_id\": \"{}\", \"sentence\": \"{}\", \"explanation\": \"\", \"label\": \"true\", \"entity\": \"\", \"en_wiki_pageid\": \"\", \"entity_mention_loc\": [[]]}}\n".format(uid, true_statement)
									false_line = "{{\"ex_id\": \"{}\", \"sentence\": \"{}\", \"explanation\": \"\", \"label\": \"false\", \"entity\": \"\", \"en_wiki_pageid\": \"\", \"entity_mention_loc\": [[]]}}\n".format(uid, false_statement)
									if len(true_statement) <= 256 and len(false_statement) <= 256:
										ct_file.write(true_line)
										cf_file.write(false_line)
							line_count += 1