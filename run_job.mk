config=/home/demo/data_builder_cron/data_builder.conf
TOP=/usr/local/heron_extract
PYTHON=python

run_job: 
	cd $(TOP)/cdr2edc; LOGNAME=demo extract_password=demouser \
		$(PYTHON) dfbuilder.py $(config) $(request1)
