## CodePipeline Lambda Function for Integration with Checkmarx SAST

* Automated project creation / update
* Scan Execution

## Credit 

https://github.com/binqsoft/CxRestPy.git

### Cloudformation Template

https://s3.amazonaws.com/checkmarx-public/cx-sast-lambda.yml 

Note: Ensure you are in AWS Region : US East (N. Virginia) us-east-1

### Lambda Source

https://s3.amazonaws.com/checkmarx-public/cx-lambda-1.0.zip 


### Create SSM Parameters
AWS UI:

* Go to AWS Systems Manager
* Application Management -> Parameter Store
* Create Parameter:
    * Name: /Checkmarx/checkmarxUser
    * Description: Checkmarx Username
    * Tier: Standard 
    * Type: SecureString
    * KMS KeySource: My Current Account
    * KMS Key ID: alias/aws/ssm
    * Value: first.last@company.com
* Do the same for Checkmarx URL (String) and Password (SecureString)


AWS CLI:
```
aws ssm put-parameter --name /Checkmarx/checkmarxURL --type String --value "https://cx.xxxxx.com"
aws ssm put-parameter --name /Checkmarx/checkmarxUser --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/checkmarxPassword --type SecureString --value "xxxxxx"
```


### Create the Stack with Cloudformation 

AWS UI:

* Go to CloudFormation
* Create Stack -> With new resources (standard) :
    * Prerequisite - Prepare Template : Template is ready
    * Specify template: 
        * Amazon S3 URL
        * https://s3.amazonaws.com/checkmarx-public/cx-sast-lambda.yml
        * Next
    * Stack Name : CxStack
    * Parameters :
        * CxPassword : /Checkmarx/checkmarxPassword - it will link to SSM Stored Parameter
        * CxPreset : Checkmarx Default
        * CxTeam : \CxServer\SP\Checkmarx\Automation - it should exists in Checkmarx Server. For CxSAST version 9.x reverse the slash so that it's /CxServer/SP/Checkmarx/Automation.
        * CxUrl : /Checkmarx/checkmarxURL - it will link to SSM Stored Parameter
        * CxUser : /Checkmarx/checkmarxUser - it will link to SSM Stored Paramete
        * KMSKeyAlias : aws/ssm
        * SSM : true
        * SSMParamPath : Checkmarx
        * Next
    * Next
    * Check the Checkbox : I acknowledge that AWS CloudFormation might create IAM resources.
    * Create Stack
    * Wait until Stack Status is : CREATE_COMPLETE


AWS CLI:
```
aws cloudformation create-stack --stack-name cx-lambda --template-url https://s3.amazonaws.com/checkmarx-public/cx-sast-lambda.yml \
 --capabilities CAPABILITY_IAM \
 --parameters  ParameterKey=CxUrl,ParameterValue="/Checkmarx/checkmarxURL" \
 ParameterKey=CxUser,ParameterValue="/Checkmarx/checkmarxUser" \
 ParameterKey=CxPassword,ParameterValue="/Checkmarx/checkmarxPassword" 
```


#### Add a Checkmarx Step to CodePipeline using new cxScan Function
* Ensure the project parameters include a project at minimum: ```{"project" : "CxLambda"}```
* Ensure the Role used by CodePipeline has Lambda Access in its permissions


AWS UI:

* Go to CodePipeline
* Create Pipeline:
    * Pipeline Settings: 
        * Pipeline Name : CxPipeline
        * Service Role : New Service Role
        * Role Name: AWSCodePipelineServiceRole-us-east-1-CxPipeline
        * Check Checkbox : Allow AWS CodePipeline to create a service role so it can be used with this new pipeline
        * Next
    * Source:
        * Source Provider: Github (for example)
        * Connect to Github
        * Repository : user/reponame
        * Branch : master
        * Change detection options : AWS CodePipeline (for example)
        * Next
    * Build:
        * Skip build stage -> Skip
        * Next
    * Deploy (for example):
        * AWS S3
        * Bucket Name: example_bucket
        * Object Key: example key
        * Next
    * Create pipeline
    * Edit
    * \+ Add Stage :
        * Stage Name : Checkmarx
        * \+ Add action group:
            * Action Name : CxScan
            * Action provider : AWS Lambda
            * Region : US East - (N. Virginia)
            * Input Artifacts : SourceArtifact
            * Function name: cxScan
            * User parameters: ```{"project" : "CxLambda"}```
            * Done
        * Done
    * Save
    * Save
* Go to IAM:
    * Roles:
        * Search for the role you set for CodePipeline: AWSCodePipelineServiceRole-us-east-1-CxPipeline
        * Expand Existing Policy : AWSCodePipelineServiceRole-us-east-1-CxPipeline
        * Click Lambda:
            * Edit Policy:
                * Lambda:
                    * Actions:
                        * Access Level:
                            * Write (InvokeFunction)
                        * Review Policy
                    * Save Changes
* Go to CodePipeline:
    * CxPipeline
        * Release Changes -> Release
        * Checkmarx Scan Succeeded
