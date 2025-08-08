# Contributing to Flokie

Thank you for your interest in contributing to Flokie! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Code samples** or error messages if applicable

### 💡 Suggesting Features

Feature suggestions are welcome! Please:

- **Check existing feature requests** to avoid duplicates
- **Provide clear use cases** for the feature
- **Explain the expected behavior** in detail
- **Consider the impact** on existing functionality

### 🔧 Code Contributions

#### Development Setup

1. **Fork the repository**
```bash
git clone https://github.com/yourusername/flokie.git
cd flokie
```

2. **Set up development environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
make install-dev
```

3. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

#### Code Standards

- **Follow PEP 8** style guidelines
- **Use type hints** where appropriate
- **Write docstrings** for all functions and classes
- **Add tests** for new functionality
- **Update documentation** as needed

#### Testing

Before submitting your changes:

```bash
# Run all tests
make test

# Check code coverage
make test-coverage

# Run code quality checks
make lint
make format

# Run security checks
make security-check
```

#### Commit Guidelines

Use conventional commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `style:` for formatting changes
- `chore:` for maintenance tasks

Example:
```
feat: add user profile image upload functionality

- Add image upload endpoint
- Implement image validation and resizing
- Add tests for image processing
- Update API documentation
```

#### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update the changelog** if applicable
5. **Submit the pull request** with a clear description

## 📋 Development Guidelines

### Code Organization

- **Controllers**: Handle HTTP requests and responses
- **Services**: Contain business logic
- **Models**: Define database schemas
- **Schemas**: Handle data validation
- **Utils**: Provide utility functions

### Testing Strategy

- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **API tests**: Test complete request/response cycles
- **Performance tests**: Test system performance

### Documentation

- **API documentation**: Update Swagger/OpenAPI specs
- **Code documentation**: Add docstrings and comments
- **User guides**: Update relevant documentation files
- **Examples**: Provide working code examples

## 🏷️ Issue Labels

We use the following labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested
- `wontfix`: This will not be worked on

## 🎯 Development Priorities

Current focus areas:

1. **Security improvements**
2. **Performance optimizations**
3. **Documentation enhancements**
4. **Test coverage improvements**
5. **Developer experience**

## 📞 Getting Help

If you need help with contributing:

- **GitHub Discussions**: Ask questions and discuss ideas
- **GitHub Issues**: Report bugs or request features
- **Email**: Contact the maintainers directly

## 🙏 Recognition

Contributors will be recognized in:

- **README.md**: Listed in the contributors section
- **CHANGELOG.md**: Mentioned in release notes
- **GitHub**: Contributor statistics and graphs

## 📄 License

By contributing to Flokie, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Flokie! 🚀
