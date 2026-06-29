pipeline {
    agent any

    environment {
        // Registre et image Docker publiees sur GitHub Container Registry.
        REGISTRY     = 'ghcr.io'
        IMAGE_NAME   = 'ghcr.io/afif-yassine/cod-metrics-api'
        IMAGE_LOCAL  = 'cod-metrics-api:latest'
        // SonarQube joignable par nom de conteneur sur cicd-network.
        SONAR_HOST   = 'http://sonarqube:9000'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Commit courant : ${env.GIT_SHA}"
                }
            }
        }

        stage('Lint') {
            steps {
                sh 'docker run --rm -v "$PWD":/app -w /app python:3.11-slim sh -c "pip install flake8==7.1.1 && flake8 src/ tests/"'
            }
        }

        stage('Build & Test') {
            steps {
                sh 'docker build -t ${IMAGE_LOCAL} .'
                // Tests + coverage.xml dans un conteneur, monte sur le workspace.
                sh '''
                    docker run --rm -v "$PWD":/app -w /app ${IMAGE_LOCAL} \
                        sh -c "pip install --no-cache-dir -r requirements-dev.txt && pytest"
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '''
                        docker run --rm --network cicd-network \
                            -v "$PWD":/usr/src \
                            sonarsource/sonar-scanner-cli \
                            -Dsonar.projectKey=cod-metrics-api \
                            -Dsonar.sources=src \
                            -Dsonar.host.url=${SONAR_HOST} \
                            -Dsonar.python.coverage.reportPaths=coverage.xml
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security Scan') {
            steps {
                // Trivy scanne l'image; le pipeline n'echoue pas sur les CVE (exit-code 0).
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image --exit-code 0 --severity HIGH,CRITICAL ${IMAGE_LOCAL}
                '''
            }
        }

        stage('Push') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'ghcr-credentials',
                    usernameVariable: 'GHCR_USER',
                    passwordVariable: 'GHCR_TOKEN'
                )]) {
                    sh '''
                        echo "$GHCR_TOKEN" | docker login ${REGISTRY} -u "$GHCR_USER" --password-stdin
                        docker tag ${IMAGE_LOCAL} ${IMAGE_NAME}:${GIT_SHA}
                        docker tag ${IMAGE_LOCAL} ${IMAGE_NAME}:latest
                        docker push ${IMAGE_NAME}:${GIT_SHA}
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('IaC Apply') {
            steps {
                dir('infra') {
                    sh 'terraform init -input=false'
                    sh 'terraform apply -auto-approve -input=false'
                    sh 'terraform output'
                }
            }
        }

        stage('Smoke Test') {
            steps {
                // Attend que le staging reponde puis verifie /health (HTTP 200).
                sh '''
                    sleep 5
                    docker exec cod-metrics-staging \
                        python -c "import urllib.request; assert urllib.request.urlopen('http://localhost:8000/health').status == 200"
                    echo "Smoke test OK : /health repond 200"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker compose down -v || true'
        }
        success {
            echo "Pipeline reussi ! Image : ${IMAGE_NAME}:${GIT_SHA}"
        }
    }
}
