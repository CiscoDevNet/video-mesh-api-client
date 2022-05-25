# Set base image as Ubuntu and install dependencies
FROM ubuntu:20.04
RUN apt update -y
RUN apt upgrade -y
RUN apt install vim tar wget python3-pip libpq-dev python3-dev -y && pip3 install --upgrade pip

# Download Grafana
RUN wget https://dl.grafana.com/oss/release/grafana-8.1.8.linux-amd64.tar.gz
RUN tar -zxvf grafana-8.1.8.linux-amd64.tar.gz

# Copy Grafana setup scripts
COPY ../setup/grafana/ setup/grafana/
COPY ../.env .env

# Setup Grafana depoenencies
RUN pip3 install requests python_dotenv
RUN ./grafana-8.1.8/bin/grafana-cli plugins install grafana-piechart-panel
RUN ./grafana-8.1.8/bin/grafana-cli plugins install aidanmountford-html-panel
RUN ./grafana-8.1.8/bin/grafana-cli plugins install goshposh-metaqueries-datasource
RUN ./grafana-8.1.8/bin/grafana-cli plugins install grafana-worldmap-panel
RUN ./grafana-8.1.8/bin/grafana-cli plugins install marcusolsson-gantt-panel

# Run Grafana Server
CMD ["./grafana-8.1.8/bin/grafana-server", "-homepath", "./grafana-8.1.8/"]