#!/bin/bash
# Setup branch protection rules for ISP Framework
# Requires GitHub CLI (gh) to be installed and authenticated

set -e

echo "🛡️ Setting up branch protection rules..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

# Get repository information
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo -e "${BLUE}📦 Repository: $REPO${NC}"

# Protect main branch
echo -e "${BLUE}🛡️ Setting up protection for main branch...${NC}"
gh api repos/$REPO/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci","tests","security-scan","code-quality-audit"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"require_last_push_approval":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field block_creations=false \
  --field required_conversation_resolution=true \
  --field lock_branch=false \
  --field allow_fork_syncing=true

# Protect develop branch (if it exists)
if git show-ref --verify --quiet refs/remotes/origin/develop; then
    echo -e "${BLUE}🛡️ Setting up protection for develop branch...${NC}"
    gh api repos/$REPO/branches/develop/protection \
      --method PUT \
      --field required_status_checks='{"strict":true,"contexts":["ci","tests"]}' \
      --field enforce_admins=false \
      --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
      --field restrictions=null \
      --field allow_force_pushes=false \
      --field allow_deletions=false \
      --field required_conversation_resolution=true
fi

# Set up repository settings
echo -e "${BLUE}⚙️ Configuring repository settings...${NC}"

# Enable vulnerability alerts
gh api repos/$REPO \
  --method PATCH \
  --field has_vulnerability_alerts=true

# Configure merge settings
gh api repos/$REPO \
  --method PATCH \
  --field allow_merge_commit=false \
  --field allow_squash_merge=true \
  --field allow_rebase_merge=false \
  --field delete_branch_on_merge=true \
  --field allow_auto_merge=true

# Set up issue and PR templates
echo -e "${BLUE}📝 Repository templates already configured${NC}"

# Configure security settings
echo -e "${BLUE}🔒 Enabling security features...${NC}"

# Enable Dependabot alerts
gh api repos/$REPO/vulnerability-alerts \
  --method PUT

# Enable Dependabot security updates
gh api repos/$REPO/automated-security-fixes \
  --method PUT

# Set up branch protection rules summary
echo -e "${GREEN}✅ Branch protection setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Protection rules applied:${NC}"
echo "  🛡️ Main branch:"
echo "    • Require pull request reviews (1 approver)"
echo "    • Require status checks to pass"
echo "    • Require branches to be up to date"
echo "    • Require conversation resolution"
echo "    • Dismiss stale reviews"
echo "    • Require code owner reviews"
echo "    • No force pushes allowed"
echo "    • No deletions allowed"
echo ""
echo "  🛡️ Repository settings:"
echo "    • Squash merge only (no merge commits)"
echo "    • Auto-delete branches after merge"
echo "    • Vulnerability alerts enabled"
echo "    • Dependabot security updates enabled"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "  1. Add team members as code owners in CODEOWNERS file"
echo "  2. Configure required status checks in branch protection"
echo "  3. Set up team permissions for the repository"
echo ""
echo -e "${GREEN}🎉 Repository is now secure and ready for collaboration!${NC}"
