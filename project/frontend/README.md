# Contract Refund Eligibility System - Frontend

Next.js 14 frontend application for the Contract Refund Eligibility System.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS (Lightspeed design system)
- **PDF Viewer**: react-pdf (PDF.js)
- **State Management**: React Context API + SWR
- **Form Handling**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Authentication**: Auth0 React SDK
- **Testing**:
  - Unit: Vitest + React Testing Library
  - E2E: Playwright

## Getting Started

### Prerequisites

- Node.js 20.x or higher
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local with your actual values
```

### Environment Variables

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_AUTH0_DOMAIN` | Auth0 tenant domain | `your-tenant.auth0.com` |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | Auth0 application client ID | `abc123...` |
| `NEXT_PUBLIC_AUTH0_AUDIENCE` | Auth0 API audience | `https://your-api.com` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_ENVIRONMENT` | Environment name | `development` \| `staging` \| `production` |

See `.env.local.example` for a complete template.

### Development

```bash
# Run development server
npm run dev

# Open http://localhost:3000
```

### Testing

```bash
# Run unit tests
npm test

# Run unit tests in watch mode
npm test -- --watch

# Run unit tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e:ui
```

### Building

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Linting

```bash
# Run ESLint
npm run lint
```

## Project Structure

```
frontend/
├── app/                      # Next.js app router pages
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   └── globals.css          # Global styles
├── components/              # React components
│   ├── ui/                  # Base UI components
│   ├── layout/              # Layout components
│   ├── search/              # Search components
│   ├── pdf/                 # PDF viewer components
│   ├── extraction/          # Data extraction components
│   ├── chat/                # Chat interface components
│   ├── admin/               # Admin panel components
│   └── auth/                # Authentication components
├── contexts/                # React contexts
├── hooks/                   # Custom React hooks
├── lib/                     # Utilities and helpers
│   ├── api/                 # API client and services
│   └── utils/               # Utility functions
├── __tests__/               # Unit tests
├── e2e/                     # E2E tests
├── public/                  # Static assets
├── tailwind.config.ts       # Tailwind configuration
├── vitest.config.ts         # Vitest configuration
└── playwright.config.ts     # Playwright configuration
```

## Development Workflow

This project follows **Test-Driven Development (TDD)**:

1. Write tests first
2. Implement features to make tests pass
3. Refactor while keeping tests green

### Component Development

1. Create test file in `__tests__/components/`
2. Write tests for component behavior
3. Implement component
4. Ensure all tests pass
5. Add to Storybook (if applicable)

### API Integration

1. Define types in `lib/api/types.ts`
2. Create service in `lib/api/`
3. Create SWR hook in `hooks/`
4. Write tests for hook
5. Use in components

## Code Quality Standards

- **SOLID Principles**: All code follows SOLID design principles
- **TypeScript Strict Mode**: Enabled for type safety
- **Test Coverage**: Maintain >90% coverage
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Lighthouse score >90

## Authentication Flow

1. User clicks login → redirected to Auth0
2. Auth0 handles authentication
3. User redirected back with JWT
4. Frontend stores token, uses for API calls
5. Backend validates JWT on each request

See [database auth documentation](../../artifacts/database-auth-update.md) for details.

## Deployment

### Docker

```bash
# Build Docker image
docker build -t contract-refund-frontend .

# Run container
docker run -p 3000:3000 contract-refund-frontend
```

### AWS ECS

1. Build and push image to ECR
2. Update ECS task definition
3. Deploy to ECS service
4. Verify deployment

See [infrastructure documentation](../../artifacts/product-docs/implementation-plan.md) for details.

## Troubleshooting

### Common Issues

**Issue**: `Cannot find module '@/*'`
- **Solution**: Ensure `tsconfig.json` has correct path aliases

**Issue**: Tests failing with "Cannot find module"
- **Solution**: Check `vitest.config.ts` has correct path resolution

**Issue**: Auth0 callback not working
- **Solution**: Verify callback URLs in Auth0 dashboard match your app URLs

**Issue**: API calls failing with CORS
- **Solution**: Check backend CORS configuration allows your frontend origin

## Contributing

1. Create feature branch from `main`
2. Write tests for new features
3. Implement features
4. Ensure all tests pass (`npm test && npm run test:e2e`)
5. Ensure build succeeds (`npm run build`)
6. Submit pull request

## License

Proprietary - Internal use only

## Support

For questions or issues, contact the development team.

---

**Version**: 0.1.0
**Last Updated**: 2025-11-08
