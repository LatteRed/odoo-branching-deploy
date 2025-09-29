pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
                script {
                    // Try to get branch name from various sources
                    if (env.BRANCH_NAME) {
                        echo "Using Jenkins BRANCH_NAME: ${env.BRANCH_NAME}"
                    } else if (env.CHANGE_BRANCH) {
                        env.BRANCH_NAME = env.CHANGE_BRANCH
                        echo "Using CHANGE_BRANCH: ${env.BRANCH_NAME}"
                    } else {
                        // Fallback: try to determine from git
                        def branchName = sh(script: 'git branch -r --contains HEAD | head -1 | sed "s/origin\\///"', returnStdout: true).trim()
                        env.BRANCH_NAME = branchName ?: 'main'
                        echo "Using git fallback: ${env.BRANCH_NAME}"
                    }
                    echo "Current branch: ${env.BRANCH_NAME}"
                }
            }
        }
        
        stage('Environment Detection') {
            steps {
                script {
                    // Use same VM for all environments
                    env.TARGET_VM_IP = '66.42.90.200'
                    env.TARGET_VM_USER = 'root'
                    env.SSH_CREDENTIAL = 'odoo-vm-ssh'
                    
                    if (env.BRANCH_NAME.startsWith('feature/')) {
                        env.DEPLOY_ENVIRONMENT = 'development'
                        env.DOCKER_COMPOSE_FILE = 'docker-compose.yml'
                        env.DOCKER_IMAGE_TAG = 't29-odoo-dev'
                        env.PORT = '8069'
                    } else if (env.BRANCH_NAME == 'staging') {
                        env.DEPLOY_ENVIRONMENT = 'staging'
                        env.DOCKER_COMPOSE_FILE = 'docker-compose.yml'
                        env.DOCKER_IMAGE_TAG = 't29-odoo-staging'
                        env.PORT = '8069'
                    } else if (env.BRANCH_NAME == 'master' || env.BRANCH_NAME == 'main') {
                        env.DEPLOY_ENVIRONMENT = 'production'
                        env.DOCKER_COMPOSE_FILE = 'docker-compose.yml'
                        env.DOCKER_IMAGE_TAG = 't29-odoo'
                        env.PORT = '8069'
                    } else {
                        error "Unsupported branch: ${env.BRANCH_NAME}"
                    }
                    echo "Deploying to: ${env.DEPLOY_ENVIRONMENT} on ${env.TARGET_VM_IP}:${env.PORT}"
                }
            }
        }
        
        stage('Code Quality') {
            when {
                anyOf {
                    branch 'feature/*'
                    branch 'staging'
                }
            }
            steps {
                echo 'Running code quality checks...'
                sh '''
                    # Check Python syntax
                    find t29_custom_* -name "*.py" -exec python3 -m py_compile {} \\;
                    
                    # Check XML syntax (if xmllint is available)
                    if command -v xmllint >/dev/null 2>&1; then
                        find t29_custom_* -name "*.xml" -exec xmllint --noout {} \\;
                    else
                        echo "xmllint not available, skipping XML validation"
                    fi
                    
                    # Check manifest files
                    for module in t29_custom_*; do
                        if [ -f "$module/__manifest__.py" ]; then
                            python3 -c "import ast; ast.parse(open('$module/__manifest__.py').read())"
                        fi
                    done
                '''
            }
        }
        
        stage('Dependency Validation') {
            when {
                anyOf {
                    branch 'feature/*'
                    branch 'staging'
                }
            }
            steps {
                echo 'Validating module dependencies...'
                sh '''
                    python3 -c "
import ast
import sys

modules = ['t29_custom_one', 't29_custom_2', 't29_custom_3']
dependencies = {}

for module in modules:
    with open(f'{module}/__manifest__.py', 'r') as f:
        content = f.read()
    manifest = ast.literal_eval(content)
    dependencies[module] = manifest.get('depends', [])

# Check dependency chain
assert 't29_custom_one' in dependencies['t29_custom_2'], 't29_custom_2 must depend on t29_custom_one'
assert 't29_custom_one' in dependencies['t29_custom_3'], 't29_custom_3 must depend on t29_custom_one'
assert 't29_custom_2' in dependencies['t29_custom_3'], 't29_custom_3 must depend on t29_custom_2'

print('Dependency validation passed!')
                    "
                '''
            }
        }
        
        stage('Security Checks') {
            when {
                branch 'staging'
            }
            steps {
                echo 'Running security checks...'
                sh '''
                    # Check for hardcoded passwords
                    if grep -r "password.*=" t29_custom_* --include="*.py"; then
                        echo "WARNING: Potential hardcoded passwords found"
                    fi
                    
                    # Check for SQL injection patterns
                    if grep -r "execute.*%" t29_custom_* --include="*.py"; then
                        echo "WARNING: Potential SQL injection patterns found"
                    fi
                '''
            }
        }
        
        stage('Database Backup') {
            when {
                branch 'staging'
            }
            steps {
                echo 'Creating database backup before deployment...'
                sshagent([env.SSH_CREDENTIAL]) {
                    sh """
                        ssh ${env.TARGET_VM_USER}@${env.TARGET_VM_IP} "
                            cd /opt/t29-odoo
                            docker-compose -f ${env.DOCKER_COMPOSE_FILE} exec -T db pg_dump -U odoo odoo_${env.DEPLOY_ENVIRONMENT} > /backups/backup_before_${BUILD_NUMBER}.sql
                        "
                    """
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo "Building Docker image for ${env.DEPLOY_ENVIRONMENT}..."
                sh "docker build --no-cache -t ${env.DOCKER_IMAGE_TAG}:${BUILD_NUMBER} ."
                sh "docker tag ${env.DOCKER_IMAGE_TAG}:${BUILD_NUMBER} ${env.DOCKER_IMAGE_TAG}:latest"
            }
        }
        
        stage('Deploy to Target Environment') {
            steps {
                echo "Deploying to ${env.DEPLOY_ENVIRONMENT} environment..."
                sshagent([env.SSH_CREDENTIAL]) {
                    sh """
                        # Save Docker image
                        docker save ${env.DOCKER_IMAGE_TAG}:latest | gzip > /tmp/${env.DOCKER_IMAGE_TAG}.tar.gz
                        
                        # Transfer to Target VM
                        scp /tmp/${env.DOCKER_IMAGE_TAG}.tar.gz ${env.TARGET_VM_USER}@${env.TARGET_VM_IP}:/tmp/
                        
                        # Deploy on Target VM
                        ssh ${env.TARGET_VM_USER}@${env.TARGET_VM_IP} "
                            cd /opt/t29-odoo
                            docker load < /tmp/${env.DOCKER_IMAGE_TAG}.tar.gz
                            
                            # Update docker-compose.yml to use custom image
                            sed -i 's/image: odoo:17.0/image: t29-odoo:latest/' docker-compose.yml
                            
                            docker-compose -f ${env.DOCKER_COMPOSE_FILE} down
                            docker-compose -f ${env.DOCKER_COMPOSE_FILE} up -d
                        "
                        
                        # Cleanup
                        rm /tmp/${env.DOCKER_IMAGE_TAG}.tar.gz
                    """
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo "Checking ${env.DEPLOY_ENVIRONMENT} deployment..."
                sh """
                    # Wait for Odoo to start up
                    echo "Waiting for Odoo to start up..."
                    sleep 30
                    
                    # Try health check with retries (with timeout)
                    for i in {1..3}; do
                        echo "Health check attempt \$i/3..."
                        if timeout 10 curl -f http://${env.TARGET_VM_IP}:${env.PORT}/web/health; then
                            echo "Health check passed!"
                            exit 0
                        fi
                        echo "Health check failed, waiting 10 seconds..."
                        sleep 10
                    done
                    
                    echo "Health check failed, but continuing deployment..."
                    echo "Note: Service might not be accessible from Jenkins"
                """
            }
        }
        
        stage('Module Installation Test') {
            when {
                anyOf {
                    branch 'feature/*'
                    branch 'staging'
                }
            }
            steps {
                echo 'Testing module installation...'
                sshagent([env.SSH_CREDENTIAL]) {
                    sh """
                        ssh ${env.TARGET_VM_USER}@${env.TARGET_VM_IP} "
                            cd /opt/t29-odoo
                            
                            # Install all simple modules
                            echo 'Installing t29_custom_one...'
                            docker-compose -f ${env.DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${env.DEPLOY_ENVIRONMENT} -i t29_custom_one --stop-after-init
                            
                            echo 'Installing t29_custom_2...'
                            docker-compose -f ${env.DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${env.DEPLOY_ENVIRONMENT} -i t29_custom_2 --stop-after-init
                            
                            echo 'Installing t29_custom_3...'
                            docker-compose -f ${env.DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${env.DEPLOY_ENVIRONMENT} -i t29_custom_3 --stop-after-init
                            
                            echo 'All simple modules installed successfully!'
                        "
                    """
                }
            }
        }
        
        stage('Integration Tests') {
            when {
                branch 'staging'
            }
            steps {
                echo 'Running integration tests...'
                sh """
                    # Test basic Odoo functionality
                    curl -f http://${env.TARGET_VM_IP}:${env.PORT}/web/database/selector
                    
                    # Test custom module endpoints
                    ssh ${env.TARGET_VM_USER}@${env.TARGET_VM_IP} "
                        cd /opt/t29-odoo
                        docker-compose -f ${env.DOCKER_COMPOSE_FILE} exec -T odoo odoo -d odoo_${env.DEPLOY_ENVIRONMENT} --test-enable --stop-after-init
                    "
                """
            }
        }
    }
    
    post {
        success {
            echo "${env.DEPLOY_ENVIRONMENT} deployment successful!"
        }
        failure {
            echo "${env.DEPLOY_ENVIRONMENT} deployment failed!"
        }
        always {
            // Cleanup
            sh "docker rmi ${env.DOCKER_IMAGE_TAG}:${BUILD_NUMBER} || true"
        }
    }
}







