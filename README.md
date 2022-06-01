# Video Mesh API Client

An example of a 3rd party application built using the Webex Video Mesh APIs.

The application is a simple simulation of how the APIs can be used to track organization data and retrieves and displays data such as Cluster Details, Cluster and Node Availability, Cluster Utilization, Call Redirects and Overflows, Media Health Monitoring and Reachability Test Results.

## Prerequisites to setup and run the Application

1. Docker v20.10 or higher
2. Docker Compose v1.29 or higher

## How to setup the application

1. Clone the repository
2. Log in to the [Cisco Webex Developer portal](https://developer.webex.com/)
3. A new OAuth Webex Integration is required to run the application. You can read up more about it on this [Real world walkthrough of building an OAuth Webex integration](https://developer.webex.com/blog/real-world-walkthrough-of-building-an-oauth-webex-integration)
4. Create a [Webex App Integration](https://developer.webex.com/docs/integrations) and set the following:
    - Scopes: 
        - `spark:organizations_read`: To allow access to read your user's organizations
        - `spark-admin:hybrid_connectors_read`: To allow access to read hybrid connectors for your organization
    - Redirect URI: `http://localhost:2808/oauth/`: You can change the route and port number as needed, ensure to propagate these changes in the subsequent steps
5. A `.env` file template has been provided. Add your Webex App Integration Client ID (`INTEGRATION_CLIENT_ID`) and Client Secret (`INTEGRATION_CLIENT_SECRET`)  to this file. Additionally, you can modify the following variables:
    - `GRAFANA_URL`: You can change the port number if you want to run the server on a different port. Remember to reflect this change in `docker-compose.yml`
    - `GRAFANA_API_KEY`: Leave this field empty for now since we need to deploy the server to obtain a key.
    - `REDIRECT_URI`: If your application performs the OAuth flow on a different API route or port number, you can make the required changes here.
    - `DATABASE_`: You can change the database credentials if you want to run the server using a different database. 
6. The TimescaleDB data is persisted to disk in the `/timescale_data` directory on the host machine, which is mapped to a volume on the container to prevent successive builds from losing data. Ensure this directory exists on your machine. Alternatively, if you would like to use a different folder to persist your data, you can change the `/timescale_data` path in `docker-compose.yml`.
7. Navigate to `docker/` and run `docker-compose --project-name video-mesh-api-client up -d` to build and start the application
8. Visit the OAuth Authorization URL obtained while creating the Integration on the Integration app page and authorize the application. You will be redirected to the `localhost:2808/oauth` (or your OAuth URL) for authentication. Once verified, it will show that you have granted access to the application.
    - **Note**: *Once you restart the application container, the authentication flow needs to be completed again*.
9. Visit `http://localhost:3000` (or the port number you deployed the Grafana container on) to see the Grafana application. Log in using `admin` as the username and password.
10. Click on the `Settings` icon on the left sidebar and click on `API Keys`. Click on `New API Key` and create a new key with the `Admin` role. Copy and note down this key.
11. Find the container ID of the Grafana container by running `docker container ls`
12. Open a new shell in the Grafana container using `docker exec -it <CONTAINER_ID> bash`
13. Use `vi .env` to edit the `.env` file and now add the `GRAFANA_API_KEY` variable. Save and exit.
    
    ```sh
    GRAFANA_API_KEY="<your copied Grafana API key>"
    ```
14. Run `./setup/grafana/setup_grafana.sh` to import all the dashboards and data sources. If no errors occur, it means that Grafana has been successfully setup.
15. Restart the Grafana container using `docker restart <CONTAINER_ID>`
16. Once restarted, all the visualizations will be available.

## Scopes and Authentication 

1. To provide the neccessary scopes to the application and grant it access, you need to visit the OAuth Authorization URL on the Integration app page. Once verified, the application will generate an access token and a refresh token, which will be used to access the APIs. 
    - **The access token is valid for 14 days, and is refreshed every 12 days automatically within the application to ensure the application remains running indefinitely**.

2. Each time the application container is restarted, the authentication flow mentioned in step 8 needs to be completed again.

## Restarting the Application

If the host machine is shut down, the application will stop running. To restart the application, run `docker-compose --project-name video-mesh-api-client up -d` in the `docker/` directory. This will restart all the containers and the application will be running. Note that the application will not be able to access the APIs until the authentication flow mentioned in step 8 is completed again.

## Adding more Organizations

Since the access token generated through the OAuth flow provides access to only the organizations the user has access to, the only way to add more organizations is to create another container for the application and authenticate it as a different user which has access to those organizations. To setup the application for different organizations, you need to follow the steps below:

1. Remove all the containers and images created by the application. You can use `docker container ls` to find the container ID of the application containers and `docker image ls` to find the image ID of the application images. You can use `docker container rm <CONTAINER_ID>` to remove the containers and `docker image rm <IMAGE_ID>` to remove the images.
2. The data is persisted to disk in the `/timescale_data` directory on the host machine. You can choose to either retain the Timescale data from the previous organizations or delete it. If you would like to create a new instance of the application without any previous data, run `rm -rf /timescale_data` to delete the data.
3. Setup the application again, including the OAuth Webex Integration with another user account (following from step 2 of how to setup the application).

## Disclaimer

This sample application is meant to demonstrate one of the ways to interact with Webex Video Mesh APIs and render the  data.

When building a production grade monitoring solution, please consider the overall architecture and design from a security , scalability and usability perspective. This is only meant to provide working, starter code where many layers have been simplified and abstracted away to focus on the Webex Video Mesh  use cases.