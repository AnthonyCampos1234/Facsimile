# Collaborative Development Workflow Guide

This document outlines how team members collaborate on the Facsimile project using git submodules, GitHub Actions, Docker, and Heroku.



## Team Collaboration Guide

### Getting Started for New Team Members

1. **Clone the repository with submodules**:
   ```bash
   git clone --recurse-submodules https://github.com/AnthonyCampos1234/Facsimile.git
   cd Facsimile
   ```

2. **Set up Docker on your local machine**:
   - Install Docker Desktop (Mac/Windows) or Docker Engine (Linux)
   - Ensure docker-compose is installed

3. **Verify GitHub access**:
   - Make sure you have write access to all three repositories:
     - Main repository (Facsimile)
     - Backend repository (facsimile-backend)
     - Frontend repository (facsimile-frontend)

### Effective Collaboration Practices

1. **Daily communication**:
   - Inform team members which feature/part you'll be working on
   - Use GitHub issues to track tasks and avoid duplicate work

2. **Branch naming conventions**:
   - `feature/feature-name` for new features
   - `bugfix/bug-description` for bug fixes
   - `hotfix/issue-description` for urgent fixes

3. **Code review process**:
   - All code changes require at least one review from a team member
   - Use GitHub's pull request features for discussions
   - The PR author is responsible for resolving merge conflicts

## Repository Structure

```
Facsimile/              # Main repository
├── .github/            # GitHub Actions workflows
├── docker-compose.yml  # Main docker-compose file for local development
├── backend/            # Backend submodule (separate Git repository)
│   ├── Dockerfile      # Backend Docker configuration
│   └── ...             # Backend code
└── frontend/           # Frontend submodule (separate Git repository)
    ├── Dockerfile      # Frontend Docker configuration
    └── ...             # Frontend code
```

## Git Submodule Workflow

### Initial Setup

When first cloning the repository:

```bash
git clone --recurse-submodules https://github.com/yourusername/Facsimile.git
```

If you already cloned the repository without the `--recurse-submodules` flag:

```bash
git submodule init
git submodule update
```

### Working with Submodules

#### Pulling Updates

When another team member has made changes to a submodule:

```bash
# From the main repository folder
git pull                         # Pull changes to the main repo
git submodule update --init      # Update submodules to their recorded state
```

To update all submodules to their latest commits on main/master:

```bash
git submodule update --remote --merge
```

#### Collaborative Development on a Submodule

When multiple team members are working on the same submodule:

1. **Sync with latest changes first**:
   ```bash
   # From the main repository
   git pull
   git submodule update --init
   cd backend  # or cd frontend
   git checkout main
   git pull
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Work on your changes and regularly push them**:
   ```bash
   # Make changes...
   git add .
   git commit -m "Description of changes"
   git push -u origin feature/your-feature-name
   ```

4. **Create a pull request in the submodule's repository**
   - Add your co-founder as a reviewer
   - Include clear descriptions of what changed
   - Reference any relevant GitHub issues

5. **After the PR is approved and merged**:
   ```bash
   # Inside the submodule directory
   git checkout main
   git pull
   
   # Go back to the main repository
   cd ..
   git add backend  # or git add frontend
   git commit -m "Update backend submodule pointer to include [feature]"
   git push
   ```

#### Resolving Submodule Conflicts

If multiple team members update the same submodule:

1. Navigate to the submodule directory: `cd backend`
2. Ensure you're on main branch: `git checkout main`
3. Pull the latest changes: `git pull`
4. Return to main repo: `cd ..`
5. Add and commit the submodule update: `git add backend && git commit -m "Update submodule pointer"`

## Local Development Workflow

### Running the Application Locally with Docker

1. **Start the entire stack**:
   ```bash
   # From the main repository folder
   docker-compose up
   ```
   This starts all services defined in docker-compose.yml, including backend, frontend, and database.

2. **Rebuild containers after code changes**:
   ```bash
   docker-compose up --build
   ```

3. **Run specific components**:
   ```bash
   # Run only the backend
   docker-compose up backend
   
   # Run only the frontend
   docker-compose up frontend
   
   # Run only the database
   docker-compose up postgres
   ```

4. **View logs for a specific service**:
   ```bash
   docker-compose logs -f backend
   ```

### Collaborating on Local Development

1. **Avoid conflicting ports**: If multiple team members are developing locally:
   - Check that ports 3000 (backend), 80 (frontend), and 5432 (postgres) are available
   - If needed, modify docker-compose.yml to use different port mappings

2. **Share database schemas**: After making database changes:
   - Document the changes in a shared document or migration file
   - Notify team members to run migrations or recreate their local database

## Heroku Deployment Workflow

### Setting Up for Heroku Deployment

1. **One-time setup** (team leader should do this and share access):
   - Create two Heroku apps: `facsimile-backend` and `facsimile-frontend`
   - Add team members as collaborators in Heroku dashboard
   - Configure GitHub repository with necessary Heroku secrets

2. **Required GitHub secrets**:
   - `HEROKU_API_KEY`: Heroku API key for CI/CD deployment
   - `HEROKU_EMAIL`: Email associated with the Heroku account

### Collaborative Deployment Process

1. **Staging environment workflow**:
   - Changes merged to `staging` branch automatically deploy to staging
   - Team reviews changes in staging before promoting to production

2. **Production deployment**:
   - Only designated team members initiate production deployments
   - Deployments happen automatically when PRs are merged to `main`

3. **Monitoring deployments**:
   - All team members can monitor deployments in GitHub Actions tab
   - Check Heroku logs for any deployment issues

## Continuous Integration and Deployment (CI/CD)

This project uses GitHub Actions for CI/CD. The workflows are defined in the `.github/workflows` directory:

- `backend-ci.yml`: Runs tests and builds the backend on pull requests
- `frontend-ci.yml`: Runs tests and builds the frontend on pull requests
- `deploy.yml`: Deploys the application when changes are merged to the main branch

## Collaborative Best Practices

1. **Use feature branches**: Never commit directly to `main` or `staging` branches. Always create feature branches and use pull requests.

2. **Daily syncing**: Pull from the main repository and update submodules daily to avoid large merge conflicts.
   ```bash
   # Morning routine for all developers
   git pull
   git submodule update --init
   ```

3. **Communicate about submodule changes**: When you update a submodule reference in the main repo, inform your teammates so they can run `git submodule update`.

4. **Code review culture**: 
   - Request reviews from at least one other team member
   - Provide constructive feedback
   - Respond to review comments promptly

5. **Version your APIs**: When making breaking changes to the backend API, version it to maintain compatibility.
   - Use routes like `/api/v1/...` and `/api/v2/...`
   - Document API changes thoroughly

6. **Local testing first**: 
   - Always test your changes locally with Docker before pushing
   - Run both backend and frontend tests before making pull requests

7. **Database changes**: Coordinate database schema changes carefully among team members.

8. **Shared environment variables**: Maintain a `.env.example` file in each repository showing required environment variables (without real values).

## Onboarding New Team Members

1. **Repository access**:
   - Ensure GitHub access to all repositories (main, backend, frontend)
   - Add to Heroku as collaborators

2. **Local setup**:
   ```bash
   git clone --recurse-submodules https://github.com/AnthonyCampos1234/Facsimile.git
   cd Facsimile
   docker-compose up
   ```

3. **Documentation review**:
   - Review this WORKFLOW.md document in full
   - Review README files in each repository

4. **First contributions**:
   - Start with small, well-defined tasks
   - Request thorough code reviews on initial PRs
   - Pair program for the first few features if possible
