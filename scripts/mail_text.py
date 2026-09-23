import subprocess, sys, email, re, html
mid = sys.argv[1]
raw = subprocess.run(["himalaya","message","read",mid,"--account","gmail","--raw"],
                     capture_output=True).stdout
msg = email.message_from_bytes(raw)
txt = None
for part in msg.walk():
    ct = part.get_content_type()
    if ct == "text/plain":
        txt = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
        break
if txt is None:
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            h = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
            h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
            h = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</tr>", "\n", h)
            txt = html.unescape(re.sub(r"(?s)<[^>]+>", " ", h))
            break
txt = re.sub(r"[ \t\r\f\v]+", " ", txt or "")
txt = re.sub(r"\n\s*\n+", "\n", txt)
lim = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
print(txt.strip()[:lim])
