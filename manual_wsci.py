from pathlib import Path
from ollama import chat


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

selected_files = [
    ##Use only the files that are relevant to the question.
    "password_changes.txt",
    "wifi_setup.txt",
    "service_status.txt",
]


context = ""

## Write a for loop to go through all the files in selected_files and read their contents into the context variable.
for filename in selected_files:
    context += (Path("knowledge") / filename).read_text()
    context += "\n\n"

## Call Qwen with the student's question and the context you created above.
response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are an IT support assistant for a university. "
                "Answer the student's question using only the knowledge base "
                "provided below.\n\n"
                f"Knowledge base:\n{context}"
            ),
        },
        {"role": "user", "content": question},
    ],
)

print(
    "Context characters:",
    len(context)
)
print(response.message.content)