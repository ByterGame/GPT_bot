import re
from html.parser import HTMLParser
from aiogram.exceptions import TelegramBadRequest

MAX_LEN = 4000

SUPPORTED_TAGS = {
    'b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del',
    'a', 'code', 'pre', 'tg-spoiler'
}

MARKDOWN_SPECIAL_CHARS = r'\_*\[\]()~`>#\+\-=\|{}\.!'

class MixedContentParser:
    def __init__(self):
        self.result = []
        self.open_tags = [] 
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
            
            self.open_tags.append(tag_lower)
            attrs_str = ""
            if tag_lower == 'a' and 'href' in attrs:
                href = attrs['href']
                href = href.replace('&', '&amp;').replace('"', '&quot;')
                attrs_str = f' href="{href}"'
            self.result.append(f"<{tag}{attrs_str}>")
        else:
            if self.open_tags and self.open_tags[-1] == tag_lower:
                closed_tag = self.open_tags.pop()
                self.result.append(f"</{closed_tag}>")
                if closed_tag == 'code':
                    self.in_code_block = False
                elif closed_tag == 'pre':
                    self.in_pre_block = False
        
        return True
    
    def handle_markdown(self, text: str):
        if not text.strip():
            return
        
        escaped_text = self.escape_markdown(text)
        self.result.append(escaped_text)
    
    def get_content(self):
        while self.open_tags:
            tag = self.open_tags.pop()
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
    """Очищает CSS и экранирует текст"""
    text = re.sub(r'[a-zA-Z\-]+\s*\{.*?\}', '', text, flags=re.DOTALL)
    text = re.sub(r':root|body|header|footer|figure|figcaption|details', '', text, flags=re.IGNORECASE)
    
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    
    text = re.sub(r'var\([^)]*\)', '', text)
    text = re.sub(r'#[0-9a-fA-F]{3,6}', '', text)
    text = re.sub(r'\d*\.?\d+px', '', text)
    text = re.sub(r'\d+%', '', text)
    
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_telegram_content(text: str) -> str:
    if not text or not text.strip():
        return text
    
    text = clean_css_and_escape(text)
    text = re.sub(r'<!DOCTYPE[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\?xml[^>]*\?>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    return parse_mixed_content(text)

def split_text_by_sentences(text: str, max_len: int = MAX_LEN):
    cleaned_text = clean_telegram_content(text)
    
    if len(cleaned_text) <= max_len:
        return [cleaned_text]
    
    chunks = []
    for i in range(0, len(cleaned_text), max_len):
        chunk = cleaned_text[i:i+max_len]
        chunks.append(chunk)
    
    return chunks

async def safe_send_message(message, text: str, max_len: int = MAX_LEN):
    if not text or not text.strip():
        return
    
    try:
        chunks = split_text_by_sentences(text, max_len)
        
        for chunk in chunks:
            try:
                if is_valid_html(chunk):
                    await message.answer(chunk, parse_mode='HTML')
                else:
                    await message.answer(chunk, parse_mode=None)
                    
            except TelegramBadRequest as e:
                if "can't parse entities" in str(e).lower():
                    plain_text = re.sub(r'<[^>]*>', '', chunk)
                    await message.answer(plain_text, parse_mode=None)
                else:
                    raise
                    
    except Exception as e:
        plain_text = re.sub(r'<[^>]*>', '', text)
        if plain_text:
            for i in range(0, len(plain_text), max_len):
                await message.answer(plain_text[i:i+max_len], parse_mode=None)

def is_valid_html(html: str) -> bool:
    """Проверяет валидность HTML для Telegram"""
    try:
        open_tags = []
        pattern = re.compile(r'<(/?)([a-zA-Z0-9\-]+)(?:\s+[^>]*)?>')
        
        for match in pattern.finditer(html):
            is_closing = bool(match.group(1))
            tag = match.group(2).lower()
            
            if tag.startswith('!') or tag.startswith('?'):
                continue
                
            if tag not in SUPPORTED_TAGS:
                return False
                
            if is_closing:
                if not open_tags or open_tags[-1] != tag:
                    return False
                open_tags.pop()
            else:
                if tag == 'a':
                    attrs_str = match.group(0)
                    if 'href=' not in attrs_str:
                        return False
                open_tags.append(tag)
        
        return len(open_tags) == 0
    except:
        return False