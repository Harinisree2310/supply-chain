"""
llm.py
--------
The ONLY file that talks to the language model. Every other file should
call ask_llm() rather than importing ollama directly -- if you ever swap
models, this is the one place you change.

Test this file completely on its own before touching nodes.py:
    python llm.py
"""

import ollama

MODEL_NAME = "phi3:mini"  # change here if you swap models later


def ask_llm(prompt, system_prompt=None):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = ollama.chat(model=MODEL_NAME, messages=messages)
    return response["message"]["content"]


if __name__ == "__main__":
    # quick manual test -- run this file directly to confirm Ollama works
    reply = ask_llm("In one short sentence, what does a supply chain do?")
    print("Model replied:\n", reply)