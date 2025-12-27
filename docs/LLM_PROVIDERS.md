# LLM Providers

Victus supports multiple large language model providers through a shared interface.
By default, a local [Ollama](https://ollama.com/) server is used. OpenAI can be
selected via configuration.

## Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | Select the provider (`ollama` or `openai`). | `ollama` |
| `OLLAMA_BASE_URL` | Base URL for the Ollama server. | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name to request from Ollama. | `llama3.1:8b` |
| `OPENAI_API_KEY` | Required when `LLM_PROVIDER=openai`. | _none_ |

## Using Ollama

1. Install Ollama and pull a model, for example `ollama pull llama3.1:8b`.
2. Start the server if it is not already running:

   ```bash
   ollama serve
   ```

3. (Optional) Override defaults:

   ```bash
   export LLM_PROVIDER=ollama
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODEL=llama3.1:8b
   ```

## Using OpenAI

1. Set your API key and switch providers:

   ```bash
   export OPENAI_API_KEY="sk-..."
   export LLM_PROVIDER=openai
   ```

2. Start Victus. The productivity LLM plugin will route requests to OpenAI when
   allowed by policy.
