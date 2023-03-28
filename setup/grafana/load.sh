#!/bin/sh
mv /var/lib/grafana/plugins/* ./grafana-9.4.3/plugins-bundled/

python3 setup/grafana/import_folders.py
python3 setup/grafana/import_dashboards.py
python3 setup/grafana/add_data_source.py
echo "Please restart the docker container to apply the changes: docker restart grafana"