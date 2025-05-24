# GitHub Wiki Maintenance Guide

This guide explains how to maintain and update the GitHub Wiki for the QR Code Generator project.

## 🌐 **Wiki Overview**

The GitHub Wiki serves as the **public documentation** for the QR Code Generator project, providing comprehensive guides for users, developers, and administrators.

**Wiki URL**: https://github.com/gsinghjay/mvp_qr_gen/wiki

## 📚 **Wiki Structure**

### Core Pages

| Page | Purpose | Audience | Auto-Updated |
|------|---------|----------|--------------|
| **[Home](https://github.com/gsinghjay/mvp_qr_gen/wiki/Home)** | Main navigation and overview | All users | Manual |
| **[Getting Started](https://github.com/gsinghjay/mvp_qr_gen/wiki/Getting-Started)** | Quick setup guide | New users | Manual |
| **[System Architecture](https://github.com/gsinghjay/mvp_qr_gen/wiki/System-Architecture)** | Technical overview | Developers | Auto (from README) |
| **[Traefik Configuration](https://github.com/gsinghjay/mvp_qr_gen/wiki/Traefik-Configuration)** | Complete Traefik setup | DevOps | Auto (from docs/) |

### Documentation Pages

| Page | Source | Update Method |
|------|--------|---------------|
| **Alert System** | `docs/observatory-first-alerts.md` | Auto-sync |
| **Grafana Dashboards** | `docs/grafana-dashboard-suite.md` | Auto-sync |
| **Observatory Overview** | `GRAFANA.md` | Auto-sync |
| **Traefik Quick Reference** | `docs/traefik-quick-reference.md` | Auto-sync |

## 🔄 **Update Methods**

### 1. Automatic Updates (Recommended)

The wiki is automatically updated via GitHub Actions when documentation changes:

**Triggers**:
- Push to `main`/`master` branch
- Changes to `docs/**`, `README.md`, or `GRAFANA.md`
- Manual workflow dispatch

**What gets updated**:
- All documentation from `docs/` directory
- System architecture from `README.md`
- Observatory overview from `GRAFANA.md`

### 2. Manual Updates

For pages that require manual editing (like Home and Getting Started):

```bash
# Clone the wiki repository
git clone https://github.com/gsinghjay/mvp_qr_gen.wiki.git wiki
cd wiki

# Edit pages
nano Home.md
nano Getting-Started.md

# Commit and push
git add .
git commit -m "Update wiki documentation"
git push origin master
```

### 3. Script-Based Updates

Use the maintenance script for bulk updates:

```bash
# Run the update script
./scripts/update_wiki.sh

# This will:
# - Pull latest wiki changes
# - Sync documentation from docs/
# - Create placeholder pages
# - Commit and push changes
```

## 🛠️ **Maintenance Workflows**

### Regular Maintenance (Weekly)

1. **Review Auto-Updates**: Check that GitHub Actions are running successfully
2. **Update Manual Pages**: Review and update Home, Getting Started as needed
3. **Check Links**: Verify all internal links are working
4. **Review Structure**: Ensure navigation remains logical

### After Major Changes

1. **Update Architecture**: Ensure System Architecture reflects current state
2. **Update Getting Started**: Verify setup instructions are current
3. **Add New Pages**: Create pages for new features or components
4. **Update Navigation**: Modify Home page navigation as needed

### Content Guidelines

#### Writing Style
- **Clear and Concise**: Use simple, direct language
- **Structured**: Use headers, lists, and tables for organization
- **Visual**: Include diagrams, code examples, and screenshots
- **Actionable**: Provide specific steps and commands

#### Code Examples
```bash
# Always include working examples
curl -X POST "https://localhost/api/v1/qr/static" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello World!", "title": "Test"}'
```

#### Cross-References
- Link to related pages: `[Traefik Configuration](Traefik-Configuration)`
- Link to main repo: `[project repository](https://github.com/gsinghjay/mvp_qr_gen)`
- Link to specific files: `[docker-compose.yml](https://github.com/gsinghjay/mvp_qr_gen/blob/main/docker-compose.yml)`

## 🔧 **Technical Setup**

### GitHub Actions Workflow

The wiki is updated by `.github/workflows/update-wiki.yml`:

**Features**:
- Automatic sync from main repository
- Preserves manual edits on certain pages
- Creates commit messages with source information
- Provides workflow summaries

**Permissions**: Uses `GITHUB_TOKEN` with wiki write access

### Local Development

```bash
# Set up local wiki development
git clone https://github.com/gsinghjay/mvp_qr_gen.wiki.git wiki
cd wiki

# Configure git
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Make changes and test locally
# (GitHub wikis use standard Markdown)

# Push changes
git add .
git commit -m "Update documentation"
git push origin master
```

## 📋 **Content Management**

### Page Categories

#### **Quick Start** (New Users)
- Getting Started
- API Documentation  
- Web Interface Guide

#### **Architecture** (Developers)
- System Architecture
- Security Model
- Database Design

#### **Configuration** (DevOps)
- Docker Deployment
- Traefik Configuration
- Environment Configuration

#### **Monitoring** (SRE/DevOps)
- Observatory Overview
- Grafana Dashboards
- Alert System
- Performance Monitoring

#### **Development** (Contributors)
- Development Setup
- Testing Guide
- Contributing Guidelines

#### **Operations** (Administrators)
- Security Best Practices
- Backup & Recovery
- Troubleshooting

### Content Sources

| Content Type | Source Location | Update Method |
|--------------|-----------------|---------------|
| **Architecture Docs** | `docs/` directory | Auto-sync |
| **Setup Guides** | Manual creation | Manual editing |
| **API Reference** | Generated from code | Manual/Auto hybrid |
| **Configuration** | Config files + docs | Auto-sync |
| **Troubleshooting** | Manual creation | Manual editing |

## 🚨 **Troubleshooting**

### Common Issues

#### Wiki Not Updating
1. Check GitHub Actions workflow status
2. Verify file paths in workflow triggers
3. Check repository permissions

#### Broken Links
1. Use relative links for wiki pages: `[Page](Page-Name)`
2. Use full URLs for external links
3. Test links after major restructuring

#### Formatting Issues
1. GitHub wikis use GitHub Flavored Markdown
2. Test complex formatting in GitHub's markdown preview
3. Use HTML for advanced formatting if needed

### Debugging Commands

```bash
# Check workflow status
gh run list --workflow=update-wiki.yml

# View workflow logs
gh run view [run-id] --log

# Test local wiki changes
# (No local preview available, push to test)

# Check wiki repository status
cd wiki
git status
git log --oneline -5
```

## 📊 **Analytics & Monitoring**

### Wiki Usage
- Monitor wiki page views (if GitHub provides analytics)
- Track which pages are most accessed
- Identify gaps in documentation

### Content Quality
- Regular review of outdated information
- User feedback integration
- Link validation

### Maintenance Metrics
- Frequency of updates
- Auto-sync success rate
- Manual edit frequency

## 🎯 **Best Practices**

### Content Strategy
1. **User-Centric**: Organize by user journey, not technical structure
2. **Progressive Disclosure**: Start simple, link to detailed information
3. **Maintenance-Friendly**: Prefer auto-sync over manual updates
4. **Searchable**: Use clear headings and keywords

### Technical Practices
1. **Version Control**: All changes tracked in git
2. **Automation**: Minimize manual maintenance overhead
3. **Consistency**: Use templates and style guides
4. **Testing**: Verify all examples and commands work

### Collaboration
1. **Clear Ownership**: Define who maintains which pages
2. **Review Process**: Review significant changes before publishing
3. **Communication**: Announce major documentation changes
4. **Feedback**: Provide channels for user feedback

---

## 🔗 **Quick Links**

- **Wiki Home**: https://github.com/gsinghjay/mvp_qr_gen/wiki
- **Main Repository**: https://github.com/gsinghjay/mvp_qr_gen
- **Update Script**: `scripts/update_wiki.sh`
- **GitHub Actions**: `.github/workflows/update-wiki.yml`

This wiki serves as the primary public documentation for the QR Code Generator project, providing comprehensive guidance for all user types while maintaining itself through automated processes. 