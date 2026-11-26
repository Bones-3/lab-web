pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Build') {
      steps {
        sh 'docker build -t lab-web:${BUILD_NUMBER} -t lab-web:latest .'
      }
    }

    stage('Tests') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
          sh '''
            rc=0
            docker run --rm lab-web:${BUILD_NUMBER} sh -c "pip install -q pytest && python -m pytest test/" > pytest.txt 2>&1 || rc=$?
            cat pytest.txt
            exit $rc
          '''
        }
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          docker rm -f app || true
          docker run -d --name app --network secnet -p 5000:5000 lab-web:${BUILD_NUMBER}
          sleep 5
          docker run --rm --network secnet curlimages/curl -s -o /dev/null -w "HTTP %{http_code}\\n" http://app:5000/login
        '''
      }
    }
  }

  post {
    always { archiveArtifacts artifacts: '*.txt', allowEmptyArchive: true }
  }
}
