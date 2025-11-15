#!/bin/bash
# Production Deployment Script for IACOL Django Project
# This script ensures proper environment configuration and prevents deployment issues

set -e  # Exit on any error

echo "🚀 Starting IACOL Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f ".env.production.example" ]; then
        cp .env.production.example .env
        print_warning "Please edit .env file with your actual production values before continuing!"
        echo ""
        print_error "Deployment stopped. Configure your .env file and run again."
        exit 1
    else
        print_error ".env.production.example not found. Cannot create .env file."
        exit 1
    fi
fi

# Source the environment file
set -a  # automatically export all variables
source .env
set +a

print_status "Loading environment variables..."

# Check required variables
required_vars=("SECRET_KEY" "ALLOWED_HOSTS" "DEBUG")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "Missing required environment variables:"
    printf '   - %s\n' "${missing_vars[@]}"
    print_error "Please set these variables in your .env file before deploying."
    exit 1
fi

print_status "Required environment variables are set ✓"

# Validate critical values
if [ "$DEBUG" = "True" ]; then
    print_warning "WARNING: DEBUG is set to True. This should be False in production!"
fi

if [ "$ALLOWED_HOSTS" = "localhost,127.0.0.1" ]; then
    print_warning "WARNING: ALLOWED_HOSTS contains localhost. Change this for production!"
fi

# Check database connection
print_status "Testing database connection..."
python manage.py migrate --check --no-color
print_status "Database connection successful ✓"

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --no-input --clear --no-color
print_status "Static files collected ✓"

# Run database migrations
print_status "Running database migrations..."
python manage.py migrate --no-color
print_status "Database migrations completed ✓"

# Create superuser if it doesn't exist (optional)
if [ "$CREATE_SUPERUSER" = "True" ]; then
    print_status "Creating superuser..."
    python manage.py createsuperuser --no-input
fi

# Optional: Load initial data
if [ "$LOAD_INITIAL_DATA" = "True" ]; then
    print_status "Loading initial data..."
    python manage.py loaddata initial_data.json
fi

# Test the application
print_status "Running basic application test..."
python manage.py check --deploy --no-color
print_status "Application check completed ✓"

print_status "🎉 Deployment completed successfully!"
print_status "Your application is ready for production."

echo ""
print_status "Next steps:"
echo "1. Ensure your web server (nginx/apache) is configured"
echo "2. Start your application server (gunicorn/uwsgi)"
echo "3. Configure SSL/TLS certificates"
echo "4. Set up monitoring and logging"
echo "5. Configure backup procedures for your database"

# Quick health check
print_status "Performing health check..."
if curl -f -s "http://localhost/health/" > /dev/null; then
    print_status "✅ Health check passed!"
else
    print_warning "⚠️  Health check failed. Please check your application logs."
fi

echo ""
print_status "Deployment script completed!"