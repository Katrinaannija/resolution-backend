# API Setup Guide for Resolution Backend

## Overview

Your Resolution Backend system requires API keys to function properly. This guide will walk you through setting up each API connection.

## Required APIs

### 1. OpenAI API (REQUIRED)

**What it does**: Powers the AI language models that analyze legal documents, generate insights, and create recommendations.

**How to get your API key**:

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your OpenAI account
3. Click "Create new secret key"
4. Give it a name like "Resolution Backend"
5. Copy the key (it starts with `sk-proj-...` or `sk-...`)
6. **Important**: Save it somewhere safe - you can't see it again!

**Cost**: OpenAI charges per token used. Typical costs:
- GPT-4o: ~$2.50 per 1M input tokens, ~$10 per 1M output tokens
- GPT-4-turbo: ~$10 per 1M input tokens, ~$30 per 1M output tokens
- GPT-3.5-turbo: ~$0.50 per 1M input tokens, ~$1.50 per 1M output tokens

**Recommended starting model**: `gpt-4o` (good balance of performance and cost)

### 2. LangSmith API (OPTIONAL BUT RECOMMENDED)

**What it does**:
- Provides observability (see what your AI is doing)
- Manages prompts centrally
- Helps debug issues
- Tracks performance

**How to get your API key**:

1. Go to [LangSmith](https://smith.langchain.com/)
2. Sign up with your email or GitHub account (free tier available)
3. Once logged in, go to **Settings** → **API Keys**
4. Click "Create API Key"
5. Name it "Resolution Backend"
6. Copy the key (starts with `lsv2_pt_...` or similar)

**Cost**: Free tier includes:
- 5,000 traces per month
- 1 seat
- 14 days of data retention

Paid plans start at $39/month for more traces and features.

## Configuration Steps

### Step 1: Add your API keys to the `.env` file

Open the `.env` file in the project root and fill in your keys:

```bash
# Required
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional but recommended
LANGSMITH_API_KEY=lsv2_pt_your-actual-key-here
LANGSMITH_PROJECT=resolution-ai
LANGSMITH_TRACING=true
```

### Step 2: Choose your model (optional)

By default, the system uses the model specified in each prompt. You can override this globally:

```bash
# Use GPT-4o (recommended)
GLOBAL_MODEL=gpt-4o

# Or use GPT-4 Turbo for better quality (more expensive)
# GLOBAL_MODEL=gpt-4-turbo

# Or use GPT-3.5 Turbo for faster/cheaper (lower quality)
# GLOBAL_MODEL=gpt-3.5-turbo
```

### Step 3: Test your configuration

Run this command to test your setup:

```bash
uv run python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenAI Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING'); print('LangSmith Key:', 'SET' if os.getenv('LANGSMITH_API_KEY') else 'MISSING')"
```

You should see:
```
OpenAI Key: SET
LangSmith Key: SET (or MISSING if you skipped it)
```

### Step 4: Start the development server

```bash
uv run langgraph dev
```

The server should start on `http://localhost:2024` without errors.

## Security Best Practices

### ⚠️ IMPORTANT: Never commit your `.env` file to git!

The `.env` file is already in `.gitignore`, but double-check:

```bash
# Verify .env is ignored
git check-ignore .env
```

If it's not ignored, add it:

```bash
echo ".env" >> .gitignore
```

### Protect your API keys

- **Never share** your API keys publicly
- **Never commit** them to version control
- **Rotate keys** if they're exposed
- Use **separate keys** for development and production
- Consider using **environment variables** in production (not .env files)

## Troubleshooting

### Error: "OpenAI API key not found"

**Solution**: Make sure you've set `OPENAI_API_KEY` in `.env` and it's a valid key.

```bash
# Test if the key is loaded
uv run python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Error: "Rate limit exceeded"

**Solution**: You've hit OpenAI's rate limit. Wait a moment or:
- Upgrade your OpenAI account tier
- Add usage limits in OpenAI dashboard
- Reduce concurrent requests

### Error: "Invalid API key"

**Solution**:
- Check for extra spaces or quotes in your `.env` file
- Regenerate the API key on OpenAI platform
- Make sure you copied the entire key

### LangSmith not showing traces

**Solution**:
- Verify `LANGSMITH_TRACING=true` is set
- Check your API key is correct
- Make sure you have a project created in LangSmith
- Traces can take a few seconds to appear

## Alternative: Use Anthropic Claude API

If you prefer to use Anthropic's Claude models instead of OpenAI:

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Install the Anthropic SDK:
   ```bash
   uv add langchain-anthropic
   ```
3. Update your code to use `ChatAnthropic` instead of `ChatOpenAI`

However, the current codebase is configured for OpenAI, so you'd need to modify the LLM initialization code.

## Cost Management Tips

1. **Start with GPT-3.5-turbo** for testing (cheapest)
2. **Set usage limits** in OpenAI dashboard
3. **Monitor usage** in OpenAI dashboard → Usage
4. **Use LangSmith** to see which operations use the most tokens
5. **Test with small documents** first before processing large batches

## Need Help?

- **OpenAI Documentation**: https://platform.openai.com/docs
- **LangSmith Documentation**: https://docs.smith.langchain.com/
- **LangChain Documentation**: https://python.langchain.com/docs/

---

**Last Updated**: 2026-01-15
