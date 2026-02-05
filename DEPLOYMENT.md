# Deployment Guide for Render

This guide will help you deploy your AI-powered questionnaire to Render.

## Pre-deployment Checklist

✅ **Files Created:**
- `requirements.txt` - Python dependencies for Render
- `render.yaml` - Render configuration (optional but recommended)
- `start.sh` - Start script for the application
- Updated `config/settings.py` - Production-ready configuration
- Updated `storage/google_sheets.py` - Handle credentials for production

## Step 1: Prepare Your Repository

1. **Commit all changes to git:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push
   ```

2. **Make sure your repository is on GitHub, GitLab, or Bitbucket**

## Step 2: Get Required API Keys

### Google AI API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Save it securely - you'll need it for environment variables

### Google Sheets Credentials (Optional)
If you want to use Google Sheets integration:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Create a Service Account:
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Download the JSON credentials file
   - **Important**: You'll need the entire JSON content as a string for Render

## Step 3: Deploy to Render

### Option A: Using render.yaml (Recommended)
1. Log into [Render](https://render.com)
2. Click "New" → "Blueprint"
3. Connect your repository
4. Render will automatically detect the `render.yaml` file

### Option B: Manual Setup
1. Log into [Render](https://render.com)
2. Click "New" → "Web Service"
3. Connect your repository
4. Configure:
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python Version**: 3.11

## Step 4: Configure Environment Variables

In your Render service dashboard, set these environment variables:

### Required Variables:
- `MODEL_API_KEY` = Your Google AI API key
- `MODEL` = `gemini-1.5-flash` (or your preferred model)

### Optional (for Google Sheets):
- `GOOGLE_SHEET_ID` = Your Google Sheet ID (from the URL)
- `GOOGLE_CREDENTIALS_JSON` = The entire JSON credentials as a string (see below)
- `QUESTION_SOURCE` = `sheets` (if using Google Sheets) or `json` (default)
- `SHEET_NAME` = `Sheet1` (or your sheet name)

### Converting Google Credentials to JSON String:
1. Open your downloaded Google credentials JSON file
2. Copy the entire content
3. Minify it (remove line breaks): you can use online JSON minifiers
4. Paste the minified JSON as the value for `GOOGLE_CREDENTIALS_JSON`

Example minified JSON:
```
{"type":"service_account","project_id":"your-project","private_key_id":"..."}
```

## Step 5: Test Your Deployment

1. Wait for the deployment to complete
2. Visit your Render URL (e.g., `https://your-app-name.onrender.com`)
3. Test the questionnaire functionality
4. If using Google Sheets, test that responses are saved

## Troubleshooting

### Common Issues:

1. **Build Fails**: Check that `requirements.txt` has all dependencies
2. **App Won't Start**: Verify the start command and PORT configuration
3. **Google Sheets Not Working**: 
   - Verify `GOOGLE_CREDENTIALS_JSON` is valid JSON
   - Check that the service account has access to your sheet
   - Ensure Google Sheets API is enabled

### Logs:
- Check Render logs in your service dashboard
- Look for specific error messages about missing environment variables

### Local Testing:
Test your changes locally first:
```bash
# Set environment variables
export MODEL_API_KEY="your_key_here"
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'

# Run the app
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Security Notes

- Never commit API keys or credentials to your repository
- Use Render's environment variables for all sensitive data
- The Google credentials JSON contains private keys - keep it secure
- Consider using Google Sheets with restricted access

## Next Steps

After successful deployment:
1. Set up a custom domain (optional)
2. Monitor your application logs
3. Set up alerts for errors
4. Consider upgrading to a paid plan for better performance

## Support

If you encounter issues:
1. Check Render's documentation: https://render.com/docs
2. Review your application logs in the Render dashboard
3. Verify all environment variables are set correctly