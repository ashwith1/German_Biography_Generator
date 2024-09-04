from langchain_together import Together

class Summarizer:
    def __init__(self):
        self.llm = Together(
            # model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            # model = "snorkelai/Snorkel-Mistral-PairRM-DPO",
            # model = "togethercomputer/StripedHyena-Nous-7B",
            # model = "upstage/SOLAR-10.7B-Instruct-v1.0",
            model = "mistralai/Mistral-7B-Instruct-v0.2",
            # model = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-SFT",
            temperature=0.1,
            max_tokens=512,
            top_k=1,
            together_api_key="a985c29ac716c499ebb9de7c125a15d984102855c1acd10ba9713403f94fc406"
        )

    def generate_summary(self, input_text):
        prompt = """
        You are a German text summarization model. Generate a concise summary of the above text in German language. Focus on key points and maintain clarity.
        """
        # prompt = """
        # You are a professional biography author. Write a biography of the above interview text in German language. Focus on key points and maintain clarity.
        # """

        full_input = input_text + prompt
        output_summary = self.llm.invoke(full_input)
        return output_summary

    def improve_coherence(self, input_text):
        # prompt = """
        # You are a German text summarization model. Generate a concise summary of the above text in German language. Focus on key points and maintain clarity.
        # """
        prompt = """
        You are a professional biography author. Write a biography of the above interview summary in German language. Focus on key points and maintain clarity.
        """

        full_input = input_text + prompt
        output_summary = self.llm.invoke(full_input)
        return output_summary
