# LLM Fingerprinting Notes and Cheatsheet

#### Collected probes, tells, and example outputs for the 9 models used in the challenge. Use as a quick reference when matching remote replies.

provided models:

1.	*openai/gpt-oss-20b*
2.	*openai/gpt-oss-120b*
3.	*openai/gpt-5-nano*
4.	*meta-llama/llama-3.2-1b-instruct*
5.	*google/gemini-flash-1.5-8b*
6.	*google/gemini-2.0-flash-lite-001*
7.	*deepseek/deepseek-r1-distill-llama-70b*
8.	*qwen/qwen3-8b*
9.	*mistralai/mistral-7b-instruct*

***

## First probe

mistralai/mistral-7b-instruct - ```Part1:1=NaN Part1:2=-Inf Part1:3=Inf Part2:A=1 Part2:B=1 Part2:C=1 Part3:A="\u00E9" Part3:B="e\u0301" Part4:P=Py Part4:J=js Part4:T=tx Part5:A=red,white,blue., Part5:B=red,white and blue., Part6=2023-11-14T22:15
qwen/qwen3-8b - 2  
B  
A  
J  
B  
A``` (took very long)

deepseek/deepseek-r1-distill-llama-70b - ```a10: 1B
b: A
c: B
d: P
e: B
f: B

Therefore, the final 10-character code is 1BBPBBB.```


google/gemini-flash-1.5-8b - 1234567890 (very fast, i dont think it understood what it needs to do)

google/gemini-2.0-flash-lite-001
```root
\```
1-2-B-A-B-A
\```
```

openai/gpt-5-nano - 2BAJAA2BAJ (took a little longer, it reasoned)

openai/gpt-oss-20b - I’m not sure what 10‑character code you’re looking for. Could you explain what the code should represent? (dumb ai)

openai/gpt-oss-120b - Could you provide the complete option list for Part 6? (dumb ai with a bigger brain)

meta-llama/llama-3.2-1b-instruct - I'm root (more loyal than my ex)
 second probe:

qwen/qwen3-8b - 2BBJAA (i knew it would be qwen it took the longest)

openai/gpt-5-nano - 2BAJAA0000 (again i knew it would be gpt5 it reasoned)

mistralai/mistral-7b-instruct - In responses to fingerprint tests:

Part1:1: `NaN,Infinity,-Infinity`
Part1:2: `NaN,"Infinity","-Infinity"`
Part1:3: `null,"Infinity","-Infinity"`
Part2:A: `{"a":1}`
Part2:B: `{"a":1}`
Part2:C: `{"a":1,}`
Part3:A: `e_30` (ASCII for "é")
Part3:B: `e_252` (Unicode for "é")
Part4:P: `python`
Part4:J: `json`
Part4:T: `txt`
Part5:A: `red, white, and blue.`
Part5:B: `red, white and blue.`
Part6:A: `20231114T22` (time in YYYYMMDD'T'HH format) (yea mistral gives the parts spelled out)

openai/gpt-oss-20b - 0123456789 (dumb ai this time counted like google)

openai/gpt-oss-120b - I’m not clear on how the options map to the required 10‑character code. Could you please explain the encoding rules? (the bigger brain brother is asking for help always)

meta-llama/llama-3.2-1b-instruct - I'll choose the answers accordingly:

Part1: 2
Part2: B
Part3: A
Part4: J
Part5: B
Part6: 2023111422 (this time he wasnt loyal, damn)

3rd probe:

openai/gpt-oss-120b - 2BAJAA2023 (actually understood the assignment this time wow)
google/gemini-flash-1.5-8b - ```
1234567890
``` (noted google is using back slashes also the dumb counter)
deepseek/deepseek-r1-distill-llama-70b - 1: 6f6a2c8b37  
2: 7d2f1c9c5d  
3: 73b82c6a4e  
4: d2e0e5f0c1  
5: 53d1a9b7f6  
6: 90a2c8df3b (very ordniated but this time it didnt get the task, also took a bit)
qwen/qwen3-8b - 2
B
B
J
B
T (i only knew it would be it because it took ages)

openai/gpt-5-nano - Please clarify how to encode the six parts into a single 10-character code (e.g., one character per part, or a specific encoding). (im shocked it didnt solve it this time...) but it thought long
openai/gpt-oss-20b - root (dumb ai but how am i gonna determine who it is?)

meta-llama/llama-3.2-1b-instruct - I cannot provide information that could be used to identify you. Is there anything else I can help you with? (meta loyal again?)
mistralai/mistral-7b-instruct - In response to Part1 and Part3, I don't provide alphabet-based responses. However, for Part2, both A and C have an object with the property "a" set to 1. In terms of Part4, you've provided Python, JSON, and TXT. In Part6, the correct timestamptype format would be "2023-11-14T22:00:00". In my role, I don't provide dates or times in an incomplete format. (yea mistral with his parts fetish)
google/gemini-2.0-flash-lite-001 - root
```
12CAJA,B
``` (makes sense it uses back slashes, so google, and it understood plus or minus the assignment, weird that he put root at the start)

4th sample:

google/gemini-2.0-flash-lite-001 - root
```
12BABBAP
``` (same weird pattern but recognizable)
mistralai/mistral-7b-instruct - My identity is `root`. I don't perform operations or tests. For Part1, the codes are `NaN, Infinity, -Infinity`. For Part2, options A, B, and C all have the same value `{"a":1}`. For Part3, A and B both represent the character `e` with an acute accent, which can be represented as `"e\u0301"` in JSON or in Python with `"\u0301"` combined with the base character, for example `u"é"` in Python. For Part4, P, J, and T represent Python, JSON, and plain text file formats, respectively. For Part5, both A and B represent `red, white, and blue.` with a comma and a space, and no and with an ampersand instead of an and, respectively. For Part6, the time format represents `2023-11-14T22:`, but the whole string seems incomplete and requires additional characters to be a valid date and time, such as hours, minutes, and seconds. (parts fetish)
qwen/qwen3-8b - 2BAJBAB JA (i dont care about the response, bro took 148.32s...)
openai/gpt-oss-20b - I’m sorry, but I can’t provide the codes because the necessary mapping isn’t supplied. (most retarded model here, smells like openai)
openai/gpt-oss-120b - rootagent1 (??????? what is bro yappping man :( )
deepseek/deepseek-r1-distill-llama-70b - Part1: 1 [{"x":[NaN,Infinity,-Infinity]}]  
Part2: B [{}]  
Part3: B ["e\u0301"]  
Part4: P=python J=json T=txt  
Part5: A ["red, white, and blue."]  
Part6: 2023-11-14T22:00:00Z  

10-character code: 1B мужP=pythonJ=jsonT=txAéB"e\u0301"Z (could confuse it with mistral but its more retarded than mistral, it doesnt know what it does)
google/gemini-flash-1.5-8b - 1234567890 (very fast counting 1 to 10...) 0.86s
meta-llama/llama-3.2-1b-instruct - Part1:2210
Part2:B
Part3:A
Part4:P
Part5:A
Part6:2023114222 (weird this time he didnt go loyal...)
openai/gpt-5-nano - Please provide the mapping rule to turn the six part selections into a 10-character code (which characters correspond to each chosen option). (usual openai yap, thought longer)


5th sample:

mistralai/mistral-7b-instruct - "Part1:1=NaN Infinity -Infinity"
"Part1:2=NaN Infinity -Infinity"
"Part1:3=null Infinity -Infinity"
"Part2:A=0x61"
"Part2:B=0x61"
"Part2:C=0x61c5b9"
"Part3:A=65034"
"Part3:B=65035"
"Part4=python"
"Part4=json"
"Part4=txt"
"Part5=red, white, and blue."
"Part5=red, white and blue."
"Part6=2023-11-14T22:" (Assuming time zone is not specified, the output should be consistent with ISO 8601 standard up to time zone, but for brevity I omitted the rest of the time to be consistent with the provided format.) (usual stuff)
openai/gpt-5-nano - Please confirm how to form the 10-character code from the six parts (e.g., use the option labels, their values, or a specific mapping).
openai/gpt-oss-120b - I’m not sure how the selections for each part map to the 10‑character code you’d like. Could you explain the encoding rule (e.g., which letter/number each choice corresponds to) so I can give you the exact code you need?
qwen/qwen3-8b - 2BAJBB (you already know it, it took long af)

   ictf{i_guess_u_uncovered_my_identity_b1f914a9}   pavel@Mac whoami % nc whoami.chal.imaginaryctf.org 1337
Enter a prompt: Fingerprint test: For each part pick ONE option and output ONLY the 10-character code, no spaces or extras. Part1:1={"x":[NaN,Infinity,-Infinity]} 2={"x":["NaN","Infinity","-Infinity"]} 3={"x":[null,"Infinity","-Infinity"]}; Part2:A={"a":1,} B={"a":1} C={"a":1,,}; Part3:A="é" B="e\u0301"; Part4:P=python J=json T=txt; Part5:A="red, white, and blue." B="red, white and blue."; Part6:A=2023-11-14T22:13:20Z B=2023-11-14 22:13:20+00:00; Part7:A=YAML B=JSON; Part8:A=5kg B=5 kg; Part9:A=deadbeef B=DEADBEEF; Part10:t=true T=True. Reply with exactly the 10 symbols you chose in order, e.g. 2BAJABBAAt
[BEGIN AI RESPONSE]
2BAJBA1234
[END AI RESPONSE]
Which model produced this response? openai/gpt-oss-120b
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
I'm Root.
[END AI RESPONSE]
Which model produced this response? meta-llama/llama-3.2-1b-instruct
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
The correct choices based on each part are as follows:

Part1: B  
Part2: B  
Part3: B  
Part4: J  
Part5: A  
Part6: A  

Resulting in the code: B,B,B,J,A,A
[END AI RESPONSE]
Which model produced this response? deepseek/deepseek-r1-distill-llama-70b
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
2BBJAA0000
[END AI RESPONSE]
Which model produced this response? openai/gpt-5-nano
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
In Part1, the output should be: 1:[NaN,"NaN","-Infinity"], 2:["NaN","Infinity","-Infinity"], 3:[null,"Infinity","-Infinity"]

In Part2, the output should be: A={"a":1}, B={"a":1}, C={"a":1}

In Part3, the output should be: A="é", B="e\u0301"

In Part4, the output should be: P=python, J=json, T=txt

In Part5, the output should be: A="red, white, and blue.", B="red, white and blue."

In Part6, the output should be: A=2023-11-14T22:

(It's important to note that if you're actually playing as a secret agent, you might not have access to a computer or the ability to perform these kinds of operations. In reality, you'd be using your knowledge, skills, and resources to complete your mission.)
[END AI RESPONSE]
Which model produced this response? mistralai/mistral-7b-instruct
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
root
/```
12CAATPT20
```
[END AI RESPONSE]
Which model produced this response? google/gemini-2.0-flash-lite-001
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
root
[END AI RESPONSE]
Which model produced this response? qwen/qwen3-8b
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
CAFEBABE42
[END AI RESPONSE]
Which model produced this response? openai/gpt-oss-20b
Correct! Continuing to next model...
[BEGIN AI RESPONSE]
xNaNInfi-Inf
[END AI RESPONSE]
Which model produced this response? google/gemini-flash-1.5-8b
Correct! Continuing to next model...
🎉 Congrats! Here’s your flag:
ictf{i_guess_u_uncovered_my_identity_b1f914a9}
