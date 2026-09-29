import sys
from markdown_pdf import Section, MarkdownPdf

def convert_md_to_pdf(md_file, pdf_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Configure PDF
    pdf = MarkdownPdf(toc_level=2)
    
    # Add section with the markdown content
    pdf.add_section(Section(content))
    
    # Save to file
    pdf.save(pdf_file)
    print(f"Successfully created {pdf_file}")

if __name__ == "__main__":
    convert_md_to_pdf("LunarVision_Final_Detailed_Project_Report.md", "LunarVision_Final_Detailed_Project_Report.pdf")



