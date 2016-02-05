#This is the daily cronjob which will call the node program "cassandra_image_insert.js".
#This node program in turn calls the python program "article_retriever.py" which also uses "article_type.py"
#to retrieve articles related to interests specified from NYTimes.
#The article information is stored in MySQL on this local machine.
#The article images are stored in Cassandra by passing the extracted images from the temporary download
#folder to python to node. Thus the image insertion into cassandra as a BLOB happens via the node program.
#Finally, once this is done, we clear the temp directory where we had downloaded images for that day's set of articles.
#
#Any changes made here will got to git, but make sure to copy this script to the actual daily cronjob directory:
#/etc/cron.daily/backend_ml_incollab
#
nodejs /home/ubuntu/machine-learning-incollab/cassandra_image_insert.js
rm -rf /home/ubuntu/machine-learning-incollab/Images/nytimes_downloaded_images/*
