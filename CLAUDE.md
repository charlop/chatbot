# CLAUDE.md - Project Instructions

## EPCC Documentation Structure

When running EPCC commands, save all documentation to these locations:

- **EXPLORE Phase**: Save EPCC_EXPLORE.md to `docs/EPCC-Explore/`
- **PLAN Phase**: Save EPCC_PLAN.md to `docs/EPCC-Plan/`
- **CODE Phase**: Save EPCC_CODE.md to `docs/EPCC-Code/`
- **COMMIT Phase**: Save EPCC_COMMIT.md to `docs/EPCC-Commit/`

## Project Context
- Documentation Root: `artifacts/`
- PRD Location: `artifacts/product-docs/`
- Project Type: Greenfield
- Frontend project location: `project/frontend`
- Backend project location: `project/backend`

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

