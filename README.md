# YouTube-Data-Harvesting-and-Warehousing
The problem statement is to create a Streamlit application that allows users to access and analyze data from multiple YouTube channels. The application should have the following features:


## Developer Guide 

### 1. Tools Install

* Virtual code.
* Jupyter notebook.
* Python 3.11.0 or higher.
* MySQL.
* Youtube API key.

 ### 2. Requirement Libraries to Install

* pip install google-api-python-client, mysql-connector-python, sqlalchemy, pymysql,streamlit.

  ### 3. Import Libraries

**Youtube API libraries**
* import googleapiclient.discovery
* from googleapiclient.discovery import build
  
**File handling libraries**
* import re

**SQL libraries**
* import mysql.connector
* import sqlalchemy
* from sqlalchemy import create_engine
* import pymysql

**Dashboard libraries**
* import streamlit as st

 ## Approach:
Set up a Streamlit app: Streamlit is a great choice for building data visualization and analysis tools quickly and easily. You can use Streamlit to create a simple UI where users can enter a YouTube channel ID, view the channel details, and select channels to migrate to the data warehouse.
Connect to the YouTube API: You'll need to use the YouTube API to retrieve channel and video data. You can use the Google API client library for Python to make requests to the API.
Store and Clean data : Once you retrieve the data from the YouTube API, store it in a suitable format for temporary storage before migrating to the data warehouse. You can use pandas DataFrames or other in-memory data structures.
Migrate data to a SQL data warehouse: After you've collected data for multiple channels, you can migrate it to a SQL data warehouse. You can use a SQL database such as MySQL or PostgreSQL for this.
Query the SQL data warehouse: You can use SQL queries to join the tables in the SQL data warehouse and retrieve data for specific channels based on user input. You can use a Python SQL library such as SQLAlchemy to interact with the SQL database.
Display data in the Streamlit app: Finally, you can display the retrieved data in the Streamlit app. You can use Streamlit's data visualization features to create charts and graphs to help users analyze the data.
Overall, this approach involves building a simple UI with Streamlit, retrieving data from the YouTube API, storing the data SQL as a warehouse, querying the data warehouse with SQL, and displaying the data in the Streamlit app.

