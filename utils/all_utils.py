import re
from html.parser import HTMLParser

MAX_LEN = 4000

class TagBalanceChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags_stack = []
    
    def handle_starttag(self, tag, attrs):
        self.tags_stack.append(tag)
    
    def handle_endtag(self, tag):
        if self.tags_stack and self.tags_stack[-1] == tag:
            self.tags_stack.pop()
    
    def get_unclosed_tags(self):
        return self.tags_stack.copy()

def split_text_by_sentences(text: str, max_len: int = MAX_LEN):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    tag_balance = []
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > max_len:
            if tag_balance:
                closed_chunk = current_chunk + ''.join(f'</{tag}>' for tag in reversed(tag_balance))
                chunks.append(closed_chunk.strip())
                next_chunk_open_tags = ''.join(f'<{tag}>' for tag in tag_balance)
                current_chunk = next_chunk_open_tags + sentence
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
        else:
            current_chunk += (" " if current_chunk else "") + sentence
        
        parser = TagBalanceChecker()
        parser.feed(sentence)
        new_unclosed = parser.get_unclosed_tags()
        
        for tag in new_unclosed:
            if tag in tag_balance:
                tag_balance.remove(tag)
            else:
                tag_balance.append(tag)
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks