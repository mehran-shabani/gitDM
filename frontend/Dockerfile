# Frontend Dockerfile for Development
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies (including dev dependencies for development)
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]