#!/bin/sh
mv /var/lib/grafana/plugins/* ./grafana-8.1.8/data/plugins/
python3 setup/grafana/import_folders.py
python3 setup/grafana/import_dashboards.py
python3 setup/grafana/add_data_source.py
echo "Please restart the docker container to apply the changes!"