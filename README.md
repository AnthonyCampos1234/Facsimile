# Facsimile

A fullstack web application with a proper GitHub and Docker workflow for collaborative development.

## Project Structure

This repository is organized as a monorepo with git submodules:

- `backend/`: Backend application submodule
- `frontend/`: Frontend application submodule

## Development Workflow

See the [WORKFLOW.md](./WORKFLOW.md) document for detailed instructions on the development workflow.

## Getting Started

1. Clone the repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/AnthonyCampos1234/Facsimile.git
   ```

2. Navigate to the project directory:
   ```bash
   cd Facsimile
   ```

3. Start the development environment:
   ```bash
   docker-compose up
   ```

## Collaboration

This project is set up for collaborative development using git submodules, Docker, and Heroku. See the [WORKFLOW.md](./WORKFLOW.md) document for comprehensive collaboration instructions.

### Key Features of Our Workflow

- **Git Submodules**: Backend and frontend are maintained as separate repositories
- **Docker**: Local development uses Docker for consistent environments across team members
- **GitHub Actions**: Automated CI/CD pipelines for testing and deployment
- **Heroku**: Backend and frontend deploy automatically to separate Heroku apps

## License

[MIT](LICENSE)
