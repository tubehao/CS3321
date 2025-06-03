from openai import OpenAI

api_key = 'sk-TODO'

client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

response = client.chat.completions.create(
    model="qwen-turbo",
    messages=[
        {'role': 'user', 'content': "Find the people who have cooperated with Yann LeCun most frequently."}
    ]
)
print(response.choices[0].message.content)