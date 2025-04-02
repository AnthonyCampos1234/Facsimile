# Facsimile

A fullstack web application with a proper GitHub and Docker workflow.

## Project Structure

This repository is organized as a monorepo with git submodules:

- `backend/`: Backend application submodule
- `frontend/`: Frontend application submodule

## Development Workflow

See the [WORKFLOW.md](./WORKFLOW.md) document for detailed instructions on the development workflow.

## Getting Started

1. Clone the repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/yourusername/Facsimile.git
   ```

2. Navigate to the project directory:
   ```bash
   cd Facsimile
   ```

3. Start the development environment:
   ```bash
   docker-compose up
   ```

## License

[MIT](LICENSE)
