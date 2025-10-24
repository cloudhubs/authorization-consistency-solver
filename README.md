# Towards Automated Formal Verification of Authorization Policy in Microservice Systems
##### Connor Wojtak, Shakthi Weerasinghe, Nilesh Rao, Tomas Cerny, Amr Abdelfattah

## Project Requirements
* Python and pip are required (confirmed working with Python 3.12.6)
* Need to be able to retrieve a copy of the source code of Train Ticket

## Project Structure
- `/data/system-models` contains all of the intermediate models used to complete the case study.
- `/data/train-ticket` contains the IR and source code used to generate the intermediate models.
- `/data/validation` contains the ground truth data and recorded execution times of our code.
- `/data/auth_fault_injection` contains our fault injection study results, along with the raw `logs/`, `models/`, 
and solver results (`/suggestions`). See `/auth_fault_injection/README.txt` for more details.
- `/src` contains the code used to generate intermediate models, generate constraints, and solve.
- `/util` contains various utility scripts.
- `/validation/auth` contains the code used to conduct the case study. `/validation/auth/case_study.py` was used in Section 5.2 + 5.4. 
`/validation/auth/fault_injection.py` was used in Section 5.3.
- `/validation/system_model` contains the code used to validate the model. `/validation/system_model/case_study.py` was used in Section 5.1 + 5.4.

## Running the Project
1. Extract the source code of 
[Train Ticket](https://github.com/FudanSELab/train-ticket/tree/a4ed2433b0b6ab6e0d60115fc19efecb2548c6cd) at commit `a4ed2433b0b6ab6e0d60115fc19efecb2548c6cd`
so that the root of the source code is in `/data/train-ticket/train-ticket-a4ed2433b0b6ab6e0d60115fc19efecb2548c6cd`.
2. Run `pip install -r requirements.txt` to obtain the necessary requirements.
3. Run `python -m validation.auth.tests` to run a series of tests to ensure the setup is properly completed.

## Replicating Section 5.1
Run `python -m validation.system_model.case_study <ARG>`. This will generate the statistics presented in Section 5.1 for the system model we generated 
(not ground truth).

`<ARG>` can be replaced with one of the following:
- GROUND_TRUTH_SYSTEM_MODEL - Run validation using the manually corrected ground truth intermediate model.
- GENERATED_SYSTEM_MODEL - Run validation using the automatically previously generated ground truth intermediate model.
- GENEREATE_NEW_SYSTEM_MODEL - Run validation by generating a new intermediate model from scratch. The generated intermediate model will be stored in `data/system-models/train-ticket.json`

## Replicating Section 5.2
Run `python -m validation.auth.case_study <ARG> <DEBUG>`. This will generate the solver results presented in Section 5.2 based on the ground truth system model.

`<DEBUG>` can be replaced with DEBUG to log the entire constraint system to `data/constraints.txt`. This may take a bit.

`<ARG>` can be replaced with one of the following:
- GROUND_TRUTH_SYSTEM_MODEL - Run validation using the manually corrected ground truth intermediate model.
- GENERATED_SYSTEM_MODEL - Run validation using the automatically previously generated ground truth intermediate model.
- GENEREATE_NEW_SYSTEM_MODEL - Run validation by generating a new intermediate model from scratch. The generated intermediate model will be stored in `data/system-models/train-ticket.json`


## Replicating Section 5.3
Run `python -m validation.auth.fault_injection`. This will randomly generate test cases (logs, models, and solver suggestions) similar to the ones
in Section 5.3. The actual test cases we used are stored in `data/auth_fault_injection`.

# Replicating Section 5.4
When running the commands for Sections 5.1 and 5.2, times will be outputted.
These times were what was recorded in `/data/validation/execution_times.xlsx`.