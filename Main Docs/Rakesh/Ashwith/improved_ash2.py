import pandas as pd
import nltk
import asyncio
from nltk.tokenize import word_tokenize, sent_tokenize
from langchain_together import Together
from docx import Document

nltk.download('punkt')

def extract_rows_with_sprecher(df, sprecher_prefix):
    df = df.dropna(subset=['Sprecher'])
    filtered_rows = df[df['Sprecher'].str.startswith(sprecher_prefix)]
    transkript_list = filtered_rows['Transkript'].tolist()
    return transkript_list

def transkript_to_string(transkript_list):
    return "\n".join(transkript_list)

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
            max_tokens=4098,
            top_k=1,
            together_api_key="9a1701e1766922590c8190108624640c185bbaa3b8531519c2ad8e4c0df498bb"
        )
        self.llm2 = Together(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            temperature=0.1,
            max_tokens=512,
            top_k=1,
            together_api_key="9a1701e1766922590c8190108624640c185bbaa3b8531519c2ad8e4c0df498bb"
        )

    async def generate_biography(self, input_text):
        chunks = divide_into_chunks(input_text, 50000)  # Adjust the chunk size as necessary
        summary = ""
        
        for chunk in chunks:
            prompt = """
            Du bist ein deutsches Textmodell, das Biografien erstellt. Schreibe eine detaillierte Biografie basierend auf dem folgenden Text. Behalte den chronologischen Fluss der Ereignisse bei und achte darauf, dass alle wichtigen Informationen enthalten sind. Vermeide es, den Text zu verallgemeinern oder zu stark zusammenzufassen.
            """
            full_input = chunk + prompt
            retry_delay = 60  # Increase delay
            max_retries = 5  # Limit the number of retries
            retries = 0

            while retries < max_retries:
                try:
                    output_summary = self.llm.invoke(full_input)  # Removed `await` here
                    summary += output_summary + "\n"  # Append each chunk's summary
                    break
                except Exception as e:
                    if "rate limited" in str(e).lower() or "error 524" in str(e).lower():
                        retries += 1
                        print(f"Error: {e}. Retrying in {retry_delay} seconds... ({retries}/{max_retries})")
                        await asyncio.sleep(retry_delay)  # Properly await asyncio.sleep
                    else:
                        print(f"An unrecoverable error occurred: {e}")
                        raise

        return summary

    async def run_with_refined_prompt(self, refined_text, transcript_data):
        chunks = divide_into_chunks(transcript_data, 60000)  # Adjust the chunk size as necessary
        summary = ""

        for chunk in chunks:
            prompt = f"""
            {refined_text}
Bitte analysieren Sie die folgenden Transkriptdaten anhand des oben verfeinerten Textes. Erstellen Sie aus den bereitgestellten Daten eine detaillierte Biografie, die den chronologischen Fluss der Ereignisse beibehält und alle wesentlichen Informationen berücksichtigt.
            """
            full_input = chunk + prompt
            retry_delay = 30
            max_retries = 5  # Adding retry logic similar to `generate_biography`
            retries = 0

            while retries < max_retries:
                try:
                    output_summary = self.llm2.invoke(full_input)  # Removed `await` here
                    summary += output_summary + "\n"
                    break
                except Exception as e:
                    if "rate limited" in str(e).lower():
                        retries += 1
                        print(f"Rate limit exceeded. Retrying in {retry_delay} seconds... ({retries}/{max_retries})")
                        await asyncio.sleep(retry_delay)  # Properly await asyncio.sleep
                    else:
                        print(f"An error occurred: {e}")
                        raise

        return summary

async def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

async def read_docx(file_path):
    try:
        doc = Document(file_path)
        data = [p.text for p in doc.paragraphs if p.text]
        return " ".join(data)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None

def count_words(sentence):
    words = word_tokenize(sentence)
    return len(words)

def remove_incomplete_sentence(biography):
    last_full_stop_index = biography.rfind('.')
    if last_full_stop_index != -1:
        return biography[:last_full_stop_index + 1]
    else:
        return biography

async def process_file(file_path):
    summarizer = Summarizer()
    
    if file_path.endswith('.csv'):
        df = await read_csv(file_path)
        if df is not None:
            sprecher_prefix = 'IP_'
            transkript_list = extract_rows_with_sprecher(df, sprecher_prefix)
            transcript_data = transkript_to_string(transkript_list)
        else:
            print("Failed to read CSV file.")
            return
    elif file_path.endswith('.docx'):
        transcript_data = await read_docx(file_path)
        if not transcript_data:
            print("Failed to read DOCX file.")
            return
    else:
        print("Unsupported file format.")
        return

    biography = await summarizer.generate_biography(transcript_data)
    print("Biography : \n ", biography)

    final_summary = await summarizer.run_with_refined_prompt(biography, transcript_data)
    print("Final Summary based on Refined Prompt: \n", final_summary)

if __name__ == "__main__":
    file_path = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/WG_ [EXTERN]  Transcripts and Biographies/adg0001_er_2024_04_23.csv"
    asyncio.run(process_file(file_path))