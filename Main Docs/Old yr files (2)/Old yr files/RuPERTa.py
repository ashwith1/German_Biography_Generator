from transformers import pipeline

# Load the question-answering pipeline with the fine-tuned model
qa_pipeline = pipeline("question-answering", model="mrm8488/RuPERTa-base-finetuned-squadv2", tokenizer="mrm8488/RuPERTa-base-finetuned-squadv2")

# Your input text that you want to summarize
input_text = """
Der Sommer legte seine warme Decke über das Land, und die Tage wurden länger.
"""

# Set a minimum length for the input text
min_length = 20

# Ask a dummy question to prompt the model to generate a summary
dummy_question = "Summarize the following text: " + input_text

# Check if the input text is too short
if len(input_text.split()) < min_length:
    print("Text is too short for summarization. Using the original text as the summary.")
    summary = input_text
else:
    # Perform question-answering (which we're treating as summarization)
    try:
        result = qa_pipeline(question=dummy_question, context=input_text, max_length=512, truncation=True)
        summary = result["answer"]
    except Exception as e:
        print(f"Error: {e}")
        summary = "Error occurred during summarization."

# Print the generated summary
print(summary)
