#!/bin/sh

# Start Ollama REST server in the background
ollama serve &
OLLAMA_PID=$!

# Wait for the REST server to be ready
echo "Waiting for Ollama to start..."
until curl -s http://dg-ollama:11434/ > /dev/null; do
  sleep 1
done
echo "Ollama is ready."

for MODEL_NAME in "mistral" "nomic-embed-text" 
do
# Check if the model is already downloaded
  if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "Downloading model $MODEL_NAME..."
    ollama pull "$MODEL_NAME"
  else
    echo "Model $MODEL_NAME already exists."
  fi
done
# Wait for the Ollama server process to keep running
wait $OLLAMA_PID