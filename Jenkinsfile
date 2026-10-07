pipeline {
  agent any

  stages {
    stage('Syntax') {
      steps {
        sh 'python3 -m compileall -q app.py tests'
      }
    }

    stage('Build test image') {
      steps {
        sh 'docker build --target test -t aceest:test .'
      }
    }

    stage('Test') {
      steps {
        sh 'docker run --rm aceest:test'
      }
    }

    stage('Build runtime image') {
      steps {
        sh 'docker build --target runtime -t aceest:runtime .'
      }
    }
  }
}
