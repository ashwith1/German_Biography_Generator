import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from langchain_together import Together
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from docx import Document

nltk.download('punkt')

# Function to extract rows from a DataFrame where 'Sprecher' column starts with the specified prefix.
def extract_rows_with_sprecher(df, sprecher_prefix):
    df = df.dropna(subset=['Sprecher'])
    filtered_rows = df[df['Sprecher'].str.startswith(sprecher_prefix)]
    transkript_list = filtered_rows['Transkript'].tolist()
    return transkript_list

# Function to convert the 'Transkript' column to a single string.
def transkript_to_string(transkript_list):
    return "\n".join(transkript_list)

# Function to divide text into chunks close to a specified maximum number of words without cutting through sentences.
def divide_into_chunks(text, max_words_per_chunk):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        words_in_sentence = len(word_tokenize(sentence))
        if current_word_count + words_in_sentence > max_words_per_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = words_in_sentence
        else:
            current_chunk.append(sentence)
            current_word_count += words_in_sentence

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

class Summarizer:
    def __init__(self):
        self.llm = Together(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            temperature=0.1,
            max_tokens= 4098,
            top_k=1,
            together_api_key="9a1701e1766922590c8190108624640c185bbaa3b8531519c2ad8e4c0df498bb"
        )
        self.llm2 = Together(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            temperature=0.1,
            max_tokens= 512,
            top_k=1,
            together_api_key="9a1701e1766922590c8190108624640c185bbaa3b8531519c2ad8e4c0df498bb"
        )
        self.llm1 = Together(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.4,
            max_tokens= 300,
            top_k=1,
            together_api_key="9a1701e1766922590c8190108624640c185bbaa3b8531519c2ad8e4c0df498bb"
        )

    def generate_biography(self, input_text):
        prompt = """
    Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des obigen Textes in deutscher Sprache innerhalb von 500 Wörtern. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit. Work only with the data given and do not provide your conclusions or interpretations of the biography or the data provided. Work only with the data.
        """
        full_input = input_text + prompt
        retry_delay = 30

        while True:
            try:
                output_summary = self.llm.invoke(full_input)
                return output_summary
            except Exception as e:
                if "rate limited" in str(e).lower():
                    print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"An error occurred: {e}")
                    raise

    def final_biography(self, input_text):
        prompt1 = """
Bitte erstellen Sie eine Biografie auf Basis des untenstehenden Textes in deutscher Sprache mit maximal 500 Wörtern. Work only with the data given and do not provide your conclusions or interpretations of the biography or the data provided. Work only with the data.
        """
        full_input = input_text + prompt1
        retry_delay = 30

        while True:
            try:
                output_summary = self.llm1.invoke(full_input)
                return output_summary
            except Exception as e:
                if "rate limited" in str(e).lower():
                    print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"An error occurred: {e}")
                    raise

    def refine_biography(self, input_text):
        def truncate_to_word_limit(text, limit):
            words = word_tokenize(text)
            if len(words) > limit:
                words = words[:limit]
            return ' '.join(words)

        words = word_tokenize(input_text)

        if len(words) <= 500:
            return input_text

        sentences = sent_tokenize(input_text)
        refined_text = ""
        current_word_count = 0

        for sentence in sentences:
            sentence_word_count = len(word_tokenize(sentence))
            if current_word_count + sentence_word_count <= 500:
                refined_text += sentence + " "
                current_word_count += sentence_word_count
            else:
                break

        refined_text = refined_text.strip()
        refined_text = truncate_to_word_limit(refined_text, 500)

        return refined_text

    def final_2_biography(self, input_text):
        prompt = """
        Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des oben genannten Textes auf Deutsch innerhalb von 500 Wörtern und behalten Sie alle wichtigen Daten bei. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit.
                """
        full_input = input_text + prompt
        retry_delay = 30

        while True:
            try:
                output_summary = self.llm2.invoke(full_input)
                return output_summary
            except Exception as e:
                if "rate limited" in str(e).lower():
                    print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"An error occurred: {e}")
                    raise

# Function to generate a biography from text chunks.
def generate_biography(summarizer, input_text):
    chunks = divide_into_chunks(input_text, 40000)
    summary = ""
    chunk_number = 1

    for chunk in chunks:
        print(f"Chunk {chunk_number}:")
        print(chunk)
        summary += summarizer.generate_biography(chunk) + "\n"
        chunk_number += 1
    return summary

# Function to read data from a CSV file.
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

# Function to read data from a DOCX file.
def read_docx(file_path):
    try:
        doc = Document(file_path)
        data = [p.text for p in doc.paragraphs if p.text]
        return " ".join(data)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None

def final_biography(summarizer, input_text):
    chunks = divide_into_chunks(input_text, 1000)
    summary = ""
    chunk_number = 1

    for chunk in chunks:
        summary += summarizer.final_biography(chunk) + "\n"
        chunk_number += 1
    return summary

def count_words(sentence):
    words = word_tokenize(sentence)
    return len(words)

def final_2_biography(summarizer, input_text):
    chunks = divide_into_chunks(input_text, 40000)
    summary = ""
    chunk_number = 1

    for chunk in chunks:
        summary += summarizer.final_2_biography(chunk) + "\n"
        chunk_number += 1
    return summary

def remove_incomplete_sentence(biography):
    last_full_stop_index = biography.rfind('.')
    if last_full_stop_index != -1:
        return biography[:last_full_stop_index + 1]
    else:
        return biography

# Main function to process the input file and generate a biography.
def process_file(file_path):
    summarizer = Summarizer()
    
    if file_path.endswith('.csv'):
        df = read_csv(file_path)
        if df is not None:
            sprecher_prefix = 'IP_'
            transkript_list = extract_rows_with_sprecher(df, sprecher_prefix)
            transcript_data = transkript_to_string(transkript_list)
        else:
            print("Failed to read CSV file.")
            return
    elif file_path.endswith('.docx'):
        transcript_data = read_docx(file_path)
        if not transcript_data:
            print("Failed to read DOCX file.")
            return
    else:
        print("Unsupported file format.")
        return

    biography = generate_biography(summarizer, transcript_data)
    print("Biography : \n ", count_words(biography), biography.strip())

    x_biography = final_biography(summarizer, biography)
    summary = remove_incomplete_sentence(x_biography)
    print("Summary : \n ", count_words(summary), summary.strip())

    if count_words(summary) <= 600:
        refined_biography = summarizer.refine_biography(summary)
        print("Refined : \n", count_words(refined_biography), refined_biography.strip())
    else:
        x = remove_incomplete_sentence(summary)
        x1_biography = final_2_biography(summarizer, x)
        summary1 = remove_incomplete_sentence(x1_biography)
        print("Summary 1: ", count_words(summary1), summary1.strip())

if __name__ == "__main__":
    #file_path = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/WG_ [EXTERN]  Transcripts and Biographies/adg0001_er_2024_04_23.csv"
    file_path = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/WG_ [EXTERN]  Transcripts and Biographies/adg0002_er_2024_04_23.csv"
    process_file(file_path)
