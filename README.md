# Let's Build LLM-Powered Apps!

Here are the setup instructions:

## ⚙️ Environment Setup

Before running the application, create a `.env` file in the root directory ((or rename the `starter.env` file to `.env`) with the following environment variables:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PINECONE_API_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_BASE_URL=
NETLIFY_TOKEN=
GMAIL_ACCOUNT=
GITHUB_TOKEN=
```

> ⚠️ Replace each value with your actual API credentials. At a minimum, fill in the `OPENAI_API_KEY`

## 🚀 Running the Scripts

To build and run the Python scripts using Docker, first make sure you've installed [Docker](https://www.docker.com/products/docker-desktop/), and then run these commands in your terminal:

```
docker compose build
docker compose run app
```

To check if everything is working, run:

```
python chatbot_00.py
```

If you get some juicy info about George Washington, you should be good to go!