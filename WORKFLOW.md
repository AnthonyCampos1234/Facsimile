# Development Workflow Guide

This document outlines the development workflow for the Facsimile project, including how to work with git submodules, GitHub Actions, and Docker.

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

To update all submodules to their latest commits:

```bash
git submodule update --remote --merge
```

#### Making Changes in a Submodule

1. Navigate to the submodule directory:
   ```bash
   cd backend  # or cd frontend
   ```

2. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes, commit them, and push to the submodule repository:
   ```bash
   git add .
   git commit -m "Implement feature X"
   git push origin feature/your-feature-name
   ```

4. Create a pull request in the submodule's GitHub repository.

5. After the pull request is merged, go back to the main repository:
   ```bash
   cd ..
   ```

6. Update the submodule reference in the main repository:
   ```bash
   git add backend  # or git add frontend
   git commit -m "Update backend submodule to include feature X"
   git push
   ```

## Docker Development Workflow

### Local Development

1. Start the entire stack:
   ```bash
   docker-compose up
   ```

2. To rebuild containers after making changes:
   ```bash
   docker-compose up --build
   ```

3. To run only specific services:
   ```bash
   docker-compose up backend  # or docker-compose up frontend
   ```

### Production Deployment

For production, the GitHub Actions workflow will:

1. Build the Docker images
2. Run tests
3. Push the images to a container registry
4. Deploy to your production environment

## Continuous Integration and Deployment (CI/CD)

This project uses GitHub Actions for CI/CD. The workflows are defined in the `.github/workflows` directory:

- `backend-ci.yml`: Runs tests and builds the backend on pull requests
- `frontend-ci.yml`: Runs tests and builds the frontend on pull requests
- `deploy.yml`: Deploys the application when changes are merged to the main branch

## Best Practices

1. **Never commit directly to main**: Always create feature branches and use pull requests.

2. **Keep submodules updated**: Regularly update submodules to prevent integration issues.

3. **Test locally with Docker**: Always test your changes locally with Docker before pushing.

4. **Version your APIs**: When making breaking changes to the backend API, version it to maintain compatibility.

5. **Document your changes**: Keep documentation up-to-date, especially regarding API changes.
