# !huggingface-cli login --token "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"

import torch
import transformers
from transformers import AutoTokenizer
from  langchain import LLMChain, HuggingFacePipeline, PromptTemplate

model = "meta-llama/Llama-2-7b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model)

pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    device_map="auto",
    max_length=4000,
    do_sample=True,
    top_k=10,
    num_return_sequences=1,
    eos_token_id=tokenizer.eos_token_id
)

llm = HuggingFacePipeline(pipeline = pipeline, model_kwargs = {'temperature':0})

template = """
              Write a concise summary of the following interview delimited by triple backquotes.
              Return your response in German language which covers the key points of the text.
              ```{text}```
              SUMMARY:
           """

prompt = PromptTemplate(template=template, input_variables=["text"])
llm_chain = LLMChain(prompt=prompt, llm=llm)

print(llm_chain.run(text))