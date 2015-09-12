#!/usr/bin/env python
from os.path import dirname
cwd = dirname(__file__)
if cwd == '': cwd = '.'

# User configuration - change these settings if needed
logfile = '/var/log/data_builder/runjob.log'
finish = '/usr/local/datafinisher_cat/df.py'
dbdir = '/home/demo/data_builder_output'
sender = 'bos@uthscsa.edu'
recipients = ['bos@uthscsa.edu'] # must also recipient in dfbuilder.py
# Standard configuration - probably does not need changes
mkfile = '{0}/run_job.mk'.format(cwd)

def sendEmail(subject, runlog):
    from email.mime.text import MIMEText
    from smtplib import SMTP
    body = ''
    with open(runlog, 'r') as lf:
        for line in lf:
            body += line
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(recipients)
    smtp = SMTP()
    smtp.connect()
    smtp.sendmail(sender, recipients, msg.as_string())
    smtp.quit()
    

if __name__=='__main__':

    def _trusted_main():
        from sys import argv
        from os import system, remove
        from os.path import basename, isfile
        import json
        import logging

        job = argv[1]
        runlog = '{0}'.format(job.replace('.json', '.out'))

        loglevel=logging.INFO
        log = logging.getLogger('RUNJOB')
        logging.basicConfig(
            level=loglevel,
            format='%(asctime)s %(levelname)s %(name)15s %(message)s', 
            filename=runlog)

        # Run data builder
        cmd = 'make -f {0} request1="{1}" run_job >>{2} 2>&1'.format( \
            mkfile, job.replace(':', '\:'), runlog)
        log.info('Data Builder:\n{0}'.format(cmd))
        status = system(cmd)

        fstat, cstat = 0, 0
        with open(job, 'r') as jfile:
            info = json.load(jfile)
        dbfile = '{0}/{1}/{2}_{3}.db'.format(dbdir, info['username'], \
            basename(job).replace('.json', ''), info['filename'])
        #csvfile = dbfile.replace('.db', '.csv')
        if status != 0 and isfile(dbfile):
            # Data builder failed, see email/logs
            remove(dbfile)
        elif len(info['concepts']['keys']) > 0:
            # Run data finisher (use -l option for verbose sql logging)
            cmd = 'python {0} {1} >>{2} 2>&1'.format(finish, dbfile, runlog)
            log.info('Data Finisher:\n{0}'.format(cmd))
            fstat = system(cmd.replace(':', '\:'))
            if fstat == 0:
                cmd = 'python {0} -c {1} >>{2} 2>&1'.format(finish, dbfile, runlog)
                log.info('Data Finisher:\n{0}'.format(cmd))
                cstat = system(cmd.replace(':','\:'))
        else:
            log.info('Data Finisher: skipped, no concepts in {0}'.format(job))

        if status != 0:
            subject = 'Data extraction error: {0}'.format(basename(job))
            log.error('Sending email: {0}'.format(subject))
        elif fstat != 0 or cstat != 0:
            subject = 'Data finisher error: {0}'.format(basename(job))
            log.error('Sending email: {0}'.format(subject))
        logging.shutdown()
        if status != 0 or fstat != 0 or cstat !=0:
            sendEmail(subject, runlog)
        system('cat {0} >>{1}'.format(runlog, logfile))
        remove(runlog)

    _trusted_main()

