import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from langchain_together import Together
import time

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
            max_tokens= 1024,  # Reduce the max tokens to handle smaller chunks
            top_k=1,
            together_api_key="3547c556949e8b9beea25d84c997eebd60a491f60e33548b59a51f86f313a277"
        )

    def invoke_with_retry(self, full_input, retries=3, retry_delay=30):
        for attempt in range(retries):
            try:
                output_summary = self.llm.invoke(full_input)
                return output_summary
            except Exception as e:
                if "524" in str(e) and attempt < retries - 1:
                    print(f"Error 524: Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(retry_delay)
                    retries += 1

                else:
                    raise

    def generate_biography(self, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 1024  # Smaller max tokens for each chunk
        self.llm.top_k = 1
        
        prompt = """
        Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des obigen Textes in deutscher Sprache innerhalb von 500 Wörtern. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit. Work only with the data given and do not provide your conclusions or interpretations of the biography or the data provided. Work only with the data.
        """
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk = 70000)
        biography_parts = []
        
        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            biography_parts.append(output_summary.strip())

        full_biography = " ".join(biography_parts)
        return full_biography

    def extend_biography(self, partial_biography, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 800  # Smaller max tokens for each chunk
        self.llm.top_k = 1
        
        prompt = f"""
        Hier ist der erste Teil der Biografie: {partial_biography}
        Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
        """

        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
        extended_biography_parts = []
        
        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            extended_biography_parts.append(output_summary.strip())

        full_extended_biography = " ".join(extended_biography_parts)
        return self.remove_incomplete_sentence(full_extended_biography)

    def refine_biography_to_500_words(self, extended_biography, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 512
        self.llm.top_k = 1

        prompt = f"""
Hier ist der erste Teil der Biografie: {extended_biography}
        Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
                """
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
        refined_parts = []

        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            refined_parts.append(output_summary.strip())

        full_refined_biography = " ".join(refined_parts)
        return self.remove_incomplete_sentence(full_refined_biography)

    def remove_incomplete_sentence(self, biography):
        words = word_tokenize(biography)
        if len(words) <= 500:
            return biography
        
        truncated_words = words[:500]
        truncated_text = " ".join(truncated_words)
        last_full_stop_index = truncated_text.rfind('.')
        
        if last_full_stop_index != -1:
            return truncated_text[:last_full_stop_index + 1]
        else:
            return truncated_text

def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


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
    else:
        print("Unsupported file format.")
        return

    # Step 1: Generate the initial biography with chunking
    initial_biography = summarizer.generate_biography(transcript_data)
    print("Initial Biography : \n", initial_biography.strip())

    # Step 2: Extend the biography with additional details, also using chunking
    extended_biography = summarizer.extend_biography(initial_biography, transcript_data)
    print("Extended Biography : \n", extended_biography.strip())

    # Step 3: Refine the biography to 500 words and remove incomplete sentences
    refined_biography = summarizer.refine_biography_to_500_words(extended_biography, transcript_data)
    print("Refined Biography (500 words) : \n", refined_biography.strip())

if __name__ == "__main__":
    file_path = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/WG_ [EXTERN]  Transcripts and Biographies/adg0001_er_2024_04_23.csv"
    process_file(file_path)