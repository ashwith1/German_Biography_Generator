from langchain_together import Together
import json

def test_api():
    # Initialize the Together API client
    llm = Together(
        model="meta-llama/Llama-3-8b-hf",
        temperature=0.1,
        max_tokens=1024,
        top_k=1,
        together_api_key="89f6359c5009e4d13ca731bb9085bf686123aa816e64ede39a6b295143c086c3"
    )

    # Define a simple test input and prompt
    input_text = "Dies ist ein einfacher Test."
    prompt = "Schreiben Sie einen kurzen Absatz basierend auf dem obigen Text."
    full_input = input_text + prompt
    print("Sending to API:", full_input)

    try:
        # Invoke the API with the full input
        output_summary = llm.invoke(full_input)
        print("API Response:", output_summary)
    except ValueError as e:
        # Handle and print detailed API error information
        error_response = e.args[0] if e.args else str(e)
        try:
            error_json = json.loads(error_response)
            print("API Error:", json.dumps(error_json, indent=2))
        except json.JSONDecodeError:
            print("API Error:", error_response)
    except Exception as e:
        # Handle any other unexpected exceptions
        print("Unexpected Error:", str(e))

if __name__ == "__main__":
    test_api()
