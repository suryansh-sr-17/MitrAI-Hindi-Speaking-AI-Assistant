# Contributing to Hindi AI Assistant 🤝

We love your input! We want to make contributing to Hindi AI Assistant as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### 📋 Pull Request Process

1. **Fork the Repository**
   ```bash
   git clone https://github.com/suryansh-sr-17/MitrAI-Hindi-Speaking-AI-Assistant.git
   cd MitrAI-Hindi-Speaking-AI-Assistant
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Set Up Development Environment**
   ```bash
   python setup.py
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

4. **Make Your Changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation as needed

5. **Test Your Changes**
   ```bash
   # Run backend tests
   pytest backend/tests/
   
   # Test frontend functionality
   python backend/app.py
   # Open frontend/index.html in browser
   ```

6. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/amazing-feature
   ```

## 🎯 Code Style Guidelines

### Python (Backend)
- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Maximum line length: 88 characters (Black formatter)

```python
def transcribe_audio(audio_path: str, language: str = "hi") -> dict:
    """
    Transcribe audio file to text using speech recognition.
    
    Args:
        audio_path: Path to the audio file
        language: Language code (default: "hi" for Hindi)
        
    Returns:
        Dictionary containing transcription result and metadata
    """
    # Implementation here
    pass
```

### JavaScript (Frontend)
- Use ES6+ features
- Follow consistent naming conventions
- Add JSDoc comments for functions
- Use meaningful variable names

```javascript
/**
 * Process audio input and send to backend for transcription
 * @param {Blob} audioBlob - The recorded audio data
 * @returns {Promise<Object>} Transcription result
 */
async function processAudioInput(audioBlob) {
    // Implementation here
}
```

### HTML/CSS
- Use semantic HTML5 elements
- Follow accessibility guidelines (WCAG 2.1 AA)
- Use CSS custom properties for theming
- Mobile-first responsive design

## 🐛 Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/suryansh-sr-17/MitrAI-Hindi-Speaking-AI-Assistant/issues/new).

### Great Bug Reports Include:

- **Summary**: Quick summary of the issue
- **Steps to Reproduce**: Detailed steps to reproduce the behavior
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, browser, Python version, etc.
- **Screenshots**: If applicable
- **Additional Context**: Any other relevant information

**Bug Report Template:**
```markdown
## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear description of what you expected to happen.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Environment
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Browser: [e.g. Chrome 96, Firefox 95, Safari 15]
- Python Version: [e.g. 3.9.7]
- Node Version: [e.g. 16.13.0] (if applicable)

## Additional Context
Add any other context about the problem here.
```

## 💡 Feature Requests

We welcome feature requests! Please provide:

- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: What alternatives have you considered?
- **Additional Context**: Screenshots, mockups, etc.

## 🧪 Testing Guidelines

### Backend Testing
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest backend/tests/test_speech_to_text.py
```

### Frontend Testing
- Test in multiple browsers (Chrome, Firefox, Safari, Edge)
- Test responsive design on different screen sizes
- Verify accessibility with screen readers
- Test with different audio formats

### Integration Testing
- Test complete user workflows
- Verify API endpoints work correctly
- Test error handling and fallback mechanisms

## 📝 Documentation

### Code Documentation
- Add docstrings to all Python functions and classes
- Use JSDoc comments for JavaScript functions
- Include type hints in Python code
- Document complex algorithms and business logic

### User Documentation
- Update README.md for new features
- Add examples for new API endpoints
- Include screenshots for UI changes
- Update deployment guides if needed

## 🌍 Internationalization

### Adding New Languages
1. **Backend**: Add language support in STT/TTS services
2. **Frontend**: Add language strings and UI translations
3. **Testing**: Test with native speakers
4. **Documentation**: Update language support documentation

### Hindi Language Improvements
- Improve speech recognition accuracy
- Add regional dialect support
- Enhance response generation quality
- Better handling of code-mixed text (Hindi-English)

## 🔒 Security Guidelines

### Reporting Security Issues
- **DO NOT** open public issues for security vulnerabilities
- Email security issues to: security@yourproject.com
- Include detailed steps to reproduce
- Allow time for fix before public disclosure

### Security Best Practices
- Never commit API keys or secrets
- Validate all user inputs
- Use HTTPS in production
- Follow OWASP guidelines
- Regular dependency updates

## 📦 Release Process

### Version Numbering
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag release in Git
- [ ] Deploy to production

## 🎖️ Recognition

### Contributors
All contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

### Types of Contributions
- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation**
- 🧪 **Testing**
- 🎨 **Design/UI**
- 🌍 **Translations**
- 🔧 **Infrastructure**

## 📞 Getting Help

### Community Support
- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Discord**: Real-time chat with the community
- **Stack Overflow**: Tag your questions with `hindi-ai-assistant`

### Development Setup Help
If you're having trouble setting up the development environment:

1. Check the [README.md](README.md) setup instructions
2. Look at existing [GitHub Issues](https://github.com/suryansh-sr-17/MitrAI-Hindi-Speaking-AI-Assistant/issues)
3. Ask in [GitHub Discussions](https://github.com/suryansh-sr-17/MitrAI-Hindi-Speaking-AI-Assistant/discussions)

## 📋 Code of Conduct

### Our Pledge
We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience, nationality
- Personal appearance, race, religion
- Sexual identity and orientation

### Our Standards
**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement
Project maintainers are responsible for clarifying standards and will take appropriate action in response to unacceptable behavior.

## 🙏 Thank You!

Your contributions make this project better for everyone. Whether you're fixing bugs, adding features, improving documentation, or helping other users, every contribution is valuable and appreciated!

---

**Happy Contributing! 🚀**