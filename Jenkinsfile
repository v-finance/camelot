pipeline {
    agent any
    stages {
        stage('Testing') {
            steps {
                sh '/usr/local/bin/invoke -l'
                sh '/usr/local/bin/invoke create-test-environment'
                sh '/usr/local/bin/invoke test'
            }
        }
    }
}
