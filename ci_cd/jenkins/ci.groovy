// @Library('jenkins-shared-library@v4.0') _

pipeline {
    options {
        skipDefaultCheckout()
        timestamps ()
        withAWS(
            credentials: ("${GIT_BRANCH}" == 'origin/main' ? 'terraform-prod' : 'terraform-dev'),
            region: 'ap-south-1'
        )
    }
    agent any
    environment {
        global = ""
    }
    stages {
        stage("Clean") {
            steps {
                sh echo "--------Clean stage---------------------------------------------" 
                script {
                    //cleanup workspace
                    cleanWs()

                    // Load common parameters
                    global = globalParameter.getContext()

                    // Setting the branch
                    if (env.gitlabBranch) {
                        GIT_BRANCH = setParameter.setBranchCI(env.gitlabBranch)
                    }

                    notification.builtStarted(GIT_BRANCH)

                    // Setting the environment for deployment
                    ENV = setParameter.setEnv(GIT_BRANCH)

                    //set build description
                    branch=GIT_BRANCH.split('/')[1]
                    if (branch in ["feature", "fix", "hotfix"]) {
                        branch=GIT_BRANCH.split('/')[2]
                    }
                    currentBuild.description = "${GIT_BRANCH}\n${env.MIO_NAME}-${branch}-${env.BUILD_NUMBER}"
                }
            }
        }
           stage('init') {
               steps {
                   sh echo "--------Init stage---------------------------------------------" 
      scripts {
        library "jenkins-shared-library@main"
      }
               }
        stage("Git") {
            steps {
                sh echo "--------Git stage---------------------------------------------" 
                script {
                    git.advancedClone(env.GIT_URL, GIT_BRANCH, env.GIT_COMMIT)

                    // Cloning smartmart-infrastructure repository
                    sh "mkdir -p ${global.smartmartFolderName}"
                    dir("${global.smartmartFolderName}") {
                        git.clone(global.gitUrlSmartmart, global.gitBranchSmartmart)
                    }
                }
            }
        }

    }
    post {
        always {
            script {
                dashboard.dashboardCIData(global.jenkinsCredentialIdDb, global.jenkinsCredentialIdJenk, global.jenkinsCredentialIdSonar, "${MIO_NAME}", "${BUILD_NUMBER}", ENV.toLowerCase(), global.dbName, global.dbPort)
                notification.buildFinished(GIT_BRANCH)
                if (currentBuild.result == 'SUCCESS' || currentBuild.result == 'UNSTABLE') {
                    artifactClean.deleteOld(global.bucketName, global.storageFolderName, env.MIO_NAME, GIT_BRANCH)
                    if (env.gitlabBranch =~ "feature/"){
                        println "[INFO] Automatic deployment from feature branch is disable, you can manually start deployment from feature branch to the DEV env."
                        RUN_DEPLOY = "no"
                    }
                    if (RUN_DEPLOY == "yes") {
                        build job: "${env.DEPLOY_JOB_NAME}", propagate: false, wait: false,
                                parameters: [string(name: 'ARTIFACT_ID', value: "${env.MIO_NAME}-${branch}-${env.BUILD_NUMBER}"),
                                             string(name: 'GIT_BRANCH', value: "${GIT_BRANCH}"),
                                             string(name: 'WORKFLOWS', value: "${WORKFLOWS}"),
                                             string(name: 'ENV', value: "${ENV}")
                                ]
                    } else {
                        println "[INFO] Automatic deployment is disabled, if you want to enable, change hidden parameter in Jenkins job"
                    }
                }
            }
        }
    }
}
