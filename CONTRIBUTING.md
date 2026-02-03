# Contributing to E-Commerce Data Warehouse

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** when creating new issues
3. **Provide detailed information** including:
   - Steps to reproduce the problem
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
   - Error messages and logs

### Submitting Changes

1. **Fork the repository** and create a new branch
2. **Make your changes** following the coding standards
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## 🔧 Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

### Local Development

```bash
# Clone your fork
git clone https://github.com/yourusername/ecommerce-data-warehouse.git
cd ecommerce-data-warehouse

# Create a new branch
git checkout -b feature/your-feature-name

# Start development environment
docker-compose up --build

# Make your changes
# Test your changes
# Commit and push
```

## 📝 Coding Standards

### Python Code Style

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Write **docstrings** for functions and classes
- Keep functions **small and focused**
- Use **meaningful variable names**

### SQL Style

- Use **uppercase** for SQL keywords
- Use **snake_case** for table and column names
- **Indent** subqueries and complex statements
- Add **comments** for complex logic

### Docker Best Practices

- Use **multi-stage builds** when appropriate
- **Minimize layer count** and image size
- Use **specific version tags** for base images
- Add **health checks** for services

## 🧪 Testing Guidelines

### Data Quality Tests

- Add tests for new data transformations
- Verify data integrity after changes
- Test edge cases and error conditions
- Validate business logic implementations

### Integration Tests

- Test Docker container interactions
- Verify database connections and queries
- Test Airflow DAG functionality
- Validate monitoring dashboard features

## 📚 Documentation

### Code Documentation

- Add docstrings to all functions and classes
- Include parameter and return type information
- Provide usage examples for complex functions
- Document any assumptions or limitations

### Project Documentation

- Update README.md for new features
- Add or update architecture diagrams
- Document configuration changes
- Update API documentation if applicable

## 🚀 Pull Request Process

1. **Update documentation** for any new features
2. **Add or update tests** for your changes
3. **Ensure all tests pass** locally
4. **Update the changelog** if applicable
5. **Request review** from maintainers

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🏷️ Commit Message Guidelines

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(etl): add Redis caching for improved performance

- Implement cache manager with TTL support
- Add cache hit rate monitoring
- Update configuration for cache settings

Closes #123
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**
   - Operating system
   - Docker version
   - Python version

2. **Steps to reproduce**
   - Detailed step-by-step instructions
   - Sample data if applicable
   - Configuration settings

3. **Expected behavior**
   - What should happen

4. **Actual behavior**
   - What actually happens
   - Error messages
   - Log output

## 💡 Feature Requests

When requesting features:

1. **Describe the problem** you're trying to solve
2. **Explain the proposed solution** in detail
3. **Consider alternatives** you've thought about
4. **Provide use cases** and examples
5. **Discuss implementation** if you have ideas

## 📋 Code Review Process

### For Contributors

- Be responsive to feedback
- Make requested changes promptly
- Ask questions if feedback is unclear
- Test changes thoroughly before requesting re-review

### For Reviewers

- Be constructive and helpful
- Focus on code quality and maintainability
- Consider performance and security implications
- Provide specific, actionable feedback

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority

- Performance optimizations
- Additional data quality checks
- Enhanced error handling
- Documentation improvements

### Medium Priority

- New analytics queries
- Dashboard enhancements
- Additional data sources
- Testing improvements

### Future Enhancements

- Streaming data integration
- Machine learning features
- Cloud deployment guides
- Advanced monitoring features

## 📞 Getting Help

If you need help:

1. **Check the documentation** first
2. **Search existing issues** for similar problems
3. **Create a new issue** with detailed information
4. **Join discussions** in existing issues

## 🙏 Recognition

Contributors will be recognized in:

- README.md acknowledgments
- Release notes for significant contributions
- Project documentation

Thank you for contributing to make this project better! 🚀