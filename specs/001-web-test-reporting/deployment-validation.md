# Deployment Validation Guide

**Feature**: Web-Based Test Reporting - GitHub Pages Deployment
**Status**: Implementation Complete - Ready for Validation
**Date**: 2026-01-30

## Overview

Phase 4 (User Story 2 - Share Results Publicly) implementation is complete. This guide provides step-by-step instructions for validating the deployment functionality.

## What's Been Implemented

### ✅ Completed Tasks (T063-T073)

1. **GitHub Actions Workflow** (T063-T068):
   - Created `.github/workflows/deploy-reports.yml`
   - Workflow triggers on push to main or manual dispatch
   - Automated pipeline: setup Python → install deps → generate reports → deploy to GitHub Pages
   - Uses `actions/deploy-pages@v4` for modern GitHub Pages deployment

2. **Documentation** (T070-T073):
   - Updated `specs/001-web-test-reporting/quickstart.md`
   - Added three deployment options:
     - Manual deployment to gh-pages branch
     - Deploy from main branch /reports folder
     - Automated deployment with GitHub Actions (recommended)
   - Includes verification and troubleshooting steps

## Validation Tasks (T074-T078)

These tasks require actual GitHub repository setup and evaluation run data.

### Prerequisites

1. **GitHub Repository Setup**:
   ```bash
   # Verify you're in a git repository
   git rev-parse --git-dir

   # Verify GitHub remote is configured
   git remote -v
   ```

2. **Evaluation Run Data**:
   ```bash
   # Verify runs directory has data
   ls runs/

   # Check for results files
   ls runs/*/results.jsonl
   ```

### T074: Generate Production Report

Generate a production-ready report with baseline comparison:

```bash
python scripts/generate_web_report.py \
    --by-model \
    --include-baseline \
    --output reports/index.html \
    --title "AI Medicare Evaluation - Latest Results"
```

**Expected Output**:
```
✓ Report generated successfully
  Output: reports/index.html
  Size: [size in KB]
  Time: [generation time]s
  Runs included: [count]
```

**Verification**:
- [ ] Command executes without errors
- [ ] `reports/index.html` file is created
- [ ] File size is reasonable (< 1MB recommended)
- [ ] Report contains expected data when opened in browser

---

### T075: Manual Deployment to gh-pages

Test manual deployment workflow:

```bash
# Option 1: Traditional gh-pages branch method
git checkout gh-pages 2>/dev/null || git checkout -b gh-pages
cp reports/index.html .
git add index.html
git commit -m "Update report: $(date +%Y-%m-%d)"
git push -u origin gh-pages
git checkout main

# Option 2: Deploy from main branch (modern method)
# 1. Generate reports in reports/ directory
python scripts/generate_web_report.py --output reports/index.html

# 2. Commit to main
git add reports/
git commit -m "Add web reports"
git push origin main

# 3. Configure in GitHub UI:
#    Settings → Pages → Source: Deploy from a branch
#    Branch: main, Folder: /reports
```

**Verification**:
- [ ] Git operations complete without errors
- [ ] Files are pushed to GitHub successfully
- [ ] GitHub Pages setting shows correct configuration

---

### T076: Verify Public URL Access

Access the deployed report via public URL:

```bash
# Replace with your actual GitHub username/repo
# URL format: https://[username].github.io/[repository-name]/
```

**Steps**:
1. Open browser and navigate to your GitHub Pages URL
2. Report should load and display correctly
3. All tables, charts, and styling should be visible

**Verification**:
- [ ] URL resolves successfully (not 404)
- [ ] Page loads completely (check browser console for errors)
- [ ] Tables display with correct data
- [ ] Bar charts render correctly
- [ ] SHIP baseline row appears (if --include-baseline was used)
- [ ] Responsive design works (try different screen sizes)

---

### T077: Test External Access (No Authentication)

Verify report is publicly accessible without GitHub authentication:

**Steps**:
1. Open browser in incognito/private mode
2. Navigate to GitHub Pages URL (https://[username].github.io/[repository])
3. Verify report loads without login prompt

**Verification**:
- [ ] Report loads in incognito mode
- [ ] No authentication/login required
- [ ] All report features work correctly
- [ ] Share URL with external user to confirm accessibility

---

### T078: Test Automated GitHub Actions Workflow

Trigger and verify the automated deployment workflow:

**Method 1: Push to Main (Automatic Trigger)**
```bash
# Make a small change to trigger workflow
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test: trigger deployment workflow"
git push origin main
```

**Method 2: Manual Trigger (workflow_dispatch)**
1. Go to GitHub repository
2. Click "Actions" tab
3. Select "Deploy Web Reports to GitHub Pages" workflow
4. Click "Run workflow" button
5. Select branch: main
6. Click "Run workflow"

**Verification Steps**:
- [ ] Workflow appears in Actions tab
- [ ] All workflow steps complete successfully:
  - [ ] Checkout repository
  - [ ] Set up Python 3.11
  - [ ] Install dependencies
  - [ ] Download Chart.js
  - [ ] Generate web reports
  - [ ] Setup GitHub Pages
  - [ ] Upload artifact
  - [ ] Deploy to GitHub Pages
- [ ] Workflow completes in reasonable time (< 5 minutes)
- [ ] Deployment URL is displayed in workflow output
- [ ] Visit deployment URL and verify report updated

**Troubleshooting**:

If workflow fails, check:
1. **Permissions**: Go to Settings → Pages → Source: GitHub Actions (not "Deploy from a branch")
2. **Workflow permissions**: Settings → Actions → General → Workflow permissions: "Read and write permissions"
3. **Python version**: Ensure Python 3.11 is available in workflow
4. **Dependencies**: Check that all required packages install correctly
5. **Run data**: Ensure `runs/` directory exists (workflow creates fallback if missing)

---

## Validation Checklist

### Phase 4 Complete When:

- [X] T063-T069: GitHub Actions workflow created and documented
- [X] T070-T073: Deployment documentation completed
- [ ] T074: Production report generated successfully
- [ ] T075: Manual deployment tested (at least one method)
- [ ] T076: Public URL accessible and report displays correctly
- [ ] T077: External access verified (no authentication required)
- [ ] T078: Automated workflow tested and working

### Success Criteria:

1. **Report Generation**: Can generate production reports via CLI
2. **Manual Deployment**: Can manually deploy to GitHub Pages
3. **Automated Deployment**: GitHub Actions workflow deploys automatically
4. **Public Access**: Reports are accessible via public URL without authentication
5. **Consistency**: Web reports match CLI output calculations

---

## Next Steps After Validation

Once Phase 4 validation is complete:

### Option 1: Continue with User Story 3 (Recommended)
Add client-side interactivity for filtering and exploring report data:
- Phase 5: User Story 3 - Filter and Explore Results (T079-T101)
- Features: Scenario filters, sortable tables, search functionality

### Option 2: Polish and Production Readiness
Complete polish phase for production deployment:
- Phase 6: Polish & Cross-Cutting Concerns (T102-T124)
- Focus: Documentation, security, performance optimization

### Option 3: Deploy to Production
If satisfied with current functionality:
1. Generate final production reports
2. Enable GitHub Actions workflow
3. Configure custom domain (optional)
4. Announce availability to stakeholders

---

## Deployment URL Format

After successful deployment, reports will be available at:

```
https://[your-github-username].github.io/AI-Medicare-Advice-Evaluator/
```

**Example**:
```
https://jamesoreilly.github.io/AI-Medicare-Advice-Evaluator/
```

---

## Support and Troubleshooting

### Common Issues

1. **404 Error on GitHub Pages URL**:
   - Check Settings → Pages is configured correctly
   - Verify gh-pages branch exists and has content
   - Allow 1-2 minutes for deployment to propagate

2. **Workflow Fails on "Deploy to GitHub Pages"**:
   - Ensure Pages source is set to "GitHub Actions" (not branch)
   - Check workflow permissions in repository settings

3. **Report Displays Incorrectly**:
   - Verify Chart.js was downloaded correctly
   - Check browser console for JavaScript errors
   - Ensure report was generated with valid data

4. **Authentication Required**:
   - Check repository is public (or Pages enabled for private repos)
   - Verify GitHub Pages is enabled in repository settings

### Getting Help

- Review quickstart.md deployment section
- Check GitHub Actions workflow logs
- Verify repository settings match documentation
- Test report locally first: `open reports/index.html`

---

## Summary

**Phase 4 Implementation Status**: ✅ **COMPLETE**

All infrastructure for GitHub Pages deployment has been implemented:
- Automated workflow ready
- Documentation comprehensive
- Three deployment methods supported

**Ready for Validation**: Yes - follow tasks T074-T078 above

**Blocks Phase 5**: No - User Story 3 can begin independently

**Production Ready**: After validation completes successfully
