pipeline {
    agent any
    options {
        skipDefaultCheckout()
    }
    triggers {
        pollSCM('H/5 * * * *')
    }
    stages {
        stage('Checkout') {
            steps {
                script {
                    def checkoutInfo = checkout scm
                    env.CHECKED_OUT_BRANCH = checkoutInfo.GIT_BRANCH
                    env.SOURCE_REVISION = checkoutInfo.GIT_COMMIT
                }
            }
        }
        stage('Test in Docker') {
            steps {
                dir('ci-reports') {
                    deleteDir()
                }
                sh '''
                    mkdir -p ci-reports
                    docker build --target test --iidfile ci-reports/image-id .

                    cleanup() {
                        if [ -s ci-reports/container-id ]; then
                            docker rm -f "$(cat ci-reports/container-id)" >/dev/null || true
                        fi
                    }
                    trap cleanup EXIT

                    test_status=0
                    docker run --cidfile ci-reports/container-id "$(cat ci-reports/image-id)" sh -ec '
                        mkdir -p /tmp/aceest-reports
                        exec python -m pytest -v --junitxml=/tmp/aceest-reports/pytest.xml \
                            --cov --cov-report=xml:/tmp/aceest-reports/coverage.xml
                    ' || test_status=$?

                    if [ -s ci-reports/container-id ]; then
                        docker cp "$(cat ci-reports/container-id):/tmp/aceest-reports/." ci-reports/ \
                            || [ "$test_status" -ne 0 ]
                    fi
                    if [ "$test_status" -eq 0 ]; then
                        test -s ci-reports/pytest.xml
                        test -s ci-reports/coverage.xml
                    fi
                    exit "$test_status"
                '''
            }
            post {
                always {
                    script {
                        if (fileExists('ci-reports/pytest.xml')) {
                            junit 'ci-reports/pytest.xml'
                        }
                    }
                }
            }
        }
        stage('SonarQube analysis and quality gate') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withEnv(["SONAR_SCANNER_HOME=${scannerHome}"]) {
                        withSonarQubeEnv('SonarQube') {
                            sh '"$SONAR_SCANNER_HOME/bin/sonar-scanner" -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=600'
                        }
                    }
                }
            }
        }
        stage('Publish to Docker Hub') {
            when {
                expression {
                    def branch = env.BRANCH_NAME ?: env.CHECKED_OUT_BRANCH
                    return !env.CHANGE_ID && (branch in ['master', 'origin/master'])
                }
            }
            steps {
                script {
                    def namespace = env.DOCKERHUB_NAMESPACE?.trim()
                    if (!namespace) {
                        error('Set DOCKERHUB_NAMESPACE in Jenkins to the Docker Hub user or organization that owns aceest-fitness.')
                    }
                    def version = "build-${env.BUILD_NUMBER}-${env.SOURCE_REVISION.take(12)}"
                    def image = "docker.io/${namespace}/aceest-fitness:${version}"
                    withEnv(["PUBLISH_IMAGE=${image}"]) {
                        sh '''
                            docker build --target runtime --tag "$PUBLISH_IMAGE" \
                                --label "org.opencontainers.image.revision=$SOURCE_REVISION" .
                        '''
                        withCredentials([usernamePassword(
                            credentialsId: 'dockerhub-credentials',
                            usernameVariable: 'DOCKERHUB_USERNAME',
                            passwordVariable: 'DOCKERHUB_TOKEN'
                        )]) {
                            sh '''
                                set +x
                                DOCKER_CONFIG="$(mktemp -d)"
                                export DOCKER_CONFIG
                                trap 'rm -rf "$DOCKER_CONFIG"' EXIT
                                # Keep credentials in the temporary config instead of the agent's credential helper.
                                printf '%s\n' '{"auths":{"https://index.docker.io/v1/":{}}}' > "$DOCKER_CONFIG/config.json"
                                printf '%s\n' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
                                docker push "$PUBLISH_IMAGE"
                            '''
                        }
                    }
                    writeFile file: 'ci-reports/image.txt', text: "${image}\n"
                    archiveArtifacts artifacts: 'ci-reports/image.txt'
                }
            }
        }
    }
}
