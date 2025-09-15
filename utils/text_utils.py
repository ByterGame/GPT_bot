import re
import logging
from html import escape as html_escape
from html.parser import HTMLParser
from typing import List
from aiogram.exceptions import TelegramBadRequest


ALLOWED_TAGS = {
    "b","strong","i","em","u","ins","s","strike","del",
    "a","code","pre","blockquote","span"
}
ALLOWED_ATTRS = {
    "a": {"href"},
    "code": {"class"},      
    "span": {"class"},      
}
SAFE_URI_SCHEMES = ("http://", "https://", "tg://", "mailto:", "ftp://")
TAG_RE = re.compile(r"</?([a-zA-Z0-9]+)(\s[^>]*)?>")
class TelegramHTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.stack: list[str] = []      
        self.open_tags_src: list[str] = []  
        self.in_pre: bool = False
        self.in_pre_code: bool = False
    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            return
        if tag == "br":
            self.out.append("\n")
            return
        attrs_dict = {k.lower(): v for k, v in attrs if isinstance(k, str)}
        clean_attrs: list[tuple[str, str]] = []
        if tag == "span":
            cls = attrs_dict.get("class", "")
            if cls != "tg-spoiler":
                return
            clean_attrs.append(("class", "tg-spoiler"))
        elif tag == "a":
            href = attrs_dict.get("href")
            if not href:
                return
            href = href.strip()
            lh = href.lower()
            if not any(lh.startswith(s) for s in SAFE_URI_SCHEMES):
                return
            clean_attrs.append(("href", href))
        elif tag == "code":
            if self.in_pre:
                cls = attrs_dict.get("class", "")
                if cls.startswith("language-"):
                    clean_attrs.append(("class", cls))
                self.in_pre_code = True
            else:
                pass
        elif tag == "pre":
            self.in_pre = True
        if self.in_pre_code and tag not in {"code","pre"}:
            return
        attrs_src = "".join(f' {k}="{html_escape(str(v), quote=True)}"' for k, v in clean_attrs)
        full = f"<{tag}{attrs_src}>"
        self.out.append(full)
        self.stack.append(tag)
        self.open_tags_src.append(full)
    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag not in ALLOWED_TAGS:
            return
        if tag == "br":
            self.out.append("\n")
            return
            
        if tag == "p":
            if self.out and self.out[-1] not in {"\n", "<br>"}:
                self.out.append("\n\n")
            return
            
        if tag == "html":
            return
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                self.open_tags_src.pop()
                self.out.append(f"</{top}>")
                if top == tag:
                    break
        if tag == "pre":
            self.in_pre = False
        if tag == "code":
            self.in_pre_code = False
    def handle_data(self, data: str) -> None:
        self.out.append(html_escape(data, quote=False))
    def handle_entityref(self, name: str) -> None:
        self.out.append(f"&{name};")
    def handle_charref(self, name: str) -> None:
        self.out.append(f"&#{name};")
    def close(self) -> None:
        super().close()
        while self.stack:
            tag = self.stack.pop()
            self.open_tags_src.pop()
            self.out.append(f"</{tag}>")
    def result(self) -> str:
        return "".join(self.out)
    

def sanitize_html_for_telegram(html: str) -> str:
    parser = TelegramHTMLSanitizer()
    parser.feed(html)
    parser.close()
    return parser.result()


def escape_user_text(s: str) -> str:
    return html_escape(s, quote=False)


def split_html_for_telegram(html: str, limit: int = 4000) -> List[str]:
    
    parts: List[str] = []
    i = 0
    n = len(html)
    while i < n:
        start = i
        stack_open_tags: list[str] = []  
        names: list[str] = []            
        last_safe_break = i
        j = i
        while j < n:
            closers = "".join(f"</{name}>" for name in reversed(names))
            if j - start + len(closers) >= limit:
                break
            ch = html[j]
            if ch == "&":
                k = html.find(";", j + 1)
                if k == -1:
                    k = j
                j = k + 1
                continue
            if ch == "<":
                m = TAG_RE.match(html, j)
                if m:
                    tag_name = m.group(1).lower()
                    full_tag = m.group(0)
                    is_close = full_tag.startswith("</")
                    is_self = full_tag.lower().startswith("<br") and full_tag.endswith(">")
                    if not is_self:
                        if is_close:
                            if tag_name in names:
                                while names:
                                    top = names.pop()
                                    stack_open_tags.pop()
                                    if top == tag_name:
                                        break
                        else:
                            names.append(tag_name)
                            stack_open_tags.append(full_tag)
                    j = m.end()
                    last_safe_break = j
                    continue
            if ch in {" ", "\n", "\t"}:
                last_safe_break = j + 1
            j += 1
        if j >= n:
            cut = n
        else:
            cut = last_safe_break if last_safe_break > start else j
        chunk_body = html[start:cut]
        closers = "".join(f"</{name}>" for name in reversed(names))
        parts.append(chunk_body + closers)
        reopen = "".join(stack_open_tags)
        i = cut
        if reopen:
            html = html[:i] + reopen + html[i:]
            n = len(html)
            i += len(reopen)
    return parts


def html_to_plain(html: str) -> str:
    import re
    from html import unescape
    s = re.sub(r"</p\s*>", "\n\n", html, flags=re.I)
    s = re.sub(r"<p(\s[^>]*)?>", "", s, flags=re.I)
    
    s = re.sub(r"</?html[^>]*>", "", s, flags=re.I)
    s = re.sub(r"<pre>\s*<code[^>]*>(.*?)</code>\s*</pre>", lambda m: "\n"+unescape(m.group(1))+"\n", html, flags=re.S|re.I)
    s = re.sub(
        r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        lambda m: f"{unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()} ({m.group(1)})",
        s,
        flags=re.S | re.I
    )
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p\s*>", "\n\n", s, flags=re.I)
    s = re.sub(r"<p(\s[^>]*)?>", "", s, flags=re.I)
    s = re.sub(r"</?(b|strong|i|em|u|ins|s|strike|del|span|blockquote|code|pre)\b[^>]*>", "", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return unescape(s).strip()

def _extract_offset_from_error(e: Exception) -> int | None:
    m = re.search(r"byte offset (\d+)", str(e))
    return int(m.group(1)) if m else None

def _show_error_context(html: str, offset_bytes: int, radius: int = 120) -> str:
    b = html.encode("utf-8", errors="ignore")
    start = max(0, offset_bytes - radius)
    end = min(len(b), offset_bytes + radius)
    snippet = b[start:end].decode("utf-8", errors="ignore")
    return snippet

async def safe_send_message(message, reply_html: str, limit: int = 4000, *, disable_preview: bool = True):
    safe = sanitize_html_for_telegram(reply_html)

    try:
        parts = split_html_for_telegram(safe, limit=limit)
    except Exception as split_err:
        parts = [safe]

    for idx, part in enumerate(parts, 1):
        try:
            await message.answer(
                part,
                parse_mode="HTML",
                disable_web_page_preview=disable_preview,
            )
        except TelegramBadRequest as e:
            off = _extract_offset_from_error(e)
            if off is not None:
                ctx = _show_error_context(part, off)
                logging.error(f"[Telegram HTML parse error] part {idx}/{len(parts)} at byte {off}\nContext:\n{ctx}\n")

            try:
                cleaned_again = sanitize_html_for_telegram(part)
                await message.answer(
                    cleaned_again,
                    parse_mode="HTML",
                    disable_web_page_preview=disable_preview,
                )
                continue
            except TelegramBadRequest:
                plain = html_to_plain(part)
                await message.answer(
                    plain,
                    disable_web_page_preview=disable_preview,
                )