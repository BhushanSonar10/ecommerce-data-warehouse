# Git Workflow Guide

This guide outlines the Git workflow and best practices for the E-Commerce Data Warehouse project.

## 🌟 Repository Setup

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ecommerce-data-warehouse.git
cd ecommerce-data-warehouse

# Set up your Git configuration
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Create your development branch
git checkout -b feature/your-feature-name
```

### Repository Structure

```
ecommerce-data-warehouse/
├── .git/                     # Git repository data
├── .github/                  # GitHub-specific files
│   ├── workflows/            # GitHub Actions workflows
│   ├── ISSUE_TEMPLATE.md     # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── .gitignore               # Git ignore rules
├── README.md                # Main project documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── CHANGELOG.md             # Version history
├── LICENSE                  # Project license
└── [project files...]      # Source code and documentation
```

## 🔄 Branching Strategy

### Branch Types

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/*`**: New features or enhancements
- **`bugfix/*`**: Bug fixes
- **`hotfix/*`**: Critical production fixes
- **`release/*`**: Release preparation

### Branch Naming Convention

```bash
# Feature branches
feature/add-redis-caching
feature/enhance-monitoring-dashboard
feature/implement-data-validation

# Bug fix branches
bugfix/fix-etl-connection-timeout
bugfix/resolve-airflow-dag-failure

# Hotfix branches
hotfix/critical-security-patch
hotfix/database-connection-fix

# Release branches
release/v2.0.0
release/v2.1.0
```

## 🚀 Development Workflow

### 1. Starting New Work

```bash
# Update your local main branch
git checkout main
git pull origin main

# Create a new feature branch
git checkout -b feature/your-feature-name

# Push the branch to remote
git push -u origin feature/your-feature-name
```

### 2. Making Changes

```bash
# Make your changes
# Edit files, add features, fix bugs

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat(etl): add Redis caching for improved performance

- Implement cache manager with TTL support
- Add cache hit rate monitoring
- Update configuration for cache settings

Closes #123"
```

### 3. Keeping Branch Updated

```bash
# Regularly sync with main branch
git checkout main
git pull origin main
git checkout feature/your-feature-name
git rebase main

# Or merge if you prefer
git merge main
```

### 4. Preparing for Review

```bash
# Ensure all tests pass
make test

# Run code quality checks
make lint
make format

# Push your changes
git push origin feature/your-feature-name
```

## 📝 Commit Message Guidelines

### Conventional Commits Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes

### Examples

```bash
# Feature addition
git commit -m "feat(monitoring): add real-time dashboard with business KPIs

- Implement Flask-based monitoring application
- Add charts for revenue and customer metrics
- Include system health monitoring
- Add responsive design for mobile access

Closes #45"

# Bug fix
git commit -m "fix(etl): resolve database connection timeout issue

- Increase connection timeout to 30 seconds
- Add retry logic with exponential backoff
- Improve error logging for connection failures

Fixes #67"

# Documentation update
git commit -m "docs: update deployment guide with cloud instructions

- Add AWS ECS deployment steps
- Include GCP Cloud Run configuration
- Update security configuration examples"

# Breaking change
git commit -m "feat(database)!: migrate to PostgreSQL 15

BREAKING CHANGE: Database schema changes require migration

- Upgrade PostgreSQL from 13 to 15
- Update connection parameters
- Add new indexing strategies
- Migration script provided in sql/migrations/"
```

## 🔍 Pull Request Process

### 1. Creating Pull Request

```bash
# Push your feature branch
git push origin feature/your-feature-name

# Create pull request via GitHub UI or CLI
gh pr create --title "Add Redis caching for ETL performance" \
             --body "This PR implements Redis caching to improve ETL pipeline performance by 60%"
```

### 2. Pull Request Template

```markdown
## Description
Brief description of changes and motivation

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] Performance testing

## Screenshots (if applicable)
Add screenshots to help explain your changes

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### 3. Code Review Process

#### For Authors
- Respond to feedback promptly
- Make requested changes in new commits
- Keep discussions focused and professional
- Test changes thoroughly before requesting re-review

#### For Reviewers
- Review code for functionality, performance, and maintainability
- Check for security issues and best practices
- Verify tests are adequate and passing
- Provide constructive feedback with suggestions

### 4. Merging Pull Requests

```bash
# Squash and merge (preferred for feature branches)
git checkout main
git pull origin main
git merge --squash feature/your-feature-name
git commit -m "feat: add Redis caching for ETL performance"
git push origin main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## 🏷️ Release Management

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Process

```bash
# 1. Create release branch
git checkout main
git pull origin main
git checkout -b release/v2.1.0

# 2. Update version numbers and changelog
# Edit CHANGELOG.md, package.json, etc.

# 3. Commit release changes
git commit -m "chore: prepare release v2.1.0"

# 4. Create pull request for release
gh pr create --title "Release v2.1.0" --body "Release preparation for v2.1.0"

# 5. After PR approval, create tag
git checkout main
git pull origin main
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0

# 6. Create GitHub release
gh release create v2.1.0 --title "v2.1.0" --notes-file RELEASE_NOTES.md
```

## 🔧 Git Configuration

### Recommended Git Configuration

```bash
# Set up Git aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'

# Set up better logging
git config --global alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

# Set up automatic rebase for pulls
git config --global pull.rebase true

# Set up default branch name
git config --global init.defaultBranch main
```

### Git Hooks

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Pre-commit hook to run tests and linting

echo "Running pre-commit checks..."

# Run tests
if ! make test; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

# Run linting
if ! make lint; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

echo "Pre-commit checks passed!"
```

## 🚨 Troubleshooting

### Common Git Issues

#### Merge Conflicts

```bash
# When conflicts occur during merge/rebase
git status  # See conflicted files

# Edit files to resolve conflicts
# Look for <<<<<<< HEAD markers

# After resolving conflicts
git add .
git commit  # For merge
# or
git rebase --continue  # For rebase
```

#### Accidentally Committed to Wrong Branch

```bash
# Move commits to correct branch
git log --oneline  # Note commit hashes
git checkout correct-branch
git cherry-pick <commit-hash>

# Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1  # Remove last commit
```

#### Undo Last Commit

```bash
# Keep changes in working directory
git reset --soft HEAD~1

# Remove changes completely
git reset --hard HEAD~1

# Amend last commit message
git commit --amend -m "New commit message"
```

### Recovery Commands

```bash
# View reflog to find lost commits
git reflog

# Recover lost commit
git checkout <commit-hash>
git checkout -b recovery-branch

# Stash changes temporarily
git stash
git stash pop

# Clean untracked files
git clean -fd
```

## 📊 Git Workflow Metrics

### Tracking Progress

```bash
# View contribution statistics
git shortlog -sn

# View commit activity
git log --since="1 month ago" --oneline

# View branch information
git branch -vv

# View remote information
git remote -v
```

### Code Quality Metrics

```bash
# Lines of code by author
git log --format='%aN' | sort -u | while read name; do echo -en "$name\t"; git log --author="$name" --pretty=tformat: --numstat | awk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf "added lines: %s, removed lines: %s, total lines: %s\n", add, subs, loc }' -; done

# Commit frequency
git log --format="%ai" | cut -d' ' -f1 | sort | uniq -c

# File change frequency
git log --name-only --pretty=format: | sort | uniq -c | sort -rg
```

## 📚 Best Practices

### Do's

- ✅ Write clear, descriptive commit messages
- ✅ Keep commits small and focused
- ✅ Test before committing
- ✅ Use branches for all changes
- ✅ Review your own code before requesting review
- ✅ Keep branches up to date with main
- ✅ Delete merged branches

### Don'ts

- ❌ Commit directly to main branch
- ❌ Force push to shared branches
- ❌ Commit sensitive information
- ❌ Make commits without testing
- ❌ Use vague commit messages
- ❌ Leave branches stale for long periods
- ❌ Ignore merge conflicts

## 🤝 Collaboration Guidelines

### Team Workflow

1. **Daily Sync**: Pull latest changes from main
2. **Feature Work**: Create feature branches for all work
3. **Regular Commits**: Commit frequently with clear messages
4. **Code Review**: All changes go through pull request review
5. **Testing**: Ensure all tests pass before merging
6. **Documentation**: Update docs with code changes

### Communication

- Use pull request descriptions to explain changes
- Reference issues in commit messages
- Discuss major changes before implementation
- Keep team informed of breaking changes
- Use GitHub discussions for design decisions

---

This Git workflow ensures code quality, collaboration efficiency, and project maintainability. Follow these guidelines to contribute effectively to the E-Commerce Data Warehouse project.