// Jenkinsfile - Pipeline CI/CD COD & Media Buyers Metrics API
// Adapte au setup Docker-out-of-Docker (DooD) : Jenkins pilote le Docker
// de l'hote via le socket monte. On utilise --volumes-from jenkins pour
// partager le workspace avec les conteneurs ephemeres.
pipeline {
    agent any

    environment {
        REGISTRY    = 'ghcr.io'
        IMAGE_NAME  = 'ghcr.io/afif-yassine/cod-metrics-api'
        IMAGE_TAG   = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'latest'}"
        SONAR_HOST  = 'http://sonarqube:9000'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log --oneline -5'
                echo "Commit courant : ${env.GIT_COMMIT}"
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    docker run --rm \
                        --volumes-from jenkins \
                        -w "$WORKSPACE" \
                        python:3.11-slim \
                        sh -c "pip install flake8==7.1.1 -q && flake8 src/ tests/ --max-line-length=100"
                '''
            }
        }

        stage('Build & Test') {
            steps {
                sh 'docker build -t cod-metrics-api:${IMAGE_TAG} .'
                sh '''
                    docker rm -f test-runner 2>/dev/null || true
                    set +e
                    docker run \
                        --name test-runner \
                        --volumes-from jenkins \
                        -w "$WORKSPACE" \
                        cod-metrics-api:${IMAGE_TAG} \
                        sh -c "pip install --no-cache-dir -r requirements-dev.txt -q && pytest"
                    TEST_EXIT=$?
                    set -e
                    docker rm -f test-runner 2>/dev/null || true
                    exit $TEST_EXIT
                '''
            }
            post {
                failure { echo 'Tests echoues ou coverage insuffisant.' }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                SONAR_TOKEN = credentials('sonar-token')
            }
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '''
                        docker run --rm \
                            --network cicd-network \
                            --volumes-from jenkins \
                            -w "$WORKSPACE" \
                            -e SONAR_HOST_URL="$SONAR_HOST_URL" \
                            -e SONAR_TOKEN="$SONAR_TOKEN" \
                            sonarsource/sonar-scanner-cli:latest \
                            sonar-scanner \
                              -Dsonar.projectKey=cod-metrics-api \
                              -Dsonar.projectName="COD Metrics API" \
                              -Dsonar.projectBaseDir="$WORKSPACE" \
                              -Dsonar.sources=src \
                              -Dsonar.python.version=3.11 \
                              -Dsonar.python.coverage.reportPaths=coverage.xml \
                              -Dsonar.sourceEncoding=UTF-8
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security Scan') {
            steps {
                // --exit-code 0 : on n'echoue pas sur les CVE, on les liste dans les logs.
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v trivy-cache:/root/.cache/trivy \
                        aquasec/trivy:latest image \
                        --severity HIGH,CRITICAL \
                        --exit-code 0 \
                        --format table \
                        cod-metrics-api:${IMAGE_TAG}
                '''
            }
        }

        stage('Push') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {
                    sh '''
                        echo "$REGISTRY_PASS" | docker login ${REGISTRY} -u "$REGISTRY_USER" --password-stdin
                        docker tag cod-metrics-api:${IMAGE_TAG} ${IMAGE_NAME}:${IMAGE_TAG}
                        docker tag cod-metrics-api:${IMAGE_TAG} ${IMAGE_NAME}:latest
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('IaC Apply') {
            steps {
                dir('infra') {
                    sh '''
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v "$WORKSPACE/infra":/infra -w /infra \
                            hashicorp/terraform:latest init -input=false
                        docker run --rm \
                            -v /var/run/docker.sock:/var/run/docker.sock \
                            -v "$WORKSPACE/infra":/infra -w /infra \
                            hashicorp/terraform:latest apply -auto-approve -input=false
                        docker run --rm \
                            -v "$WORKSPACE/infra":/infra -w /infra \
                            hashicorp/terraform:latest output
                    '''
                }
            }
        }

        stage('Smoke Test') {
            steps {
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
        success {
            echo "Pipeline reussi ! Image : ${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline echoue. Consultez les logs ci-dessus.'
        }
    }
}
