# GITDM React Client

A modern healthcare management system client built with React, TypeScript, and Tailwind CSS. This application provides a comprehensive interface for managing medical records, AI-powered summaries, patient data, and clinical information.

## 🚀 Features

### Core Functionality

- **AI-Powered Medical Summaries**: Generate and manage AI summaries for medical records
- **Patient Management**: Complete patient record system with detailed profiles
- **Clinical Encounters**: Track and document patient visits with SOAP notes
- **Lab Results**: Manage laboratory test results with LOINC codes
- **Medication Orders**: Track prescriptions and medication schedules
- **Clinical References**: Access and manage medical literature references

### Technical Features

- **Type-Safe API Client**: Auto-generated from OpenAPI specification using Orval
- **Authentication**: JWT-based authentication with automatic token refresh
- **Real-time Data**: React Query for efficient data fetching and caching
- **Error Handling**: Comprehensive error boundaries and toast notifications
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Modern UI**: Clean, accessible components with consistent design

## 🛠️ Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **State Management**: React Query v5
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **API Client**: Axios with Orval code generation
- **Build Tool**: Vite
- **Icons**: Lucide React
- **Date Handling**: date-fns

## 📋 Prerequisites

- Node.js 18.18.0 or higher
- npm or yarn
- Backend API server running (default: `http://localhost:3000`)

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone [repository-url]
cd react-client
```

### 2. Install dependencies

```bash
npm install
```

### 3. Set up environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Update the `.env` file with your backend API URL:

```text
VITE_API_BASE_URL=http://localhost:3000
```

### 4. Generate API client

```bash
npm run api:generate
```

### 5. Start the development server

```bash
npm run dev
```

The application will be available at [http://localhost:5173](http://localhost:5173)

## 📁 Project Structure

```text
src/
├── api/
│   ├── generated/      # Auto-generated API client
│   └── http/          # Axios configuration
├── components/
│   ├── layout/        # Layout components (Header, Sidebar, etc.)
│   └── ui/            # Reusable UI components
├── contexts/          # React contexts (Auth, Theme, etc.)
├── hooks/             # Custom React hooks
├── lib/               # Utility functions
├── pages/             # Route components
│   ├── ai-summaries/
│   ├── encounters/
│   ├── lab-results/
│   ├── medications/
│   ├── patients/
│   └── clinical-references/
├── styles/            # Global styles
├── App.tsx            # Main application component
└── main.tsx           # Application entry point
```

## 📜 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run api:generate` - Generate API client from OpenAPI spec
- `npm run api:watch` - Watch and regenerate API client on changes

## 🏗️ Architecture

### Authentication Flow

- JWT-based authentication with access and refresh tokens
- Automatic token refresh on 401 responses
- Protected routes with authentication checks
- Persistent login state using localStorage

### Data Management

- React Query for server state management
- Optimistic updates for better UX
- Automatic cache invalidation
- Background refetching for fresh data

### UI/UX Design

- Consistent design system with reusable components
- Responsive layout that works on all devices
- Loading states and error handling
- Toast notifications for user feedback
- Accessible components following WCAG guidelines

### Code Generation

- API client automatically generated from OpenAPI spec
- Type-safe API calls with full TypeScript support
- Consistent API across the application

## 🔐 Authentication

The application uses JWT-based authentication:

1. Login with email and password
2. Receive access and refresh tokens
3. Access token is included in all API requests
4. Refresh token is used to obtain new access tokens when they expire

Demo credentials (if available):

- Email: <admin@example.com>
- Password: password

## 🎨 UI Components

The application includes a comprehensive set of reusable UI components:

- **Button**: Various styles and sizes
- **Card**: Container component for content
- **Table**: Data display with sorting and filtering
- **Badge**: Status and category indicators
- **Input/Textarea**: Form controls with validation
- **Select**: Dropdown selection component
- **Toast**: Notification system
- **Loading**: Consistent loading states
- **ErrorMessage**: Error display component
- **ErrorBoundary**: Application-wide error handling

## 🚀 Deployment

### Build for production

```bash
npm run build
```

### Preview production build

```bash
npm run preview
```

## 🔧 Configuration

- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_API_WITH_CREDENTIALS`: Enable credentials for CORS (true/false)
- `VITE_SHOW_DEMO_CREDS`: Show demo credentials in login (development only)

## 🐛 Troubleshooting

### API Connection Issues

1. Ensure the backend server is running
2. Check the `VITE_API_BASE_URL` in your `.env` file
3. Verify CORS settings on the backend

### Build Issues

1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Ensure you're using Node.js 18.18.0 or higher

### Common Issues

- **401 Unauthorized**: Check if your access token is valid or try logging in again
- **Network Error**: Verify the backend server is accessible
- **CORS Error**: Backend needs to allow requests from your frontend URL

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
