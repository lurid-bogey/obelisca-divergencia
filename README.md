# Obelisca Divergencia da Silva 

Obelisca Divergencia is yet another Azure OpenAI client.

### But why?

Well... Azure OpenAI changed their API for the new reasoning models. The client that 
I was previously using didn't pick up these changes, so I was left with no access
to the new `o1` and `o3` models. I raised an issue with them and waited for a month, but 
they were obviously busy and the changed API was not a priority for them.

So, I just decided to write my own client. 🙈

This project is for my own education and entertainment. It is specifically geared to 
the Azure flavour of the `o1` and `o3` models. Of course, you have to bring your 
own API key.

### API keys
You have to export your own API keys to the environment:

```
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
```

### OpenAI vs. Azure OpenAI
Obelisca Divergencia should work with both of them, but I am only using and testing 
the Azure deployment.

# Features

* Conversations are persisted in a SQLite database, so past conversations are not lost.
* You can attach files to the conversation.
* PDF and Word attachments should be supported, but are not thoroughly tested.
* So far I'm only testing on Windows, but this being a Python and Pyside6 project,
 it shouldn't be difficult to run it on Linux or MacOS.
* Precompiled Windows binary is available

# Installation

### Clone the repo
```
mkdir obelisca
cd obelisca
git clone git@github.com:lurid-bogey/obelisca-divergencia.git .
cd openAIClient
```

### Run the project
```
python -m venv env
env\Scripts\activate.bat
pip install -r requirements.txt
python -m openAIClient
```
