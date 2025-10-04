# Contributing to AgniRakshak

Thank you for your interest in contributing to AgniRakshak! We welcome contributions from the community to help improve wildfire prediction and threat assessment capabilities.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Issue Reporting](#issue-reporting)
7. [Documentation](#documentation)

## Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of machine learning concepts
- Understanding of web development (HTML, CSS, JavaScript)

### Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/agnirakshak.git
   cd agnirakshak
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Contributing Guidelines

### Types of Contributions

We welcome the following types of contributions:

1. **Bug fixes** - Fix issues in existing code
2. **Feature enhancements** - Improve existing features
3. **New features** - Add new wildfire prediction capabilities  
4. **Documentation** - Improve README, code comments, or guides
5. **Testing** - Add or improve test coverage
6. **Performance** - Optimize algorithms or system performance

### Areas for Contribution

#### Machine Learning & Data Science
- Improve prediction model accuracy
- Add new data sources (satellite imagery, IoT sensors)
- Enhance feature engineering
- Implement ensemble methods
- Add model interpretability features

#### Frontend Development
- Improve user interface design
- Add data visualization components
- Enhance mobile responsiveness
- Implement real-time updates
- Add accessibility features

#### Backend Development
- Optimize API performance
- Add new endpoints
- Improve error handling
- Enhance logging and monitoring
- Add caching mechanisms

#### Data Processing
- Add new weather data sources
- Improve data cleaning pipelines
- Add real-time data streaming
- Enhance terrain analysis
- Add vegetation index calculations

### Coding Standards

#### Python Code
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable and function names

Example:
```python
def calculate_fire_behavior_index(
    temperature: float,
    humidity: float,
    wind_speed: float,
    fuel_moisture: float
) -> float:
    """
    Calculate the fire behavior index based on weather conditions.
    
    Args:
        temperature: Air temperature in Celsius
        humidity: Relative humidity as percentage
        wind_speed: Wind speed in km/h
        fuel_moisture: Fuel moisture content as percentage
        
    Returns:
        Fire behavior index (0-100 scale)
    """
    # Implementation here
    pass
```

#### JavaScript Code
- Use ES6+ features
- Follow Airbnb JavaScript style guide
- Use meaningful variable names
- Add JSDoc comments for functions
- Use async/await for asynchronous operations

#### HTML/CSS
- Use semantic HTML5 elements
- Follow BEM methodology for CSS classes
- Ensure mobile-first responsive design
- Add appropriate ARIA labels for accessibility
- Optimize for performance

### Testing

#### Unit Tests
- Write tests for all new functions
- Maintain >80% code coverage
- Use pytest for Python tests
- Mock external API calls

#### Integration Tests
- Test API endpoints
- Test frontend-backend integration
- Test model prediction pipelines

#### Manual Testing
- Test in multiple browsers
- Verify mobile responsiveness
- Test with different API key configurations

### Documentation

- Update README.md for new features
- Add inline code comments
- Update API documentation
- Include usage examples
- Document configuration options

## Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, tested code
   - Follow coding standards
   - Update documentation

3. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black .
   flake8
   
   # Type checking
   mypy .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new fire behavior prediction model"
   ```

### Commit Message Format

Use conventional commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### Pull Request Template

When submitting a PR, please include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer review required
3. Address feedback promptly
4. Squash commits before merge

## Issue Reporting

### Bug Reports

Please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages/stack traces
- Screenshots if applicable

### Feature Requests

Please include:
- Clear description of the feature
- Use case and benefits
- Proposed implementation approach
- Potential challenges or considerations

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation needs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority-high` - High priority issue

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - Feature development
- `hotfix/*` - Emergency fixes
- `release/*` - Release preparation

### Local Development

1. **Start development server**
   ```bash
   python app.py
   ```

2. **Run in development mode**
   ```bash
   export FLASK_ENV=development
   flask run --debug
   ```

3. **Test prediction endpoints**
   ```bash
   curl -X POST http://localhost:5000/predict \
     -H "Content-Type: application/json" \
     -d '{"lat": 37.7749, "lon": -122.4194}'
   ```

## Getting Help

- Check existing issues and documentation first
- Join our community discussions
- Contact maintainers via GitHub issues
- Read the full documentation in the wiki

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Annual contributor acknowledgment

Thank you for helping make AgniRakshak better! 🔥🛡️