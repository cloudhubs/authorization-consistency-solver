How to conduct the case study.
1. Open the spreadsheet.
2. Open the corresponding log, model, and solver output (suggestions)
3. The "train-ticket-auth-fixed-model" is the baseline model with all architecture and policy correct.
4. Each log in the logs is a set of faulty changes made to the model (note the changes may not always result in an inconsistency).
5. Each model in the models folder is the model AFTER the faulty changes have been made.
6. Each suggestion in the suggestions folder is the solver output when analyzing the faulty model.
7. sat = no issues, unsat = issues.
8. Determine if the suggested changes by the solver fix all
	* endpoint permitted role inconsistencies
	* data entity operation inconsistencies
	* at least one permitted role inconsistencies
	that were caused by the change. (This identifies any false negatives.)
9. Determine if it makes sense that an inconsistency was detected.
	* Example: a data entity operation inconsistency was detected between a get one user's information endpoint and a get all user's information endpoint
	* This shouldn't be an inconsistency because it makes sense to have different permissions based on whether you are just getting your info or all the user info in the DB.
	* This issue is introduced because our model/method does not take into account the scope of the data (i.e., one entity v all).
10. Fill out the spreadsheet.
11. Repeat steps 1-10 for each test case.

Note that train-ticket-auth-fixed-model.json contains the base model used to generate all the fault injection test cases.