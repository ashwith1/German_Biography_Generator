import os
import glob
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize  # Importing the required functions
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
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
    sentences = sent_tokenize(text)  # Now, this will work as sent_tokenize is imported
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
            max_tokens=1024,
            top_k=1,
            together_api_key="9a1701e1766922590c8190108624640c185bbaa3b8531519c2ad8e4c0df498bb"
        )
# together_api_key="3547c556949e8b9beea25d84c997eebd60a491f60e33548b59a51f86f313a277"



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
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
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

    def refine_biography_to_500_words(self, extended_biography, transcript_data):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 512
        self.llm.top_k = 1

        prompt = f"""
        Hier ist der erste Teil der Biografie: {extended_biography}
        Using the above information, refine the biography to 500 words for other parts of the data and combine them in German. Focus on the key points and maintain clarity.
            """

        chunks = divide_into_chunks(transcript_data, max_words_per_chunk=70000)  # Corrected from 'hunks' to 'chunks'
        refined_parts = []

        for chunk in chunks:
            full_input = prompt + chunk
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
        # Attempt to read with different delimiters
        try:
            df = pd.read_csv(file_path, sep='\t')
        except pd.errors.ParserError:
            df = pd.read_csv(file_path, sep=',')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None



def save_biography_to_pdf(text, output_dir, filename_prefix="biography"):
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{filename_prefix}.pdf")
        c = canvas.Canvas(filename, pagesize=A4)
        text = text.split('\n')
        text = [line.strip() for line in text if line.strip() != '']
        width, height = A4
        left_margin = 72
        right_margin = width - 72
        y = height - 72
        max_width = right_margin - left_margin
        
        for line in text:
            wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)
            for wrapped_line in wrapped_lines:
                c.drawString(left_margin, y, wrapped_line)
                y -= 15
                if y < 72:
                    c.showPage()
                    y = height - 72
        
        c.save()
        print(f"Biography saved to {filename}")
        return filename
    except Exception as e:
        print(f"An error occurred while saving the PDF: {e}")
        return None

def process_file(file_path):
    summarizer = Summarizer()
    
    print(f"Processing file: {file_path}")  # Debugging statement
    
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

    # Generate and save biography
    initial_biography = summarizer.generate_biography(transcript_data)
    initial_biography = initial_biography.strip()

    extended_biography = summarizer.extend_biography(initial_biography, transcript_data)
    extended_biography = extended_biography.strip()

    refined_biography = summarizer.refine_biography_to_500_words(extended_biography, transcript_data)
    refined_biography = refined_biography.strip()


    output_dir = os.path.join(os.path.dirname(file_path), 'Output')
    filename_prefix = os.path.splitext(os.path.basename(file_path))[0]
    save_biography_to_pdf(refined_biography, output_dir, filename_prefix)

def process_all_files(directory):
    # Update to look inside the subdirectory
    target_directory = os.path.join(directory, 'WG_ [EXTERN]  Transcripts and Biographies')

    # Debugging: List all files in the directory
    all_files = os.listdir(target_directory)
    print("Files in target directory:", all_files)

    # Get all CSV files in the directory
    csv_files = [f for f in all_files if f.endswith('.csv')]
    print("CSV files identified:", csv_files)  # Debugging statement
    
    if not csv_files:
        print("No CSV files found in the directory.")
    
    for file_name in tqdm(csv_files, desc="Processing CSV files"):
        file_path = os.path.join(target_directory, file_name)
        print(f"Full path for processing: {file_path}")  # Debugging statement
        process_file(file_path)

class NewFileHandler(FileSystemEventHandler):
    def __init__(self, directory):
        self.directory = directory

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.csv'):
            response = input(f"New file detected: {event.src_path}. Do you want to process it? (y/n): ")
            if response.lower() == 'y':
                process_file(event.src_path)

def monitor_directory(directory):
    event_handler = NewFileHandler(directory)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    print(f"Monitoring directory: {directory}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    directory = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/"
    process_all_files(directory)
    monitor_directory(directory)