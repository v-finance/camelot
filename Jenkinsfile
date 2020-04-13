pipeline {
    agent any
    stages {
        stage('Testing') {
            steps {
                cleanWs()
                sh '/usr/local/bin/invoke -l'
                sh '/usr/local/bin/invoke create-test-environment'
                sh '/usr/local/bin/invoke test'
            }
        }
    }
}
