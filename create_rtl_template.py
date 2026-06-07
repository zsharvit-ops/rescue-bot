"""Creates an RTL .docx template by modifying python-docx default template."""
import zipfile, re, shutil, os, docx

default_template = os.path.join(os.path.dirname(docx.__file__), "templates", "default.docx")
out = "template_rtl.docx"
shutil.copy(default_template, out)

tmp = out + ".tmp"
with zipfile.ZipFile(out, "r") as zin:
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/settings.xml":
                xml = data.decode("utf-8")
                if "<w:bidi" not in xml:
                    xml = xml.replace("</w:settings>", "<w:bidi/></w:settings>")
                data = xml.encode("utf-8")
            elif item.filename == "word/styles.xml":
                xml = data.decode("utf-8")
                if "<w:pPrDefault>" in xml:
                    inner = xml.split("<w:pPrDefault>")[1].split("</w:pPrDefault>")[0]
                    if "<w:pPr>" not in inner:
                        xml = xml.replace("<w:pPrDefault>", '<w:pPrDefault><w:pPr><w:bidi/><w:jc w:val="right"/></w:pPr>')
                    else:
                        def fix_pp(m):
                            s = m.group(0)
                            if "w:bidi" not in s:
                                s = s.replace("</w:pPr>", '<w:bidi/><w:jc w:val="right"/></w:pPr>')
                            return s
                        xml = re.sub(r"<w:pPrDefault>.*?</w:pPrDefault>", fix_pp, xml, flags=re.DOTALL)
                else:
                    xml = xml.replace("</w:docDefaults>", '<w:pPrDefault><w:pPr><w:bidi/><w:jc w:val="right"/></w:pPr></w:pPrDefault></w:docDefaults>')
                def add_bidi(m):
                    s = m.group(0)
                    if "w:bidi" not in s:
                        s = s.replace("</w:pPr>", '<w:bidi/><w:jc w:val="right"/></w:pPr>')
                    return s
                xml = re.sub(r"<w:pPr>.*?</w:pPr>", add_bidi, xml, flags=re.DOTALL)
                data = xml.encode("utf-8")
            zout.writestr(item, data)
os.replace(tmp, out)
print("Created RTL template:", out)
