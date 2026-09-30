pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t cloudsecure-ecommerce:latest .'
            }
        }

        stage('Test Application') {
            steps {
                sh 'docker run -d --name cloudsecure-ci-test -p 127.0.0.1:8002:8000 cloudsecure-ecommerce:latest'
                sh 'sleep 5'
                sh 'curl -f http://127.0.0.1:8002/'
            }
        }

        stage('Cleanup Test Container') {
            steps {
                sh 'docker rm -f cloudsecure-ci-test || true'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker rm -f cloudsecure-app || true && docker compose up -d --build'
            }
        }

        stage('Health Check') {
            steps {
                sh 'sleep 5'
                sh 'curl -f http://127.0.0.1:8001/'
            }
        }
    }
}
