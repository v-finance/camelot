pipeline {
    agent any
    stages {
        stage('Testing') {
            steps {
                sh 'git clean -dfx'
                sh '/usr/local/bin/invoke -l'
                sh '/usr/local/bin/invoke create-test-environment'
                sh '/usr/local/bin/invoke source-check'
                sh '/usr/local/bin/invoke test'
            }
        }
    }
}
