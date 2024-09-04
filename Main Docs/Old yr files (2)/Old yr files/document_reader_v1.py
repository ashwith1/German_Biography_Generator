#pip install python-docx

from summarizer import Summarizer
import docx

def read_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def summarize_document(file_path):
    summarizer = Summarizer()
    input_text = read_text_from_docx(file_path)
    summary = summarizer.generate_summary(input_text)
    return summary

if __name__ == "__main__":
    # Example usage
    document_path = "Transkript_sample.docx"
    summarized_text = summarize_document(document_path)
    print(summarized_text)
