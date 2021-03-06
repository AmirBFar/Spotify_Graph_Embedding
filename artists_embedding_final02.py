import spotipy
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import pandas as pd
import seaborn as sns
import os
import json
import time
from spotipy.oauth2 import SpotifyClientCredentials
plt.rcParams['figure.figsize'] = [18, 12]

def bfs(num_artists):
    
    start = time.time()
    id_ = '6M2wZ9GZgrQXHCFfjv46we'
    with open('spotify_api_cred.json') as f:
        creds = json.load(f)
        auth_manager = SpotifyClientCredentials(client_id = creds['client_id'],
                                        client_secret= creds['client_secret'])
        sp = spotipy.Spotify(auth_manager=auth_manager)

    visited_artists = []
    added_artists = [(id_,sp.artist(id_)["name"],sp.artist(id_)["popularity"])]
    artist_dict = {}
    cnt = 1
    queue = [(id_,sp.artist(id_)["name"],sp.artist(id_)["popularity"])]
    G = nx.Graph()
    
    try:
        os.remove("artist_conectivity_dict_{num_artists}artists.json")
        os.remove("artist_dict_{num_artists}artists.json")
    except:
        pass
    
    open(f"artist_conectivity_dict_{num_artists}artists.json", "a+")
    open(f"artist_dict_{num_artists}artists.json", "a+")
        

    while queue and len(visited_artists) < num_artists:
        current_artist = queue.pop()
        data = {current_artist : [(item["id"],item["name"],item["popularity"]) for item in sp.artist_related_artists(current_artist[0])['artists']]}
        with open(f"artist_conectivity_dict_{num_artists}artists.json" , "r+") as f:
            try:
                temp = json.load(f)
            except:
                temp = {}
                
        with open(f"artist_conectivity_dict_{num_artists}artists.json" , "w+") as f:
            temp[str(current_artist)] = data[current_artist]
            json.dump(temp,f)
            
        with open(f"artist_dict_{num_artists}artists.json", "r+") as f:
            try:
                temp = json.load(f)
            except:
                temp = {}
                
        with open(f"artist_dict_{num_artists}artists.json", "w+") as f:
            temp[current_artist[0]] = current_artist[1:]
            for item in data[current_artist]:
                temp[item[0]] = item[1:] 
            json.dump(temp,f)
        
        cnt += len(data[current_artist])
        for x in data[current_artist]:
            if x not in visited_artists:
                visited_artists.append(x)
                queue.append(x)
                
    artist_index_dict = {}
    with open(f"artist_dict_{num_artists}artists.json", "r") as f:
        temp = json.load(f)
        for i,item in enumerate(temp.keys()):
            artist_index_dict[item] = i
            temp[item] = [i] + temp[item]
            
    with open(f"artist_dict_{num_artists}artists.json", "w") as f:
        json.dump(temp,f)

    with open(f"artist_conectivity_dict_{num_artists}artists.json", "r") as f:
        temp = json.load(f)
        for artist in temp.keys():
            try:
                artist_tuple = str_to_tuple(artist)
                for nei in temp[artist]:
                    G.add_edge(artist_index_dict[artist_tuple[0]],artist_index_dict[nei[0]])
            except ValueError:
                pass

    nx.write_adjlist(G, f"artists_{num_artists}artists.adjlist", comments='#', delimiter=' ', encoding='utf-8')
    nx.draw_kamada_kawai(G)
    print(f"Retrieving data from Spotify took {time.time()-start} seconds.")

    


def embedding_and_clustering(n_artists,n_dims):
    
    adj_list = nx.read_adjlist(f"artists_{n_artists}artists.adjlist")
    G = nx.Graph(adj_list)
    with open(f"artist_dict_{n_artists}artists.json", "r") as f:
        temp = json.load(f)
    
    artist_dict = {}
    for key in temp.keys():
        artist_dict[temp[key][0]] = [key]+temp[key][1:]
    try:
        os.remove(f"artists_{n_artists}artists_{n_dims}dims.embedding")
    except:
        pass
    start = time.time()
    os.system(f"deepwalk --input artists_{n_artists}artists.adjlist --output artists_{n_artists}artists_{n_dims}dims.embedding --representation-size 3")
    print(f'Graph embedding took {time.time()-start} seconds.')
    
    df = pd.DataFrame(columns=["label",'dim1','dim2','dim3'])
    with open(f"artists_{n_artists}artists_{n_dims}dims.embedding") as f:
        next(f)
        for line in f:
            temp = line.split(' ')
            name, popularity = artist_dict[int(temp[0])][1], artist_dict[int(temp[0])][2]
            temp_dict = {"label":int(temp[0]),"name":name,"popularity":popularity,"dim1":float(temp[1]),"dim2":float(temp[2]),"dim3":float(temp[3].strip('\n'))}
            df = df.append(temp_dict,ignore_index=True)

    n_clusters = 10
    kmeans = KMeans(n_clusters=n_clusters,random_state=0).fit(df[['dim1','dim2','dim3']].values)
    df['cluster_assignment'] = kmeans.labels_

    color_codes = list(sns.color_palette("Paired"))
    df['node_color'] = df['cluster_assignment'].apply(lambda x: color_codes[x])

  
    color_dict = df[['label','node_color']].set_index('label',drop=True).to_dict()['node_color']
    node_clr = [color_dict[int(x)] for x in G.nodes()]

    #nx.draw_networkx(G,with_labels=False,node_color=node_clr,node_size=100,alpha=.5)

    fig = plt.figure(figsize=(15,15))
    ax = fig.add_subplot(111,projection='3d')
    ax.scatter(df['dim1'],df['dim2'],df['dim3'],s=280,color=df['node_color'])
    plt.show()

    nx.draw_kamada_kawai(G,with_labels=False,node_color=node_clr,node_size=100,alpha=.5)


def str_to_tuple(key):
    temp = key.split(',')
    return (temp[0].strip('(')[1:-1],temp[1][1:-1],int(temp[2].strip(')')))

def get_artist_name_popularity(artists_spotify_id):
    with open('spotify_api_cred.json') as f:
        creds = json.load(f)
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=creds['client_id'],
                                                           client_secret=creds['client_secret']))
    names = [sp.artist(ID)["name"] for ID in artists_spotify_id]
    popularities = [sp.artist(ID)["popularity"] for ID in artists_spotify_id]

    return names, popularities

if __name__ == "__main__":
    num_artists = 1000
    bfs(num_artists)
    
    get_embeddings(num_artists,3)

