pipeline {
    agent any
    options { timestamps() }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Syntax check') {
            steps {
                dir('aceest-fitness') {
                    sh 'python3 -m compileall -q app.py programs.py tests'
                }
            }
        }
        stage('Docker build') {
            steps {
                dir('aceest-fitness') {
                    sh 'docker build --target test -t aceest-fitness:test .'
                    sh 'docker build --target runtime -t aceest-fitness:runtime .'
                }
            }
        }
        stage('Container tests') {
            steps {
                sh 'docker run --rm aceest-fitness:test'
            }
        }
    }
}

