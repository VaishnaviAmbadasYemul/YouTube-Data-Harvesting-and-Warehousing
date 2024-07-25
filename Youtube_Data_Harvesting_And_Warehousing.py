#Import necessary libraries
import streamlit as st
import mysql.connector
import pandas as pd
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import re
from PIL import Image

# Define API version and service name
api_service_name = "youtube"
api_version = "v3"
api_key="API KEY"

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

#Function to fetch the data from MYSQL Database
def fetch_data(query):
    mydb = mysql.connector.connect(host="localhost", user="root", password="user password", database="youtube_data")
    df = pd.read_sql(query, mydb)
    mydb.close()
    return df

#Function to execute the predefined queries
def execute_query(question):
    query_mapping = {
        "What are the names of all the videos and their corresponding channels?":
		         """SELECT Video_title,channel_name 
                 FROM videos 
                 JOIN channels ON channels.channel_id=videos.channel_id;""",
        "Which channels have the most number of videos, and how many videos do they have?": 
		         """SELECT channel_name, COUNT(video_id) AS video_count
				 FROM videos 
                 JOIN Channels ON channels.channel_id=videos.channel_id
                 GROUP BY channel_name
                 ORDER BY video_count DESC;""",
        "What are the top 10 most viewed videos and their respective channels?": 
		         """SELECT video_title,channel_name 
                 FROM videos 
                 JOIN channels ON channels.channel_id =videos.channel_id 
                 ORDER BY video_viewcount DESC 
                 LIMIT 10;""",
        "How many comments were made on each video, and what are their corresponding video names?": 
		         """SELECT video_title, COUNT(*) AS comment_counts
                 FROM videos 
                 JOIN comments on videos.video_id=comments.video_id
                 GROUP BY video_title;""",
        "Which videos have the highest number of likes, and what are their corresponding channel names?": 
		         """SELECT video_title,channel_name
                 FROM videos 
                 JOIN channels ON channels.channel_id=videos.channel_id
                 ORDER BY video_likecount DESC
                 LIMIT 1;""",
        "What is the total number of likes for each video, and what are their corresponding video names?":	          
                """SELECT videos.Video_title, SUM(videos.Video_likecount) AS total_likes
                  FROM videos
                  GROUP BY videos.Video_title;""",
        "What is the total number of views for each channel, and what are their corresponding channel names?": 
		          """SELECT channel_name, SUM(video_viewcount) AS Total_views
                  FROM videos
                  JOIN channels ON channels.channel_id=videos.channel_id
                  GROUP BY channel_name;""",
        "What are the names of all the channels that have published videos in the year 2022?": 
		          """SELECT DISTINCT channels.channel_name
                  FROM channels
                  JOIN videos ON channels.channel_id = videos.channel_id
                  WHERE YEAR(videos.Video_pubdate) = 2022;""",
        "What is the average duration of all videos in each channel, and what are their corresponding channel names?": 
		          """ SELECT channel_name,AVG(video_duration) AS Average_duration
                  FROM videos
                  JOIN channels ON videos.channel_id = channels.channel_id
                  GROUP BY channel_name;""",
        "Which videos have the highest number of comments, and what are their corresponding channel names?": 
		          """ SELECT video_title,channel_name
                  FROM videos
                  JOIN channels ON videos.channel_id = channels.channel_id
                  ORDER BY Video_commentcount DESC
                  LIMIT 1;""" 
    }

    query=query_mapping.get(question)
    if query:
        return fetch_data(query)
    else:
        return pd.DataFrame()
    
#Function to fetch the channel details using API key
def fetch_channel_data(newchannel_id):
    try:
        mydb = mysql.connector.connect(host="localhost", user="root", password="user password", database="youtube_data")
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM channels WHERE channel_id = %s", (newchannel_id,))
        existing_channel = cursor.fetchone()
        
        #Checking the given Channel ID already exist in database and give error message if exists
        if existing_channel:
                cursor.close()
                mydb.close()
                st.error("Channel ID already exists in the database.")
                return pd.DataFrame()
                
        request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=newchannel_id
        )
        response = request.execute()
        if 'items' in response and len(response["items"]) >0:
        #Analysing the response and extracting the required data
            data = {
            "channel_name": response["items"][0]["snippet"]["title"],
            "channel_id": newchannel_id,
            "channel_des": response["items"][0]["snippet"]["description"],
            "channel_playid": response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"],
            "channel_viewcount": response["items"][0]["statistics"]["viewCount"],
            "channel_subcount": response["items"][0]["statistics"]["subscriberCount"]
             }

            #Inserting the fetched data into MSQL database           
            cursor.execute("""INSERT INTO channels (channel_name, channel_id, channel_des, channel_playid, channel_viewcount, channel_subcount)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,(data['channel_name'], data['channel_id'], data['channel_des'], data['channel_playid'],
		    data['channel_viewcount'],data['channel_subcount']))
            mydb.commit()
            cursor.close()
            mydb.close()
            
            return pd.DataFrame(data, index=[0])   
        else:
            cursor.close()
            mydb.close()
            st.error("No items found in the response.")
            return pd.DataFrame()
    
    except HttpError as e:
        st.error(f"HTTP Error: {e}")
        return pd.DataFrame()
    except KeyError as e:
        st.error(f"KeyError: {e}. Please make sure the channel ID is correct.")
        return pd.DataFrame()
    
#Function to fetch the video ID using channel ID
def playlist_videos_id(channel_ids):
    all_video_ids=[]
    for newchannel_id in channel_ids:
        videos_ids=[]
        try:
            response = youtube.channels().list(part="contentDetails",id=newchannel_id).execute()
            if 'items' in response and len(response["items"]) > 0:
                playlist_Id=response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                nextPageToken=None

                while True:
                    response2 = youtube.playlistItems().list(
                       part="snippet",
                       playlistId=playlist_Id,maxResults=50,
                       pageToken=nextPageToken).execute()
                    for i in range(len(response2.get("items",[]))):
                       videos_ids.append(response2["items"][i]["snippet"]["resourceId"]["videoId"])
                    nextPageToken=response2.get("nextPageToken")
                    if nextPageToken is None:
                        break
                else:
                    st.error(f"No channels found for ID: {newchannel_id}")
        except HttpError as e:
            st.error(f"HTTP Error: {e}")
        except KeyError as e:
            st.error(f"KeyError: {e}") 
            
        all_video_ids.extend(videos_ids)        
    return all_video_ids   

#Function to fetch the video datas from the video_IDs
def fetch_video_data(all_video_ids):
    video_info=[]
    for each in all_video_ids:
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=each
            
        )
        response = request.execute()
        for i in response["items"]:
            given= {
                       "Video_Id":i["id"] ,
                       "Video_title":i["snippet"]["title"],
                       "Video_Description":i["snippet"]["description"],
                       "channel_id":i['snippet']['channelId'],
                       "video_Tags": i['snippet'].get("Tags",0),
                       "Video_pubdate":i["snippet"]["publishedAt"],
                       "Video_viewcount":i["statistics"]["viewCount"],
                       "Video_likecount":i["statistics"].get('likeCount',0) ,
                       "Video_favoritecount":i["statistics"]["favoriteCount"],
                       "Video_commentcount":i["statistics"].get("Comment_Count",0),
                       "Video_duration":iso8601_duration_to_seconds(i["contentDetails"]["duration"]),
                       "Video_thumbnails":i["snippet"]["thumbnails"]['default']['url'],
                       "Video_caption":i["contentDetails"]["caption"]
            }
                   
            video_info.append(given)
            
    #Inserting the fetched data into MSQL database          
    mydb = mysql.connector.connect(host="localhost", user="root", password="user password", database="youtube_data")
    cursor = mydb.cursor()
    for all in video_info:
        cursor.execute("""INSERT INTO videos (Video_Id, Video_title, Video_Description,channel_id,video_Tags, Video_pubdate,Video_viewcount, 
            Video_likecount, Video_favoritecount, Video_commentcount, Video_duration,Video_thumbnails, Video_caption)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
            (all['Video_Id'], all['Video_title'], all['Video_Description'], all['channel_id'], all['video_Tags'],
			all['Video_pubdate'],all['Video_viewcount'], all['Video_likecount'], all['Video_favoritecount'], all['Video_commentcount'],
			all['Video_duration'],all['Video_thumbnails'],all["Video_caption"]))
    mydb.commit()
    mydb.close()
    
    return pd.DataFrame(video_info)

#Function to fetch the comments from video IDs
def Fetch_comment_data(newchannel_id):
    commentdata=[]
    allvideo_ids=playlist_videos_id([newchannel_id])
    for video in allvideo_ids:
        
            try:
                request=youtube.commentThreads().list(
                        part="snippet",
                        videoId=video,
                        maxResults=50)
                response=request.execute()
                for all in response["items"]:
                    given={
                                        "comment_id":all["snippet"]["topLevelComment"]["id"],
                                        "Comment_Text":all["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                                        "Comment_Authorname":all["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                        "published_date":all["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                                        "video_id":all["snippet"]["topLevelComment"]["snippet"]["videoId"],
                                        'channel_id': all['snippet']['channelId']}
                                   
                    commentdata.append(given)
                nextpagetoken= response.get('nextPageToken')                                             
            except HttpError as e:
                pass
                
    #Inserting the fetched data into MSQL database   
    mydb = mysql.connector.connect(host="localhost", user="root", password="user password", database="youtube_data")
    cursor = mydb.cursor()
    for comment in commentdata:
        cursor.execute("""INSERT INTO comments (comment_id,Comment_Text, Comment_Authorname,published_date,video_id,channel_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (comment['comment_id'], comment['Comment_Text'], comment['Comment_Authorname'], comment['published_date'],
			  comment['video_id'],comment['channel_id']))
    mydb.commit()
    mydb.close()
    return pd.DataFrame(commentdata)

#function to convert the duration from hours to seconds
def iso8601_duration_to_seconds(duration):
    match = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', duration)
    if not match:
        return None

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    return total_seconds

#Streamlit coding part to showcase the output in streamlit
# SETTING PAGE CONFIGURATIONS


def main():

    icon = Image.open("youtube-logo.png")
    st.set_page_config(page_title= "Youtube Data Harvesting and Warehousing | By Vaishnavi Yemul",
                   page_icon= icon,
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# This app is created by *Vaishnavi Yemul!*"""})

    st.image("Youtube.png",
            width=300)
    st.title(':red[YouTube Data Harvesting and Warehousing using SQL and Streamlit]')              
                       
    st.sidebar.header("Tables")

    Options = st.sidebar.radio("Options", ("Channels", "Videos", "Comments", "Queries", "Enter YouTube Channel ID"))

    if  Options == "Channels":
        st.header(':violet[Channels]')
        channels_df = fetch_data("SELECT * FROM Channels;")
        channels_df.index += 1
        st.dataframe(channels_df)

    elif Options == "Videos":
        st.header(':black[Videos]')
        videos_df = fetch_data("SELECT * FROM Videos;")
        videos_df.index += 1
        st.dataframe(videos_df)

    elif Options == "Comments":
        st.header(':orange[Comments]')
        comments_df = fetch_data("SELECT * FROM Comments;")
        comments_df.index += 1
        st.dataframe(comments_df)

    elif Options == "Queries":
        st.header("Queries")
        query_question = st.selectbox("Select Query", [
            "What are the names of all the videos and their corresponding channels?",
            "Which channels have the most number of videos, and how many videos do they have?",
            "What are the top 10 most viewed videos and their respective channels?",
            "How many comments were made on each video, and what are their corresponding video names?",
            "Which videos have the highest number of likes, and what are their corresponding channel names?",
            "What is the total number of likes for each video, and what are their corresponding video names?",
            "What is the total number of views for each channel, and what are their corresponding channel names?",
            "What are the names of all the channels that have published videos in the year 2022?",
            "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
            "Which videos have the highest number of comments, and what are their corresponding channel names?"])
                                      
        if query_question:
            query_result_df = execute_query(query_question)
            query_result_df.index += 1
            st.dataframe(query_result_df) 
    elif Options == "Enter YouTube Channel ID":
        st.header("Enter YouTube Channel ID")
        channel_id = st.text_input("Channel ID")
        if st.button("Fetch Channel Data"):
            channel_df = fetch_channel_data(channel_id)
            channel_df.index +=1
            st.subheader("Channel Data")
            st.write(channel_df)

        if st.button("Fetch Video Data"):
            all_video_ids = playlist_videos_id([channel_id])
            video_df = fetch_video_data(all_video_ids)
            video_df.index +=1
            st.subheader("Video Data")
            st.write(video_df)

        if st.button("Fetch Comment Data"):
            comment_df = Fetch_comment_data([channel_id])
            comment_df.index +=1
            st.subheader("Comment Data")
            st.write(comment_df)
			

if __name__ == "__main__":
    main()
