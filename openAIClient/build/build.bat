
rem pyinstaller --name=openAIClient --onefile --windowed --add-data "../openAIClient/assets;openAIClient/assets" --hidden-import tiktoken_ext --hidden-import tiktoken_ext.openai_public ../openAIClient/main.py

pyinstaller openAIClient.spec
