#!/usr/bin/env python
from os.path import dirname
cwd = dirname(__file__)
if cwd == '': cwd = '.'

# User configuration - change these settings if needed
logfile = '/var/log/data_builder/runjob.log'
finish = '/usr/local/datafinisher/df.py'
dbdir = '/home/demo/databuilder_output'
sender = 'informatics@uthscsa.edu'
MAXSIZE=1073741824  # 1 GB (in bytes) max SQLite output size before data builder is killed
recipients = ['bos@uthscsa.edu', 'bokov@uthscsa.edu'] # must also recipient in dfbuilder.py
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
        import os
        import subprocess
        from signal import SIGKILL
        from time import sleep
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
        with open(job, 'r') as jfile:
            info = json.load(jfile)
        dbfile = '{0}/{1}/{2}_{3}.db'.format(dbdir, info['username'], \
            basename(job).replace('.json', ''), info['filename'])
        cmd = 'make -f {0} request1="{1}" run_job >>{2} 2>&1'.format( \
            mkfile, job.replace(':', '\:'), runlog)
        log.info('Data Builder:\n{0}'.format(cmd))
        db_status = None
        subproc = subprocess.Popen(cmd, shell=True)   # use a subprocess we can monitor
        while subproc.poll() is None:
            # check file size every 2 seconds
            sleep(2)
            mon = subprocess.Popen("du -b \"{0}\"".format(dbfile), shell=True, stdout=subprocess.PIPE)
            size = int(mon.communicate()[0].split()[0])
            if size > MAXSIZE:
                # kill the real data builder process not the parent subproc,
                # necessary for file cleanup/removal
                lsof = subprocess.Popen(\
                    "/usr/sbin/lsof | grep \"%s\" | awk '{print $1, $2, $3, $9}'" \
                    % (dbfile), shell=True, stdout=subprocess.PIPE)
                data = lsof.communicate()[0]
                if len(data) > 0 and data.count(" ") == 3:
                    proc_name, proc_id, user, file_name = data.split()
                    #log.info("proc_id={0}, user={1}, file_name={3}".format(proc_id, user, file_name))
                    log.info("Killing PID {0}, filesize {1} > {2}".format(proc_id, size, MAXSIZE))
                    os.kill(int(proc_id), SIGKILL)
                    db_status = -9
                    subproc.wait()
        if db_status is None:
            db_status = subproc.returncode
        log.info("Data builder status code: {0}".format(db_status))
        fstat, cstat = 0, 0
        #csvfile = dbfile.replace('.db', '.csv')
        if db_status != 0 and isfile(dbfile):
            # Data builder failed, see email/logs
            log.info("Clean up, removing {0}".format(dbfile))
            try:
                os.remove(dbfile)
            except Exception, e:
                log.info("Error removing file: {1}".format(str(e)))
        elif len(info['concepts']['keys']) > 0:
            # Run data finisher (use -l option for verbose sql logging)
            cmd = 'python {0} {1} >>{2} 2>&1'.format(finish, dbfile, runlog)
            log.info('Data Finisher:\n{0}'.format(cmd))
            fstat = os.system(cmd.replace(':', '\:'))
            if fstat == 0:
                cmd = 'python {0} -c {1} >>{2} 2>&1'.format(finish, dbfile, runlog)
                log.info('Data Finisher:\n{0}'.format(cmd))
                cstat = os.system(cmd.replace(':','\:'))
        else:
            log.info('Data Finisher: skipped, no concepts in {0}'.format(job))

        if db_status != 0:
            subject = 'Data extraction error: {0}'.format(basename(job))
            log.error('Sending email: {0}'.format(subject))
        elif fstat != 0 or cstat != 0:
            subject = 'Data finisher error: {0}'.format(basename(job))
            log.error('Sending email: {0}'.format(subject))
        logging.shutdown()
        if db_status != 0 or fstat != 0 or cstat !=0:
            sendEmail(subject, runlog)
        os.system('cat {0} >>{1}'.format(runlog, logfile))
        os.remove(runlog)

    _trusted_main()

