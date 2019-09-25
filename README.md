## CodePipeline Lambda Function for Integration with Checkmarx SAST
* Automated project creation / update
* Scan Execution

## Credit 
https://github.com/binqsoft/CxRestPy.git

### Cloudformation Template
https://s3.amazonaws.com/checkmarx-public/cx-sast-lambda.yml 

### Lambda Source
https://s3.amazonaws.com/checkmarx-public/cx-lambda-1.0.zip 


### Create SSM Parameters
```aws ssm put-parameter --name /Checkmarx/checkmarxURL --type String --value "https://cx.xxxxx.com"
aws ssm put-parameter --name /Checkmarx/checkmarxUser --type SecureString --value "xxxxxx"
aws ssm put-parameter --name /Checkmarx/checkmarxPassword --type SecureString --value "xxxxxx"
```


### Create the Stack with Cloudformation 
```aws cloudformation create-stack --stack-name cx-lambda --template-url https://s3.amazonaws.com/checkmarx-public/cx-sast-lambda.yml \
 --capabilities CAPABILITY_IAM \
 --parameters  ParameterKey=CxUrl,ParameterValue="/Checkmarx/checkmarxURL" \
 ParameterKey=CxUser,ParameterValue="/Checkmarx/checkmarxUser" \
 ParameterKey=CxPassword,ParameterValue="/Checkmarx/checkmarxPassword" 
 ```


#### Add a Checkmarx Step to CodePipeline using new cxScan Function
* Ensure the project paramters include a project at minimum: ```{"project" : "lambda"}```

