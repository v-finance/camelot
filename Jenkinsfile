pipeline {
    agent any
    stages {
        stage('Testing') {
            steps {
                sh '/usr/local/bin/invoke -l'
                sh '/usr/local/bin/invoke create_test_environment'
                sh '/usr/local/bin/invoke test'
            }
        }
    }
}
