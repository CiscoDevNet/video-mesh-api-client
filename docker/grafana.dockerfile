# Set base image as Ubuntu and install dependencies
FROM ubuntu:22.04
RUN apt update -y
RUN apt upgrade -y
RUN apt install vim tar wget python3-pip libpq-dev python3-dev -y && pip3 install --upgrade pip
RUN pip3 install pyyaml

# Download Grafana
RUN wget https://dl.grafana.com/oss/release/grafana-9.4.3.linux-amd64.tar.gz
RUN tar -zxvf grafana-9.4.3.linux-amd64.tar.gz

# Copy Grafana setup scripts
COPY ../app/utils.py setup/grafana/utils.py
COPY ../app/constants.py setup/grafana/constants.py
COPY ../app/conf/config.yaml config.yaml
COPY ../setup/grafana/ setup/grafana/

# Setup Grafana depoenencies
RUN pip3 install requests python-dotenv
RUN ./grafana-9.4.3/bin/grafana-cli plugins install grafana-piechart-panel
RUN ./grafana-9.4.3/bin/grafana-cli plugins install aidanmountford-html-panel
RUN ./grafana-9.4.3/bin/grafana-cli plugins install goshposh-metaqueries-datasource
RUN ./grafana-9.4.3/bin/grafana-cli plugins install grafana-worldmap-panel
RUN ./grafana-9.4.3/bin/grafana-cli plugins install marcusolsson-gantt-panel

# Run Grafana Server
CMD ["./grafana-9.4.3/bin/grafana-server", "-homepath", "./grafana-9.4.3/"]