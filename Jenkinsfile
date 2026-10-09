pipeline { 

    agent any 

    stages { 
        stage('Checkout') { 
            steps { 
                echo 'Checking out source code' 
                checkout scm 
            } 
        } 

        stage('Build') { 
            steps { 
                echo 'Installing Python dependencies' 
                sh ''' 
                    python3 -m venv .venv 
                    .venv/bin/pip install -r requirements.txt 
                '''
            }
        } 

        stage('Test') { 
            steps { 
                echo 'Running automated tests' 
                sh ''' 
                    .venv/bin/python -m pytest -q
                ''' 
            } 
        } 
    } 
} 

/* pipeline {
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
} */
