# Automate data builder / finisher

## Requirements

Deployment of new data builder UI and back end changes.

**TODO**: finish deployment section below...


## Wrapper scripts

These are intended to be run from cron, but can also be kicked-off manually (see usage below).

* run_concurrent.py - Runs all pending db/df jobs concurrently, **Oracle only**
* run_sequential.py - Runs all pending db/df job sequentially, use on **Postgres** i2b2 virtual machines

    ### Configuration
    Set the following fields:  
        logfile - should match run_job.py  
        pidfile - lock file to prevent concurrent wrapper runs  
        filedir - data builder job queue dir (cleared by running these wrapper script)  
        prepdir - working dir where jobs are moved for processing  

    ### Usage  
        $ python run_concurrent.py  
        $ python run_sequential.py  
        As user who will run the scripts; typically this is written to /var/spool/cron/username.  
        $ crontab -e  
          */5 * * * * python /path/to/run_[concurrent|sequential].py  

## Other files

* run_job.py - Runs db/df for a specific job (json)

    ### Configuration

    Set the following fields:  
        logfile - should match run_concurrent/sqeuential.py  
         finish - path to data finisher program  
          dbdir - where output files get created (will contain subdirs for each i2b2 user)  
         sender - notification email address of sender  
     recipients - notification email addresses recipients (comma separated list)  

    **NOTE**: must also set recipeint in dfbuilder.py (**TODO**: moved to data builder config file)

    ### Usage  
        $ python run_job.py /path/to/job_file.json
        

* *run_job.mk* - Make file to run data builder

    ### Configuration  
        config - /path/to/data_builder.conf  
        TOP - /path/to/heron_extract (data builder source code)  

## Output

See logfile

Email from data builder success/fail. Email from finisher fail.

## Deployment 

* Deploy CIRD/data_finisher as usual
* Deploy KUMC/heron_extract as usual
  * Tested with cgi version of data builder
  * **TODO**: Try with Jython/JBoss version
* Deploy CIRD/databuilder (overwrite regular data builder files)
* Back up/archive data builder jobs queue
* Clear data builder jobs queue
* Deploy CIRD/databuilder_automate
* As user who will run the scripts; typically this is written to /var/spool/cron/username.  
  $ crontab -e  
  */5 * * * * python /path/to/run_[concurrent|sequential].py  

