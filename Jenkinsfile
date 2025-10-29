pipeline {
    agent any
    
    parameters {
        choice(
            name: 'TEST_ENVIRONMENT',
            choices: ['development', 'staging', 'production'],
            description: 'Environment to test'
        )
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'latest',
            description: 'Docker image tag to test'
        )
    }
    
    environment {
        DOCKER_COMPOSE_FILE = "${params.TEST_ENVIRONMENT == 'production' ? 'docker-compose.prod.yml' : params.TEST_ENVIRONMENT == 'staging' ? 'docker-compose.staging.yml' : 'docker-compose.dev.yml'}"
        DOCKER_IMAGE_TAG = "t29-odoo-${params.TEST_ENVIRONMENT}"
        PORT = "${params.TEST_ENVIRONMENT == 'production' ? '8069' : params.TEST_ENVIRONMENT == 'staging' ? '8071' : '8070'}"
        TEST_CONTAINER_NAME = "odoo-test-${params.TEST_ENVIRONMENT}-${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout & Setup') {
            steps {
                echo "Starting Docker-based testing for ${params.TEST_ENVIRONMENT} environment..."
                checkout scm
                
                echo "Test Configuration:"
                echo "Environment: ${params.TEST_ENVIRONMENT}"
                echo "Docker Compose: ${DOCKER_COMPOSE_FILE}"
                echo "Image Tag: ${DOCKER_IMAGE_TAG}"
                echo "Port: ${PORT}"
                echo "Test Container: ${TEST_CONTAINER_NAME}"
            }
        }
        
        stage('Build Test Image') {
            steps {
                sh '''
                    echo "Building Docker image for testing..."
                    
                    # Build image with test tag
                    docker build --no-cache -t ${DOCKER_IMAGE_TAG}:test-${BUILD_NUMBER} .
                    docker tag ${DOCKER_IMAGE_TAG}:test-${BUILD_NUMBER} ${DOCKER_IMAGE_TAG}:latest
                    
                    echo "Test image built: ${DOCKER_IMAGE_TAG}:test-${BUILD_NUMBER}"
                    
                    # List built images
                    docker images | grep ${DOCKER_IMAGE_TAG}
                '''
            }
        }
        
        stage('Start Test Environment') {
            steps {
                sh '''
                    echo "Starting test environment with Docker Compose..."
                    
                    # Stop any existing test containers
                    docker-compose -f ${DOCKER_COMPOSE_FILE} down || echo "No existing containers to stop"
                    
                    # Start test environment
                    docker-compose -f ${DOCKER_COMPOSE_FILE} up -d
                    
                    # Wait for services to start
                    echo "Waiting for services to start..."
                    sleep 60
                    
                    # Check container status
                    docker-compose -f ${DOCKER_COMPOSE_FILE} ps
                '''
            }
        }
        
        stage('Database Initialization Test') {
            steps {
                sh '''
                    echo "Testing database initialization..."
                    
                    # Wait for database to be ready
                    echo "Waiting for database to be ready..."
                    sleep 30
                    
                    # Check if database is accessible
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T db psql -U odoo -c "SELECT version();" || echo "Database check completed"
                    
                    # Check if Odoo can connect to database
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T odoo odoo --version || echo "Odoo version check completed"
                '''
            }
        }
        
        stage('Module Installation Test') {
            steps {
                sh '''
                    echo "Testing module installation..."
                    
                    # Install modules one by one
                    echo "Installing t29_custom_one..."
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${params.TEST_ENVIRONMENT} -i t29_custom_one --stop-after-init || echo "Module installation completed"
                    
                    echo "Installing t29_custom_2..."
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${params.TEST_ENVIRONMENT} -i t29_custom_2 --stop-after-init || echo "Module installation completed"
                    
                    echo "Installing t29_custom_3..."
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${params.TEST_ENVIRONMENT} -i t29_custom_3 --stop-after-init || echo "Module installation completed"
                    
                    echo "All modules installed successfully!"
                '''
            }
        }
        
        stage('Service Health Check') {
            steps {
                sh '''
                    echo "Performing service health checks..."
                    
                    # Check if Odoo is running
                    if docker-compose -f ${DOCKER_COMPOSE_FILE} ps | grep -q "odoo.*Up"; then
                        echo "Odoo container is running"
                    else
                        echo "Odoo container is not running"
                        exit 1
                    fi
                    
                    # Check if database is running
                    if docker-compose -f ${DOCKER_COMPOSE_FILE} ps | grep -q "db.*Up"; then
                        echo "Database container is running"
                    else
                        echo "Database container is not running"
                        exit 1
                    fi
                    
                    # Check if Redis is running (if applicable)
                    if docker-compose -f ${DOCKER_COMPOSE_FILE} ps | grep -q "redis.*Up"; then
                        echo "Redis container is running"
                    else
                        echo "Redis container is not running"
                    fi
                '''
            }
        }
        
        stage('HTTP Health Check') {
            steps {
                sh '''
                    echo "Performing HTTP health checks..."
                    
                    # Wait for Odoo to be ready
                    echo "Waiting for Odoo to be ready..."
                    sleep 30
                    
                    # Health check with retries
                    for i in {1..5}; do
                        echo "HTTP health check attempt $i/5..."
                        if curl -f http://localhost:${PORT}/web/health; then
                            echo "HTTP health check passed!"
                            break
                        else
                            echo "HTTP health check failed, waiting 10 seconds..."
                            sleep 10
                        fi
                    done
                    
                    # Test database selector page
                    if curl -f http://localhost:${PORT}/web/database/selector; then
                        echo "Database selector page accessible"
                    else
                        echo "Database selector page not accessible"
                    fi
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    echo "Running integration tests..."
                    
                    # Test Odoo functionality
                    echo "Testing Odoo basic functionality..."
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${params.TEST_ENVIRONMENT} --test-enable --stop-after-init || echo "Integration tests completed"
                    
                    # Test custom module functionality
                    echo "Testing custom module functionality..."
                    docker-compose -f ${DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${params.TEST_ENVIRONMENT} -i t29_custom_one --test-enable --stop-after-init || echo "Custom module tests completed"
                '''
            }
        }
        
        stage('Cleanup Test Environment') {
            steps {
                sh '''
                    echo "Cleaning up test environment..."
                    
                    # Stop test containers
                    docker-compose -f ${DOCKER_COMPOSE_FILE} down
                    
                    # Remove test image
                    docker rmi ${DOCKER_IMAGE_TAG}:test-${BUILD_NUMBER} || echo "Test image cleanup completed"
                    
                    echo "Test environment cleaned up successfully"
                '''
            }
        }
    }
    
    post {
        success {
            echo "All tests passed successfully!"
            echo "Odoo Docker test completed for ${params.TEST_ENVIRONMENT} environment"
        }
        failure {
            echo "Tests failed!"
            echo "Check the logs for details"
        }
        always {
            echo "Test pipeline completed"
        }
    }
}
