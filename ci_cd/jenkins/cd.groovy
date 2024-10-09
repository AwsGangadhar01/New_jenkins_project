//@Library('jenkins-shared-library@v4.0') _

pipeline {
    options {
        skipDefaultCheckout()
        timestamps ()
		withAWS(
            credentials: ("${ENV}" == 'PROD' ? 'terraform-prod' : 'terraform-dev'),
            region: 'ap-south-1'
        )
    }
    agent any
    environment {
        //Loads the global properties
        global = ""
        //Loads the local properties
        local  = ""
        MIO_NUMBER = "${env.MIO_NAME.split('_')[0]}"
    }
    stages {
        stage("Clean") {
            steps {
                script {
                    //cleanup workspace
                    cleanWs()

                    // Loads the global properties from shared-library
                    global = globalParameter.getContext()

                    if (env.GIT_BRANCH == "") {
                        GIT_BRANCH = setParameter.setBranchCD(env.ENV)
                    }

                    notification.builtStarted(GIT_BRANCH)
                    echo "Git branch = ${GIT_BRANCH}\nEnv = ${env.ENV}"

                    //set build description
                    currentBuild.description = "${env.ENV}\n${GIT_BRANCH}\n${env.ARTIFACT_ID}"
                }
            }
        }
        stage("Download artifact") {
            steps {
                script {
                    download.downloadArtifact(global.bucketName, global.storageFolderName, env.MIO_NAME, GIT_BRANCH, env.ARTIFACT_ID)
                    download.copyWorkflows(global.bucketName, env.ENV, global.glueFolderName, env.MIO_NAME, env.WORKFLOWS, global.storageFolderName, GIT_BRANCH, env.ARTIFACT_ID, global.workflowFolderName)

                    // Loads the local.properties
                    local = readProperties file: "${global.localPropsPath}"
                }
            }
        }
        stage("Checker") {
            steps {
                script {
                    prepareDir.cfCheck(global.deploymentPath, env.WORKFLOWS, global.cfTemplateShortPath, global.cfParametersShortPath, env.ENV)
                }
            }
        }
        stage("Deploy CF stack") {
            steps {
                script {
                    for (workflow in env.WORKFLOWS.tokenize()) {
                        mio_name_upper         = ((MIO_NAME.toUpperCase()).replaceAll("_", "-"))
                        change_set_name        = "${mio_name_upper}-${env.BUILD_NUMBER}"
                        stack_name             = "${global.cfStackNamePrefix}-${mio_name_upper}-${workflow.toUpperCase().replaceAll("_", "-")}-${env.ENV}"
                        cf_template_full_path  = "${global.deploymentPath}/${workflow}/${global.cfTemplateShortPath}"
                        cf_parameter_full_path = "${global.deploymentPath}/${workflow}/${global.cfParametersShortPath}"
                        parameters_filename    = "${env.ENV}.${global.cfParametersType}"
                        cloudFormation.deployStack(stack_name, global.region, cf_template_full_path, cf_parameter_full_path, parameters_filename, change_set_name)
                    }
                }
            }
        }         

    post {
        always {
            script {
                notification.buildFinished(GIT_BRANCH)
                download.downloadDashboardScript(global.bucketName, global.storageFolderName, env.MIO_NAME, GIT_BRANCH, env.ARTIFACT_ID, global.dashboardScriptName)
                dashboard.dashboardCDData(global.jenkinsCredentialIdDb, global.jenkinsCredentialIdJenk, global.jenkinsCredentialIdSonar, "${MIO_NAME}", "${BUILD_NUMBER}", ENV.toLowerCase(), global.dbName, global.dbPort)
            }
        }
    }
  }
}	
	
