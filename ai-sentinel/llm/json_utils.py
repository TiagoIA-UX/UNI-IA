import json
import re


def extract_json_object(raw_text: str):
    if not raw_text:
        raise ValueError("Resposta vazia do LLM.")

    text = raw_text.strip()

    fenced_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fenced_match:
        text = fenced_match.group(1)

    text = text.replace("**{**", "{").replace("**}**", "}")

    decoder = json.JSONDecoder()
    parsed_objects = []
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
            parsed_objects.append(obj)
        except json.JSONDecodeError:
            continue

    if parsed_objects:
        return parsed_objects[-1]

    raise ValueError(f"JSON não encontrado na resposta do LLM. Resposta: {raw_text}")