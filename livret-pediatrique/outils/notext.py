import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
r=PdfReader(sys.argv[1]); w=PdfWriter()
for page in r.pages:
    cs=ContentStream(page.get_contents(), r)
    ops=[]; intext=False
    for operands,op in cs.operations:
        if op==b'BT': intext=True; continue
        if op==b'ET': intext=False; continue
        if intext and op in (b'Tj',b'TJ',b"'",b'"'): continue
        if intext: ops.append((operands,op)); continue
        ops.append((operands,op))
    cs.operations=ops
    page[NameObject('/Contents')]=w._add_object(cs) if False else cs
    w.add_page(page)
w.write(sys.argv[2])
