# CLAUDE.md - Project Instructions

## EPCC Documentation Structure

When running EPCC commands, save all documentation to these locations:

- **EXPLORE Phase**: Save EPCC_EXPLORE.md to `docs/EPCC-Explore/`
- **PLAN Phase**: Save EPCC_PLAN.md to `docs/EPCC-Plan/`
- **CODE Phase**: Save EPCC_CODE.md to `docs/EPCC-Code/`
- **COMMIT Phase**: Save EPCC_COMMIT.md to `docs/EPCC-Commit/`

## Project Background

We are building a tool to help F&I back-office specialists understand the contractual terms of aftermarket products (cancellation fees, refund details, state-specific logic). The tool connects to a database that already has the contract text loaded in. This tool uses AI to extract the info if needed, and allows users to prompt for additional info.
- PRD Location: `artifacts/product-docs/PRD.md`
- UI/UX design specs: `artifacts/mockups/README.md`
- Frontend project location: `project/frontend`
- Backend project location: `project/backend`
- Frontend, backend, and DB can be started (and optionally seeded) by running `project/start.sh`

## Code Quality Standards
- ALWAYS follow SOLID design principles
- We must use TDD. Build out test cases before adding any new feature
- Single Responsibility: Each class/function has one reason to change
- Open/Closed: Open for extension, closed for modification
- Liskov Substitution: Subtypes must be substitutable for base types
- Interface Segregation: No client forced to depend on unused interfaces
- Dependency Inversion: Depend on abstractions, not concretions
- You must ensure there are automated tests for all code or create tests if they do not exist
- You must compile the code and pass all tests before committing
- Terraform scripts must pass `terraform init` and `terraform plan` before committing
- Deployments must be scripted and automated. NO AWS CLI usage to modify resources ad-hoc.

