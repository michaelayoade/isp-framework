#!/bin/bash
# Setup Git hooks and automation for ISP Framework

set -e

echo "🔧 Setting up Git hooks and automation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a Git repository${NC}"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}📦 Installing pre-commit...${NC}"
    pip install pre-commit
fi

# Install pre-commit hooks
echo -e "${BLUE}🪝 Installing pre-commit hooks...${NC}"
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push

# Create commit message template
echo -e "${BLUE}📝 Setting up commit message template...${NC}"
cat > .gitmessage << 'EOF'
# <type>[optional scope]: <description>
#
# [optional body]
#
# [optional footer(s)]
#
# Types:
# feat:     New feature
# fix:      Bug fix
# docs:     Documentation changes
# style:    Code style changes (formatting, etc.)
# refactor: Code refactoring
# test:     Adding or updating tests
# chore:    Maintenance tasks
# perf:     Performance improvements
# ci:       CI/CD changes
#
# Examples:
# feat(customers): add bulk customer import functionality
# fix(billing): resolve invoice calculation rounding error
# docs(api): update authentication endpoint documentation
EOF

git config commit.template .gitmessage

# Set up conventional commit validation
echo -e "${BLUE}✅ Setting up commit message validation...${NC}"
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/sh
# Conventional commit message validation

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci)(\(.+\))?: .{1,50}'

error_msg="❌ Invalid commit message format!

Your commit message should follow the Conventional Commits format:
<type>[optional scope]: <description>

Examples:
✅ feat(customers): add bulk customer import functionality
✅ fix(billing): resolve invoice calculation rounding error
✅ docs(api): update authentication endpoint documentation

Types: feat, fix, docs, style, refactor, test, chore, perf, ci"

if ! grep -qE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
EOF

chmod +x .git/hooks/commit-msg

# Set up branch naming validation
echo -e "${BLUE}🌿 Setting up branch naming validation...${NC}"
cat > .git/hooks/pre-push << 'EOF'
#!/bin/sh
# Branch naming validation

protected_branch='main'
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

# Allow pushes to main from CI/CD
if [ "$current_branch" = "$protected_branch" ] && [ -z "$CI" ]; then
    echo "❌ Direct pushes to main branch are not allowed!"
    echo "Please create a feature branch and submit a pull request."
    exit 1
fi

# Validate branch naming convention
branch_regex='^(feat|fix|hotfix|chore)\/[a-z0-9-]+$'

if [ "$current_branch" != "main" ] && [ "$current_branch" != "develop" ]; then
    if ! echo "$current_branch" | grep -qE "$branch_regex"; then
        echo "❌ Invalid branch name: $current_branch"
        echo ""
        echo "Branch names should follow the pattern:"
        echo "  feat/feature-name"
        echo "  fix/bug-description"
        echo "  hotfix/critical-fix"
        echo "  chore/maintenance-task"
        echo ""
        echo "Examples:"
        echo "  feat/customer-portal-redesign"
        echo "  fix/billing-calculation-error"
        echo "  hotfix/security-vulnerability-patch"
        exit 1
    fi
fi
EOF

chmod +x .git/hooks/pre-push

# Configure Git settings
echo -e "${BLUE}⚙️  Configuring Git settings...${NC}"
git config pull.rebase true
git config branch.autosetupmerge always
git config branch.autosetuprebase always
git config core.autocrlf input
git config init.defaultBranch main

# Set up aliases for common operations
echo -e "${BLUE}🔗 Setting up Git aliases...${NC}"
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
git config alias.st status
git config alias.unstage 'reset HEAD --'
git config alias.last 'log -1 HEAD'
git config alias.visual '!gitk'
git config alias.tree 'log --graph --pretty=format:"%C(yellow)%h%Creset -%C(red)%d%Creset %s %C(green)(%cr) %C(bold blue)<%an>%Creset" --abbrev-commit --all'
git config alias.cleanup 'branch --merged | grep -v "\*\|main\|develop" | xargs -n 1 git branch -d'

# Create useful Git scripts
echo -e "${BLUE}📜 Creating Git utility scripts...${NC}"

# Create new feature branch script
cat > scripts/new-feature.sh << 'EOF'
#!/bin/bash
# Create a new feature branch

if [ -z "$1" ]; then
    echo "Usage: ./scripts/new-feature.sh <feature-name>"
    echo "Example: ./scripts/new-feature.sh customer-portal-redesign"
    exit 1
fi

FEATURE_NAME="$1"
BRANCH_NAME="feat/$FEATURE_NAME"

echo "🌿 Creating new feature branch: $BRANCH_NAME"

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create and checkout new feature branch
git checkout -b "$BRANCH_NAME"

echo "✅ Feature branch '$BRANCH_NAME' created and checked out"
echo "💡 Start developing your feature!"
EOF

chmod +x scripts/new-feature.sh

# Create release preparation script
cat > scripts/prepare-release.sh << 'EOF'
#!/bin/bash
# Prepare a new release

if [ -z "$1" ]; then
    echo "Usage: ./scripts/prepare-release.sh <version>"
    echo "Example: ./scripts/prepare-release.sh 1.2.0"
    exit 1
fi

VERSION="$1"
RELEASE_BRANCH="release/v$VERSION"

echo "🚀 Preparing release v$VERSION"

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid version format. Use X.Y.Z format."
    exit 1
fi

# Ensure we're on develop and up to date
git checkout develop
git pull origin develop

# Create release branch
git checkout -b "$RELEASE_BRANCH"

# Update version files
echo "$VERSION" > backend/VERSION
cd frontend && npm version "$VERSION" --no-git-tag-version && cd ..

# Generate changelog
echo "📝 Generating changelog..."
npx conventional-changelog -p angular -i CHANGELOG.md -s

# Commit version updates
git add .
git commit -m "chore(release): prepare v$VERSION"

echo "✅ Release branch '$RELEASE_BRANCH' prepared"
echo "💡 Review changes, then merge to main and tag the release"
EOF

chmod +x scripts/prepare-release.sh

# Create cleanup script
cat > scripts/cleanup-branches.sh << 'EOF'
#!/bin/bash
# Clean up merged branches

echo "🧹 Cleaning up merged branches..."

# Remove local branches that have been merged
git branch --merged | grep -v "\*\|main\|develop" | xargs -n 1 git branch -d

# Remove remote tracking branches that no longer exist
git remote prune origin

echo "✅ Branch cleanup completed"
EOF

chmod +x scripts/cleanup-branches.sh

echo -e "${GREEN}✅ Git hooks and automation setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Summary of what was configured:${NC}"
echo "  🪝 Pre-commit hooks installed"
echo "  📝 Commit message template and validation"
echo "  🌿 Branch naming validation"
echo "  ⚙️  Git configuration optimized"
echo "  🔗 Useful Git aliases added"
echo "  📜 Utility scripts created"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "  1. Run 'pre-commit run --all-files' to check existing code"
echo "  2. Use './scripts/new-feature.sh <name>' to create feature branches"
echo "  3. Follow conventional commit format for all commits"
echo "  4. Submit pull requests for code review"
echo ""
echo -e "${GREEN}🎉 Happy coding!${NC}"
