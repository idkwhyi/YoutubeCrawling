from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pandas as pd
import warnings
import requests
import re
import networkx as nx 
import matplotlib.pyplot as plt
from textblob import TextBlob 
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory 

plt.rcParams["font.family"] = "Arial Unicode MS"
plt.rcParams["font.family"] = "DejaVu Sans"

warnings.filterwarnings("ignore", category=UserWarning, message="Glyph.*missing from current font")

def remove_emojis(text):
    # Pattern to match emojis
    emoji_pattern = re.compile("["
                                "\U0001F600-\U0001F64F"  # Emoticons
                                "\U0001F300-\U0001F5FF"  # Symbols & pictographs
                                "\U0001F680-\U0001F6FF"  # Transport & map symbols
                                "\U0001F700-\U0001F77F"  # Alchemical symbols
                                "\U0001F780-\U0001F7FF"  # Geometric shapes extended
                                "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                                "\U0001F900-\U0001F9FF"  # Supplemental symbols and pictographs
                                "\U0001FA00-\U0001FA6F"  # Chess Symbols
                                "\U0001FA70-\U0001FAFF"  # Symbols and pictographs Extended-A
                                "\U0001F3FB-\U0001F3FF"  # Emoji modifiers
                                "\U000E0020-\U000E007F"  # Tags
                                "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def clean_data(comment):
    if isinstance(comment, str) and comment.strip():
        cleaned_comment = remove_emojis(comment)
        if cleaned_comment.strip():
            return cleaned_comment
    return None

# api_key = 'AIzaSyBxXSehH2W7DodVvf92yUFX2XWkheab-VU'
api_key = 'AIzaSyDP0rEeaxoDtc4W74qzdOeoazsso0zESFE'

graph = nx.Graph()

comment_data = []
cleaned_data = []
connetion_data = [] 

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

print("----------- Input Video Data -----------")
search_video_title = input("Enter video title that you want to find: ")
print("")
print("Input Video Date Information")
start_year = input("Enter start year: ")
start_month = input("Enter start month: ")
start_day = input("Enter start day: ")
print("")
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

for video in videos:
    video_title = video['snippet']['title']
    if search_video_title == video_title:
        video_id = video['id']['videoId']
        video_response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&maxResults=10000"
        comments_response = requests.get(comments_url).json()
        all_comments = []

        graph.add_node(video_title, text=video_title)

        for comment in comments_response['items']:
            comment_id = comment['id']
            comment_text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
            comment_author = comment['snippet']['topLevelComment']['snippet']['authorDisplayName']
            comment_like = comment['snippet']['topLevelComment']['snippet']['likeCount']
            comment_publish_date = comment['snippet']['topLevelComment']['snippet']['publishedAt']
            comment_published_at = datetime.strptime(comment_publish_date, "%Y-%m-%dT%H:%M:%SZ")
            formatted_publish_date = comment_published_at.strftime("%B %d, %Y")

            comment_text_clean = clean_data(comment_text)

            graph.add_node(comment_author, text=comment_text, color="#31e086")
            graph.add_edge(video_title, comment_author)

            comment_data.append({
                'Author': comment_author,
                'Comment': comment_text,
                'Comment ID': comment_id,
                'Parent Comment': "",
                'Like Count': comment_like,
                'Publish Date': formatted_publish_date,
            })

            cleaned_comment = clean_data(comment_text)
            if cleaned_comment:
                cleaned_data.append({
                    'Author': comment_author,
                    'Comment': cleaned_comment,
                    'Comment ID': comment_id,
                    'Parent Comment': "",
                    'Like Count': comment_like,
                    'Publish Date': formatted_publish_date,
                })

            connetion_data.append({
                'Parent': video_title,
                'Child': comment_author
            })
            

            reply_count = comment['snippet']['totalReplyCount']
            if reply_count > 0:
                reply_url = f"https://www.googleapis.com/youtube/v3/comments?part=snippet&parentId={comment['id']}&key={api_key}&maxResults=2000" 
                replies_response = youtube.comments().list(
                    part='snippet',
                    parentId=comment_id,
                    maxResults=20,
                ).execute()


                for reply in replies_response['items']:
                    reply_id = reply['id']
                    reply_text = reply['snippet']['textDisplay']
                    reply_author = reply['snippet']['authorDisplayName']
                    reply_like = reply['snippet']['likeCount']
                    reply_publish_date = reply['snippet']['publishedAt']
                    reply_published_at = datetime.strptime(reply_publish_date, "%Y-%m-%dT%H:%M:%SZ")
                    reply_formatted_publish_date = reply_published_at.strftime("%B %d, %Y")

                    reply_text_clean = clean_data(reply_text)

                    graph.add_node(reply_author, text=reply_text, color="#31cce0")
                    graph.add_edge(comment_author, reply_author)

                    comment_data.append({
                        'Author': reply_author,
                        'Comment': reply_text,
                        'Comment ID': reply_id,
                        'Parent Comment': comment_author,
                        'Like Count': reply_like,
                        'Publish Date': reply_formatted_publish_date,
                    })

                    cleaned_reply = clean_data(reply_text)
                    if cleaned_reply:
                        cleaned_data.append({
                            'Author': reply_author,
                            'Comment': cleaned_reply,
                            'Comment ID': reply_id,
                            'Parent Comment': comment_author,
                            'Like Count': reply_like,
                            'Publish Date': reply_formatted_publish_date,
                        })
                    
                    connetion_data.append({
                        'Parent': comment_author,
                        'Child': reply_author
                    })

print("Done Crawl!")


comment_df = pd.DataFrame(comment_data)
with pd.ExcelWriter('raw_data.xlsx') as writer:
    comment_df.to_excel(writer, sheet_name='Comments', index=False)
print("Done Excel Data")


cleaned_data_df = pd.DataFrame(cleaned_data)
with pd.ExcelWriter('clean_data.xlsx') as writer:
    cleaned_data_df.to_excel(writer, sheet_name='Comments', index=False)
print("Done Data Cleaning")


connection_data_df = pd.DataFrame(connetion_data)
connection_data_df.to_csv('connection_data.csv', index=False)
print("Done Connection Data")


positive_comments = []
negative_comments = []
neutral_comments = []
for data in cleaned_data:
    comment = data["Comment"]

    factory = StopWordRemoverFactory()
    stopword_remover = factory.create_stop_word_remover()
    comment = stopword_remover.remove(comment)

    sentiment_score = TextBlob(comment).sentiment.polarity

    if sentiment_score > 0:
        positive_comments.append(comment)
    elif sentiment_score < 0:
        negative_comments.append(comment)
    else:
        neutral_comments.append(comment)

labels = ['Positive Comments', 'Negative Comments', 'Neutral Comments']
sizes = [len(positive_comments), len(negative_comments), len(neutral_comments)]
colors = ['#42f56f', '#f54242', '#31a3e0']
plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
plt.axis('equal')
plt.title('Sentiment Analysis')
plt.show()


pos = nx.spring_layout(graph, seed=47)
plt.figure(figsize=(12, 8))
node_colors = [graph.nodes[node].get('color', '#e03154') for node in graph.nodes]
nx.draw(graph, pos, with_labels=True, node_size=1000, font_size=9, cmap=plt.cm.Blues, node_color=node_colors, edge_color='gray')
plt.title('YouTube Comments Graph', fontsize=9)
plt.axis('off')
plt.show()
