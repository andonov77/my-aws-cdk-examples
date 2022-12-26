#!/bin/bash

# Set a right conda or anaconda3 path according to the Deep Learning AMIs
export PATH=/home/ec2-user/anaconda3/bin:$PATH
echo 'export PATH=$HOME/anaconda3/bin:$PATH' >> /home/ec2-user/.bash_profile

my_region=$1
echo "region is $my_region"

sudo yum update -y -q
curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install -y -q nodejs
pip install --upgrade --quiet jupyter
# pip install --quiet "jupyterlab>=2.2.9,<3.0.0"
pip install --quiet "jupyterlab>=2.2.9"
pip install --quiet aws-jupyter-proxy

npm_version=`npm --version`
node_version=`node --version`
jupyterlab_version=`jupyter lab --version`
echo "NODE VERISON : $node_version , NPM VERSION : $npm_version and JUPYTERLAB VERSION : $jupyter_version"

echo "*********************Jupyter Version Info*********************"
jupyter --version
echo "**************************************************************"

CERTIFICATE_DIR="/home/ec2-user/certificate"
JUPYTER_CONFIG_DIR="/home/ec2-user/.jupyter"

if [ ! -d "$CERTIFICATE_DIR" ]; then
  mkdir -p $CERTIFICATE_DIR
  openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout "$CERTIFICATE_DIR/mykey.key" -out "$CERTIFICATE_DIR/mycert.pem" -batch
  chown -R ec2-user $CERTIFICATE_DIR
fi
echo "*********************Finished Writing Certificats******************"

mkdir -p $JUPYTER_CONFIG_DIR

echo "*********************Started Writing Config File*********************"

# append notebook server settings
cat <<EOF >> "$JUPYTER_CONFIG_DIR/jupyter_notebook_config.py"
# Set options for certfile, ip, password, and toggle off browser auto-opening
c.NotebookApp.certfile = u'$CERTIFICATE_DIR/mycert.pem'
c.NotebookApp.keyfile = u'$CERTIFICATE_DIR/mykey.key'
from notebook.auth import passwd
password = passwd("amazon_dlami")
c.NotebookApp.password = password

# Set ip to '*' to bind on all interfaces (ips) for the public server
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False

# It is a good idea to set a known, fixed port for server access
c.NotebookApp.port = 8888
EOF

chown -R ec2-user $JUPYTER_CONFIG_DIR
echo "*********************Finished Writing Config File*********************"

pip install --upgrade --quiet boto3
pip install --upgrade --quiet awscli
aws configure set region $my_region
nohup jupyter lab --config=$JUPYTER_CONFIG_DIR/jupyter_notebook_config.py >/home/ec2-user/jupyter.log 2>&1 &
df -h
echo "********************Start running Juypter notebook********************"
