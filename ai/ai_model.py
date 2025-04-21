from ctransformers import AutoModelForCausalLM
#
# llm = AutoModelForCausalLM.from_pretrained(
#     "./llama-2-7b-chat.ggmlv3.q8_0.bin",
#     model_type="llama",
#     gpu_layers=0,
#     threads=12,
#     context_length=2048,
#     batch_size=1
# )
#
#
# response = llm(
#     "how are you? my name is Egor, you?",
#     temperature=0.7,
#     top_k=40,
#     top_p=0.9,
#     repetition_penalty=1.1,
#     max_new_tokens=150
# )
#
# print(response)