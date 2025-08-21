import re

MAX_LEN = 4000

def split_text_by_sentences(text: str, max_len: int = MAX_LEN):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > max_len:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += (" " if current_chunk else "") + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks