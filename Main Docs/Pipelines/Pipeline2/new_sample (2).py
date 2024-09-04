import docx
import pandas as pd
from llama3 import Summarizer
import time

def read_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        return '\n'.join(paragraphs)
    except Exception as e:
        print(f"Error reading document: {e}")
        return None

def read_text_from_csv(file_path):
    try:
        return pd.read_csv(file_path, sep='\t')
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def chunk_text(text, max_words=1000):
    words = text.split()
    chunks = [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]
    return chunks

def process_text_file(file_path):
    if file_path.endswith('.docx'):
        text = read_text_from_docx(file_path)
    elif file_path.endswith('.csv'):
        df = read_text_from_csv(file_path)
        text = ' '.join(df['Transkript'].dropna().tolist()) if 'Transkript' in df.columns else ''
    else:
        print("Unsupported file type")
        return

    if text:
        summarizer = Summarizer()
        chunks = chunk_text(text)
        biography_texts = []
        for chunk in chunks:
            biography = summarizer.generate_biography(chunk)
            biography_texts.append(biography)
        
        final_biography = "\n\n".join(biography_texts)
        print("Final Biography Text:")
        print(final_biography)
    else:
        print("No text available for processing.")

if __name__ == "__main__":
    file_path = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/WG_ [EXTERN]  Transcripts and Biographies/adg0001_er_2024_04_23.csv"
    process_text_file(file_path)
