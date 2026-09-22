from pathlib import Path
from ollama import chat
import json



question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

## WRITE ##
service_status = {
    "wifi": "operational"
}

state = {
    "problem": question,
    "wi_fi status": "operational",
    "wi-fi_check": True
}

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

with open("state.json", "r") as file:
    state = json.load(file)

print(state)


## SELECT CONTEXT FILES BASED ON QUESTION
## Create the function that takes the student's question, takes some keywords and chooses the relevant files from the knowledge base. Return a list of the selected files.
## For example, if the question has the kyeword "print" or "printer", then the function should return the file "knowledge/printer_setup.txt" in a list.
KEYWORD_TO_FILES = {
    "wifi": ["wifi_setup.txt", "service_status.txt"],
    "wi-fi": ["wifi_setup.txt", "service_status.txt"],
    "eduroam": ["wifi_setup.txt", "service_status.txt"],
    "password": ["password_changes.txt", "wifi_setup.txt"],
    "login": ["password_changes.txt"],
    "email": ["email_setup.txt"],
    "vpn": ["vpn.txt"],
    "print": ["printing.txt"],
    "projector": ["classroom_projectors.txt"],
    "display": ["classroom_projectors.txt"],
}


def select_context(question):
    question_lower = question.lower()
    selected = []
    for keyword, files in KEYWORD_TO_FILES.items():
        if keyword in question_lower:
            selected.extend(files)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for f in selected:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    # Fallback so the function always returns something useful
    if not unique:
        unique = ["service_status.txt"]
    return [Path("knowledge") / f for f in unique]


selected_files = select_context(question)

## READ SELECTED FILES and add their contents to the context variable.
context = ""
for file in selected_files:
    context += file.read_text()
    context += "\n\n"


##
## COMPRESS CONTEXT
## Add logic to compress the context from above by calling Qwen with "context" and the "question" as the parameter
## The response from Qwen should be the compressed context. Store it in a variable called "compressed_context"

def compress_context(context, question):
    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a context compressor. Given the user's question "
                    "and a knowledge base, keep ONLY the information that is "
                    "directly relevant to answering the question. Remove "
                    "everything else. Output a concise, compressed version "
                    "of the relevant facts as plain text."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nKnowledge base:\n{context}",
            },
        ],
    )
    return response.message.content


compressed_context = compress_context(context, question)

## Print the length of the compressed context
print(len(compressed_context))

## Now, call Qwen again with the compressed context and the student's question. Store the response in a variable called "response" and print the response from Qwen.
## Ensure the model produces a structured output
response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an IT support assistant for a university. "
                "Answer the student's question using ONLY the compressed "
                "knowledge base provided below. Structure your answer as JSON "
                "with these keys: diagnosis (string), recommended_steps "
                "(list of short strings), confidence (one of "
                "'low', 'medium', 'high').\n\n"
                f"Compressed knowledge base:\n{compressed_context}"
            ),
        },
        {"role": "user", "content": question},
    ],
    format="json",
)


print(response.message.content)

## WRITE the above output in an artifact called "state"
state = {
    "problem": question.strip(),
    "answer": response.message.content,
    "selected_files": [str(f) for f in selected_files],
    "raw_context_chars": len(context),
    "compressed_context_chars": len(compressed_context),
    "service_status": {"wifi": "operational"},
}

with open("state.json", "w", encoding="utf-8") as file:
    json.dump(state, file, indent=2, ensure_ascii=False)

## Update the rest of the code so that it uses the "state" artifact as part of the context.
## It is important to ensure that the model uses only the relevant parts from the "state" artifact and not the entire artifact.
## For this, you may have to think of a good structure for the "state" artifact and how to use it in the context.

# ISOLATE — reload state.json but only project the fields relevant to the current
# question. The model never sees the whole artifact at once; it only sees the
# fields that match the problem domain (wifi / password).
with open("state.json", "r", encoding="utf-8") as file:
    saved_state = json.load(file)

isolated_context_parts = [f"problem: {saved_state['problem']}"]
if "wifi" in saved_state.get("problem", "").lower() or "wi-fi" in saved_state.get(
    "problem", ""
).lower():
    isolated_context_parts.append(
        f"service_status.wifi: {saved_state['service_status']['wifi']}"
    )
    isolated_context_parts.append(f"answer: {saved_state['answer']}")
elif "print" in saved_state.get("problem", "").lower():
    isolated_context_parts.append(f"answer: {saved_state['answer']}")
else:
    isolated_context_parts.append(f"answer: {saved_state['answer']}")

isolated_context = "\n".join(isolated_context_parts)

isolated_response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an IT support assistant. Based on the isolated "
                "state context below, produce ONE sentence summary that "
                "directly answers the user's problem. Use plain text, no JSON."
            ),
        },
        {
            "role": "user",
            "content": f"State context:\n{isolated_context}",
        },
    ],
)

print("--- ISOLATED one-line summary ---")
print(isolated_response.message.content)


