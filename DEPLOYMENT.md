# Deployment Guide - Hindi AI Assistant

## 🚀 Quick Deployment to Vercel

### Prerequisites
- Vercel account (free)
- Google Gemini API key (free from [Google AI Studio](https://makersuite.google.com))
- Git repository

### Step-by-Step Deployment

#### 1. Prepare Your Repository
```bash
# Ensure you're in the project root
cd hindi-ai-assistant

# Verify all files are present
ls -la
# Should see: README.md, vercel.json, backend/, frontend/, requirements.txt
```

#### 2. Install Vercel CLI
```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to your Vercel account
vercel login
```

#### 3. Deploy to Vercel
```bash
# Deploy the project
vercel --prod

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? (Select your account)
# - Link to existing project? No
# - Project name: hindi-ai-assistant (or your preferred name)
# - Directory: ./ (current directory)
# - Override settings? No
```

#### 4. Configure Environment Variables
```bash
# Add your Gemini API key
vercel env add GEMINI_API_KEY

# When prompted:
# - Enter the value: your_actual_gemini_api_key
# - Environment: Production
# - Add to Development and Preview? Yes (recommended)
```

#### 5. Redeploy with Environment Variables
```bash
# Redeploy to apply environment variables
vercel --prod
```

### Your App is Live! 🎉

After deployment, you'll receive a URL like: `https://hindi-ai-assistant-xyz.vercel.app`

## 🔧 Alternative Deployment Options

### Heroku Deployment

#### 1. Create Heroku App
```bash
# Install Heroku CLI
# Create new app
heroku create hindi-ai-assistant-your-name

# Set environment variables
heroku config:set GEMINI_API_KEY=your_api_key_here
```

#### 2. Create Procfile
```bash
echo "web: gunicorn backend.app:app --bind 0.0.0.0:\$PORT" > Procfile
```

#### 3. Deploy
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Railway Deployment

#### 1. Connect Repository
- Go to [Railway.app](https://railway.app)
- Connect your GitHub repository
- Select the hindi-ai-assistant project

#### 2. Configure Environment
- Add `GEMINI_API_KEY` in the Variables section
- Railway will automatically detect Python and deploy

### DigitalOcean App Platform

#### 1. Create App
- Go to DigitalOcean App Platform
- Create new app from GitHub repository

#### 2. Configure Build
```yaml
# .do/app.yaml
name: hindi-ai-assistant
services:
- name: backend
  source_dir: /
  github:
    repo: your-username/hindi-ai-assistant
    branch: main
  run_command: python backend/app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: GEMINI_API_KEY
    value: your_api_key_here
- name: frontend
  source_dir: /frontend
  github:
    repo: your-username/hindi-ai-assistant
    branch: main
  build_command: echo "Static files"
  run_command: echo "Serving static files"
```

## 🔍 Troubleshooting Deployment Issues

### Common Vercel Issues

#### Issue: "Build failed - Python dependencies"
**Solution:**
```bash
# Ensure requirements.txt is in root directory
# Remove any problematic dependencies
pip freeze > requirements.txt

# Check for Windows-specific packages and remove them
# Edit requirements.txt and remove lines like:
# pywin32==306
# winsound==1.0
```

#### Issue: "Function timeout"
**Solution:**
```json
// In vercel.json, increase timeout
{
  "functions": {
    "backend/app.py": {
      "maxDuration": 30
    }
  }
}
```

#### Issue: "Environment variables not working"
**Solution:**
```bash
# Verify environment variables are set
vercel env ls

# If missing, add them:
vercel env add GEMINI_API_KEY production
```

### Common Heroku Issues

#### Issue: "Application error"
**Solution:**
```bash
# Check logs
heroku logs --tail

# Common fixes:
# 1. Ensure Procfile is correct
echo "web: gunicorn backend.app:app --bind 0.0.0.0:\$PORT" > Procfile

# 2. Add runtime.txt
echo "python-3.9.16" > runtime.txt

# 3. Check environment variables
heroku config
```

#### Issue: "Slug size too large"
**Solution:**
```bash
# Add .slugignore file
echo "venv/" > .slugignore
echo "*.pyc" >> .slugignore
echo "__pycache__/" >> .slugignore
echo ".git/" >> .slugignore
```

## 📊 Post-Deployment Checklist

### ✅ Functionality Tests

1. **Frontend Loading**
   - [ ] Website loads without errors
   - [ ] Camera permission request appears
   - [ ] Microphone button is visible

2. **Backend API**
   - [ ] `/api/status` returns service status
   - [ ] Audio upload works
   - [ ] Speech transcription works
   - [ ] Response generation works
   - [ ] Text-to-speech works
   - [ ] Face detection works

3. **Error Handling**
   - [ ] Graceful error messages appear
   - [ ] Fallback responses work when APIs fail
   - [ ] Network errors are handled properly

### 🔧 Performance Optimization

1. **Enable Compression**
```javascript
// Add to vercel.json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

2. **Monitor Performance**
- Set up Vercel Analytics
- Monitor function execution times
- Check error rates in dashboard

### 🔒 Security Configuration

1. **HTTPS Enforcement**
   - Vercel automatically provides HTTPS
   - Ensure all API calls use HTTPS URLs

2. **Environment Variables**
   - Never commit API keys to repository
   - Use Vercel's environment variable system
   - Rotate API keys regularly

## 📈 Scaling Considerations

### Traffic Growth
- **Vercel Pro**: For higher limits and better performance
- **CDN**: Static assets automatically cached
- **Database**: Consider adding Redis for caching

### Cost Optimization
- **Function Duration**: Optimize code to reduce execution time
- **Memory Usage**: Monitor and optimize memory consumption
- **API Calls**: Implement caching to reduce external API calls

## 🆘 Support Resources

### Documentation
- [Vercel Documentation](https://vercel.com/docs)
- [Heroku Python Guide](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Railway Documentation](https://docs.railway.app)

### Community Support
- [Vercel Discord](https://vercel.com/discord)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/vercel)
- Project GitHub Issues

---

**Your Hindi AI Assistant is now ready for the world! 🌍**