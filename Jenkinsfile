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

    stage('SAST y Dependencias') {
      steps {
        sh '''
          docker run --rm lab-web:${BUILD_NUMBER} sh -c "pip install -q bandit && bandit -r app.py init_db.py" > bandit.txt 2>&1 || true
          docker run --rm lab-web:${BUILD_NUMBER} sh -c "pip install -q pip-audit && pip-audit -r requirements.txt" > pip-audit.txt 2>&1 || true
          cat bandit.txt
          cat pip-audit.txt
        '''
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

    stage('ZAP') {
      steps {
        sh '''
          docker volume rm -f zapwrk || true
          docker volume create zapwrk
          docker run --rm -u 0 --network secnet -v zapwrk:/zap/wrk ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://app:5000 -r zap.html > zap.txt 2>&1 || true
          cat zap.txt
          docker rm -f zapcp || true
          docker create --name zapcp -v zapwrk:/zap/wrk alpine
          docker cp zapcp:/zap/wrk/zap.html .
          docker rm zapcp
        '''
      }
    }
  }

  post {
    always { archiveArtifacts artifacts: '*.txt, zap.html', allowEmptyArchive: true }
  }
}