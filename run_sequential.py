#!/usr/bin/env python
# Copy queued data builder jobs into a run dir, and fork/run the jobs
import logging
from os.path import dirname
cwd = dirname(__file__)
if cwd == '': cwd = '.'

# User configuration - change these settings if needed
logfile = '/var/log/data_builder/runjob.log'
pidfile = '/tmp/databuilder.pid'
filedir = '/var/log/data_builder/queue'
prepdir = '/home/demo/databuilder_jobs'
# Standard configuration - probably does not need changes
runjob = '{0}/run_job.py'.format(cwd)


loglevel=logging.INFO
log = logging.getLogger('PREP')

if __name__ == '__main__':
    def _trusted_main():
        import fcntl
        from datetime import datetime
        import glob
        from os.path import isfile, basename
        from os import getpid, fork, system, remove
        from shutil import copy
        from hashlib import md5
        logging.basicConfig(
            level=loglevel,
            format='%(asctime)s %(levelname)s %(name)15s %(process)d %(message)s',
            filename=logfile)
        log.info('Preparing data builder jobs: {0}'.format(datetime.now()))
        try:
            # Use flock to prevent duplicate runs
            lock_fd = open(pidfile, 'w')
            fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            log.debug('Flock-ing pidfile: {0}'.format(pidfile))
            lock_fd.write('{0}\n'.format(getpid()))
        except IOError:
            log.info('Done, cannot flock pidfile, duplicate process')
            exit()
        try:
            for file in glob.glob(filedir + '/*.json'):
                job = prepdir + '/' + basename(file)
                if isfile(job):
                    log.warn('Skipping file, already exists: {0}'.format(job))
                    continue
                log.info('Copying file {0}'.format(basename(job)))
                log.debug('\n\tsrc: {0}\n\tdest: {1}'.format(file, job))
                copy(file, job)
                fsum = md5(open(file, 'rb').read()).hexdigest()
                jsum = md5(open(job, 'rb').read()).hexdigest()
                if fsum == jsum:
                    remove(file) 
                    log.info('Launching runjob {0}'.format(job))
                    rc = system('python {0} {1}'.format(runjob, job))
                else:
                    log.error('Bad file copy: {0}'.format(basename(job)))
                    remove(job) 
            log.debug('Unlocking pidfile: {0}'.format(pidfile))
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except:
            raise
        log.info('Done')

    _trusted_main()
