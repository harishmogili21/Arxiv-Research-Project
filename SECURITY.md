# Security Guidelines

## 🔒 API Key Management

### ✅ What's Protected
- All API keys are stored in `.env` files (ignored by git)
- Configuration files use environment variable references
- No hardcoded secrets in the codebase
- Example files show placeholder values only

### 🚨 Before Using
1. **Copy environment templates:**
   ```bash
   cp arxiv-mcp-server-clean/.env.example arxiv-mcp-server-clean/.env
   cp arxiv-chainlit-app/.env.example arxiv-chainlit-app/.env
   ```

2. **Add your actual API keys:**
   ```bash
   # In .env files, replace placeholders with real values
   MISTRAL_API_KEY=your_actual_api_key_here
   ```

3. **Verify .env files are ignored:**
   ```bash
   git status  # Should not show .env files
   ```

## 🛡️ Security Checklist

### Environment Variables
- [ ] `.env` files are in `.gitignore`
- [ ] No API keys in committed code
- [ ] Environment variables used in all configurations
- [ ] `.env.example` files provide templates

### Code Security
- [ ] No hardcoded credentials
- [ ] Proper error handling for API failures
- [ ] Input validation for user queries
- [ ] Rate limiting considerations

### Deployment Security
- [ ] Use environment variables in production
- [ ] Secure API key storage (e.g., secrets manager)
- [ ] HTTPS for all external API calls
- [ ] Regular API key rotation

## 🔑 Getting API Keys

### Mistral AI
1. Visit [Mistral Console](https://console.mistral.ai/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Copy and store securely in your `.env` file

### Best Practices
- Never share API keys in chat, email, or public forums
- Use different keys for development and production
- Monitor API usage regularly
- Revoke unused or compromised keys immediately

## 🚨 If You Accidentally Commit Secrets

1. **Immediately revoke the exposed API key**
2. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch path/to/file' \
   --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push to update remote:**
   ```bash
   git push --force --all
   ```
4. **Generate new API keys**
5. **Update your `.env` files**

## 📞 Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not** create a public issue
2. Email the maintainer directly
3. Include detailed information about the vulnerability
4. Allow time for the issue to be addressed before disclosure

---

*Security is everyone's responsibility. When in doubt, ask!*