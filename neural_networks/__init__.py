from openai import OpenAI
from config import OPENAI_API_KEY
from neural_networks.gpt import GPT 

client = OpenAI(api_key=OPENAI_API_KEY)

gpt = GPT(client)
