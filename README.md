# browser_use
This application is using next.Js as frontend and flask as backend
## libraries required

```bash
pip install browser-use
playwright install
```

## Local LLM using ollama
```python
from langchain_ollama import ChatOllama
from browser_use import Agent
from pydantic import SecretStr


# Initialize the model
llm=ChatOllama(model="qwen2.5", num_ctx=32000)

# Create agent with the model
agent = Agent(
    task="Your task here",
    llm=llm
)
```
