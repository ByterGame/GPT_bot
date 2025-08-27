import re
from html.parser import HTMLParser

MAX_LEN = 4000

SUPPORTED_TAGS = {
    'b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del',
    'a', 'code', 'pre', 'tg-spoiler'
}

MARKDOWN_SPECIAL_CHARS = r'\_*\[\]()~`>#\+\-=\|{}\.!'

class MixedContentParser:
    def __init__(self):
        self.result = []
        self.current_context = []  
        self.in_code_block = False
        self.in_pre_block = False
    
    def escape_markdown(self, text: str) -> str:
        if self.in_code_block or self.in_pre_block:
            return text
        return re.sub(f'([{re.escape(MARKDOWN_SPECIAL_CHARS)}])', r'\\\1', text)
    
    def handle_html_tag(self, tag: str, attrs: dict, is_start: bool):
        tag_lower = tag.lower()
        
        if tag_lower not in SUPPORTED_TAGS:
            return False
        
        if is_start:
            if tag_lower == 'code':
                self.in_code_block = True
            elif tag_lower == 'pre':
                self.in_pre_block = True
            
            self.current_context.append(tag_lower)
            attrs_str = ""
            if tag_lower == 'a' and 'href' in attrs:
                attrs_str = f' href="{attrs["href"]}"'
            self.result.append(f"<{tag}{attrs_str}>")
        else:
            if self.current_context and self.current_context[-1] == tag_lower:
                self.current_context.pop()
                if tag_lower == 'code':
                    self.in_code_block = False
                elif tag_lower == 'pre':
                    self.in_pre_block = False
                self.result.append(f"</{tag}>")
        
        return True
    
    def handle_markdown(self, text: str):
        if not text.strip():
            return
        
        if self.current_context:
            self.result.append(text)
            return
        
        escaped_text = self.escape_markdown(text)
        self.result.append(escaped_text)
    
    def get_content(self):
        while self.current_context:
            tag = self.current_context.pop()
            self.result.append(f"</{tag}>")
            if tag == 'code':
                self.in_code_block = False
            elif tag == 'pre':
                self.in_pre_block = False
        
        return ''.join(self.result)

def parse_mixed_content(text: str) -> str:
    if not text or not text.strip():
        return text
    
    parser = MixedContentParser()
    
    html_pattern = re.compile(r'<(/?)([a-zA-Z0-9]+)([^>]*)>')
    pos = 0
    
    while pos < len(text):
        match = html_pattern.search(text, pos)
        if not match:
            remaining_text = text[pos:]
            parser.handle_markdown(remaining_text)
            break
        
        text_before = text[pos:match.start()]
        if text_before:
            parser.handle_markdown(text_before)
        
        is_closing = bool(match.group(1))
        tag = match.group(2)
        attrs_str = match.group(3)
        
        attrs = {}
        attr_pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']')
        for attr_match in attr_pattern.finditer(attrs_str):
            attrs[attr_match.group(1).lower()] = attr_match.group(2)
        
        parser.handle_html_tag(tag, attrs, not is_closing)
        
        pos = match.end()
    
    return parser.get_content()

def clean_telegram_content(text: str) -> str:
    if not text or not text.strip():
        return text
    
    text = re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\?xml[^>]*\?>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    return parse_mixed_content(text)

class TagBalanceChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags_stack = []
        self.supported_tags_stack = []
    
    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        self.tags_stack.append(tag_lower)
        if tag_lower in SUPPORTED_TAGS:
            self.supported_tags_stack.append(tag_lower)
    
    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if self.tags_stack and self.tags_stack[-1] == tag_lower:
            self.tags_stack.pop()
        if self.supported_tags_stack and self.supported_tags_stack[-1] == tag_lower:
            self.supported_tags_stack.pop()
    
    def get_unclosed_tags(self):
        return self.tags_stack.copy()
    
    def get_unclosed_supported_tags(self):
        return self.supported_tags_stack.copy()

def split_text_by_sentences(text: str, max_len: int = MAX_LEN):
    cleaned_text = clean_telegram_content(text)
    
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    chunks = []
    current_chunk = ""
    tag_balance = []
    
    for sentence in sentences:
        parser = TagBalanceChecker()
        try:
            parser.feed(sentence)
        except:
            new_unclosed = []
        else:
            new_unclosed = parser.get_unclosed_supported_tags()
        
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
        
        for tag in new_unclosed:
            if tag in tag_balance:
                tag_balance.remove(tag)
            else:
                tag_balance.append(tag)
    
    if current_chunk:
        if tag_balance:
            current_chunk += ''.join(f'</{tag}>' for tag in reversed(tag_balance))
        chunks.append(current_chunk.strip())
    
    return chunks
