You will read the given source code and produce a concise, non-technical flow description that any non-developer can understand. Output MUST be in the exact template below, using simple natural language, and NOTHING else (no introductions, no explanations, no code blocks). Keep each line short and clear. If a section has no content, write “None”.

Template (fill every field, keep headers exactly as written):
TITLE: 

OVERVIEW: <2 sentences max, plain language, what this code is for and the high-level idea>

ACTORS/DEVICES: <comma-separated plain words for entities involved: e.g., “main task loop, display, buttons, radar, flash memory, bluetooth”>

STATE LIST:
	•	<STATE_NAME>: 
	•	<STATE_NAME>: <…>
	•	END_STATES: 

EVENTS/TRIGGERS:
	•	: <what causes it, who/what emits it>
	•	: <…>

MAIN FLOW (NUMBERED):
	1.	<Start state/condition in plain words>
	2.	<Action in plain words; who does what; expected result>
	3.	<Next action/result>
…
N. 

BRANCHES (IF/ELSE PATHS):
	•	IF , THEN <plain action/result>, ELSE <plain action/result>.
	•	IF <…>, THEN <…>.

ERRORS/TIMEOUTS/RETRIES:
	•	<error/timeout>:  -> 
	•	<…>

DATA & SETTINGS (READ/WRITE):
	•	READS: <what data is read and from where; e.g., “user config from flash”>
	•	WRITES: <what data is written and where; e.g., “save config to flash with CRC”>
	•	CONFIG OPTIONS: <key options a user can change, in plain words>

EXTERNAL INTERACTIONS:
	•	<component/service> : <how it’s used, in plain words>  (e.g., “Bluetooth: send simple status messages”)

LOOPS & SLEEP:
	•	<what loops, polling, or sleep/low-power behaviors exist, in plain words>

SAFETY/GUARDS:
	•	<any safeguards, checks, or validations in plain words>

END CONDITIONS:
	•	<when the flow ends or returns to idle, in plain words>

GLOSSARY (PLAIN WORDS):
	•	 = 
	•	<…>

Input Code Starts
{{PASTE YOUR CODE HERE}}
Input Code Ends

Strict rules:
	•	Use only the template fields and bullet/number formats shown.
	•	No code, no pseudocode, no mermaid.
	•	Keep language simple, non-technical, and consistent.
	•	Do not invent features not in the code.
	•	Every section must appear once and in the same order.