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
                dir('flask-v1.0') {
                    sh 'python3 -m compileall -q app.py tests'
                }
            }
        }
        stage('Docker build') {
            steps {
                dir('flask-v1.0') {
                    sh 'docker build --target test -t aceest-v1:test .'
                    sh 'docker build --target runtime -t aceest-v1:runtime .'
                }
            }
        }
        stage('Container tests') {
            steps {
                sh 'docker run --rm aceest-v1:test'
            }
        }
    }
}
