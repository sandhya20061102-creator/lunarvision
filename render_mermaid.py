import re
import base64
import json
import zlib

def replace_mermaid(match):
    mermaid_code = match.group(1).strip()
    
    # We can also use kroki which is much simpler: base64(zlib(text))
    # kroki.io/mermaid/svg/{payload}
    compressed = zlib.compress(mermaid_code.encode('utf-8'), 9)
    b64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    url = f"https://kroki.io/mermaid/svg/{b64_str}"
    
    return f"![Mermaid Diagram]({url})"

with open("LunarVision_Final_Detailed_Project_Report.md", "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r'```mermaid(.*?)```', re.DOTALL)
new_content = pattern.sub(replace_mermaid, content)

with open("LunarVision_Final_Detailed_Project_Report_Rendered.md", "w", encoding="utf-8") as f:
    f.write(new_content)
