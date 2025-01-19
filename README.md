# mea-munera-lambda
Latin for "My Lambda Functions"

Welcome to the `mea-munera-lambda` project! This repository contains a collection of AWS Lambda functions I use on various projects. These functions are designed to perform various tasks efficiently and effectively.

## Features

* Automated versioning and deployment using GitHub Actions.
* Lambda functions packaged and uploaded to an S3 bucket.
* versions.json tracks the latest version of each function.

## How It Works
Changes to a Lambda function directory trigger a workflow.
The directory is zipped, versioned, and uploaded to S3.
versions.json is updated with the new version.


## Contributing
I welcome any contribution or feedback that would improve this project. 
