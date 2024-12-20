from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pandas as pd

# if api error change the api key
# api_key = 'AIzaSyBxXSehH2W7DodVvf92yUFX2XWkheab-VU'
api_key = 'AIzaSyDP0rEeaxoDtc4W74qzdOeoazsso0zESFE'

youtube = build('youtube', 'v3', developerKey=api_key)

channel_name = input("Enter channel name you want to crawl: ")

search_response = youtube.search().list(
    q=channel_name,
    part='id',
    type='channel'
).execute()

if 'items' in search_response:
    channel_id = search_response['items'][0]['id']['channelId']
else:
    print('Channel not found.')
    exit()

start_year = input("Enter start year: ")
start_month = input("Enter start month: ")
start_day = input("Enter start day: ")

end_year = input("Enter end year: ")
end_month = input("Enter end month: ")
end_day = input("Enter end day: ")

start_date = datetime(int(start_year), int(start_month), int(start_day))
end_date = datetime(int(end_year), int(end_month), int(end_day))  

published_after = start_date.isoformat() + 'Z'
published_before = (end_date + timedelta(days=1)).isoformat() + 'Z'

videos = []
next_page_token = None

while True:
    playlist_items_response = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=5,
        publishedAfter=published_after,
        publishedBefore=published_before,
        order='date',
        pageToken=next_page_token
    ).execute()

    videos += playlist_items_response['items']
    next_page_token = playlist_items_response.get('nextPageToken')

    if not next_page_token:
        break

crawl_results = []

for video in videos:
    video_title = video['snippet']['title']
    video_id = video['id']['videoId']
    video_published_at = video['snippet']['publishedAt']
    video_published_at = datetime.strptime(video_published_at, "%Y-%m-%dT%H:%M:%SZ")
    formatted_publish_date = video_published_at.strftime("%B %d, %Y")

    video_response = youtube.videos().list(
        part='statistics',
        id=video_id
    ).execute()

    video_views = video_response['items'][0]['statistics']['viewCount']

    video_like = video_response['items'][0]['statistics']['likeCount']
    comment_count = video_response['items'][0]['statistics']['commentCount']

    like_precentage = (int(video_like)/int(video_views))/100
    comment_percentage = (int(comment_count)/int(video_views))/100
    
    crawl_result = {
        'Video Title': video_title,
        'Video Id': video_id,
        'Publish Date': formatted_publish_date,
        'Video Views': video_views,
        'Video Like': video_like,
        'Like Percentage': like_precentage,
        'Comment Count': comment_count,
        'Comment Percentage': comment_percentage
    }
    crawl_results.append(crawl_result)
    
print("Success to save as CSV file")

df = pd.DataFrame(crawl_results)
df.index = df.index + 1
df.to_csv("youtube_crawl_result.csv", index=True)
