import ollama

models = ollama.list()
print('Installed Ollama models:')
print('=' * 80)
for m in models['models']:
    print(f"  - {m.model}")
print('=' * 80)
