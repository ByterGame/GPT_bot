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
            if tag_lower in self.current_context:
                while self.current_context:
                    current_tag = self.current_context.pop()
                    self.result.append(f"</{current_tag}>")
                    if current_tag == 'code':
                        self.in_code_block = False
                    elif current_tag == 'pre':
                        self.in_pre_block = False
                    if current_tag == tag_lower:
                        break
        
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

def clean_css_and_escape(text: str) -> str:
    text = re.sub(r':root\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'body\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'\.\w+\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'header\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'footer\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'a\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'code\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'pre\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'table\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'th\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'td\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'figure\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'figcaption\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'details\s*\{.*?\}\s*', '', text, flags=re.DOTALL)
    
    text = text.replace('\\-', '-')
    text = text.replace('\\.', '.')
    text = text.replace('\\:', ':')
    text = text.replace('\\;', ';')
    text = text.replace('\\{', '{')
    text = text.replace('\\}', '}')
    text = text.replace('\\#', '#')
    text = text.replace('\\ ', ' ')
    text = text.replace('\\>', '>')
    
    text = re.sub(r'var\([^)]*\)', '', text)
    text = re.sub(r'#[0-9a-fA-F]{3,6}', '', text)
    text = re.sub(r'\d*\.?\d+px', '', text)
    text = re.sub(r'\d+%', '', text)
    
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def clean_telegram_content(text: str) -> str:
    if not text or not text.strip():
        return text
    
    text = clean_css_and_escape(text)

    text = re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\?xml[^>]*\?>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    return parse_mixed_content(text)

class TagBalanceChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags_stack = []
    
    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in SUPPORTED_TAGS:
            self.tags_stack.append(tag_lower)
    
    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if self.tags_stack and self.tags_stack[-1] == tag_lower:
            self.tags_stack.pop()
    
    def get_unclosed_tags(self):
        return self.tags_stack.copy()

def validate_html(html: str) -> bool:
    try:
        parser = HTMLParser()
        parser.feed(html)
        return True
    except:
        return False

def split_text_by_sentences(text: str, max_len: int = MAX_LEN):
    cleaned_text = clean_telegram_content(text)
    
    if not re.search(r'<[a-zA-Z][^>]*>', cleaned_text):
        chunks = []
        for i in range(0, len(cleaned_text), max_len):
            chunks.append(cleaned_text[i:i+max_len])
        return chunks
    
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
            new_unclosed = parser.get_unclosed_tags()
        
        if len(current_chunk) + len(sentence) + 1 > max_len:
            if tag_balance:
                closed_chunk = current_chunk + ''.join(f'</{tag}>' for tag in reversed(tag_balance))
                if validate_html(closed_chunk):
                    chunks.append(closed_chunk.strip())
                else:
                    chunks.append(re.sub(r'<[^>]*>', '', current_chunk).strip())
                
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
        if validate_html(current_chunk):
            chunks.append(current_chunk.strip())
        else:
            chunks.append(re.sub(r'<[^>]*>', '', current_chunk).strip())
    
    return chunks

async def safe_send_message(message, text: str, max_len: int = MAX_LEN):
    try:
        chunks = split_text_by_sentences(text, max_len)
        
        for chunk in chunks:
            parse_mode = 'HTML' if re.search(r'<[a-zA-Z][^>]*>', chunk) else None
            
            try:
                await message.answer(chunk, parse_mode=parse_mode)
            except Exception as e:
                if 'parse entities' in str(e).lower():
                    plain_text = re.sub(r'<[^>]*>', '', chunk)
                    await message.answer(plain_text, parse_mode=None)
                else:
                    raise
                    
    except Exception as e:
        plain_text = re.sub(r'<[^>]*>', '', text)
        for i in range(0, len(plain_text), max_len):
            await message.answer(plain_text[i:i+max_len], parse_mode=None)